#include <cstdlib>
#include <deque>
#include <iostream>
#include <chrono>
#include <span>
#include <fstream>
#include <boost/asio.hpp>

#include "common_util.h"
#include "RateTracker.h"
#include "StatsCalc.h"
#include "DataPacket.h"
#include "CsvWriter.h"

using boost::asio::ip::tcp;

// accumulate input data vectors and calculate statistics on them
class DataAnalytics
{
public:
    // give a hint about the expected size of the data
    void size_hint(size_t vec_len, size_t count_vec)
    {
        m_data.reserve(vec_len * count_vec);
        m_means.reserve(vec_len);
        m_stds.reserve(vec_len);
        // m_vec_len not set since this is only a hint
    }

    size_t add(const std::vector<std::byte>& raw_data)
    {
        REQUIRE_FMT(raw_data.size() % sizeof(double) == 0, "wrong size data, should be a whole multiple of double, got{}", raw_data.size());
        auto count_values = raw_data.size() / sizeof(double);
        // once we started adding vectors, all of them should be the same size
        if (m_vec_len != 0)
            REQUIRE_FMT(count_values == m_vec_len, "Unexpected number of values got:{}, expected:{}", count_values, m_vec_len);
        else
            m_vec_len = count_values;

        // append received data
        auto prev_size = m_data.size();
        m_data.resize(prev_size + count_values);
        auto copy_start = &m_data[prev_size];
        // assumes client and server has the same endiannes 
        std::memcpy(copy_start, raw_data.data(), raw_data.size());
        ++m_count_vec;
        return m_count_vec;
    }

    void reset()
    {
        m_data.clear();
        m_vec_len = 0;
        m_count_vec = 0;
    }

    // This function is not reentrant since it's using the member scratch-pads to avoid memory allocation and returning references to them
    // returns means and standard deviation over the time dimension (sizes == vector length)
    std::pair<const std::vector<double>&, const std::vector<double>&> stats()
    {
        m_means.clear();
        m_stds.clear();
        for (size_t vi = 0; vi < m_vec_len; ++vi)
        {
            StatsCalc calc;
            // maintaining the offset as we itertate avoids multiplications
            size_t offset = vi;
            for (size_t time_i = 0; time_i < m_count_vec; ++time_i)
            {
                auto v = m_data.at(offset);
                offset += m_vec_len;
                calc.update(v);
            }
            auto [mean, std] = calc.get_stats();
            m_means.push_back(mean);
            m_stds.push_back(std);
        }
        return { m_means, m_stds };
    }
    

private:
    // contigous data for the entire matrix. major axis - vectors, minor axis - time
    // invariant: size of m_data = m_vec_len * m_count_vec
    std::vector<double> m_data;
    size_t m_vec_len = 0;
    size_t m_count_vec = 0;

    // scratch-pad for stats return so that it's not reallocated every time
    std::vector<double> m_means;
    std::vector<double> m_stds;
};



// handle data incoming from the network layer and perform all the needed processing
class DataHandler
{
private:
    static constexpr const size_t EXPECTED_VEC_SIZE = 50;
    static constexpr const size_t VECTORS_BATCH_SIZE = 100;

public:
    DataHandler()
    {
        m_data_accumulator.size_hint(EXPECTED_VEC_SIZE, VECTORS_BATCH_SIZE);
        m_input_rate.size_hint(VECTORS_BATCH_SIZE);
    }

    void handle_data(const std::vector<std::byte>& raw_data)
    {
        m_input_rate.got_packet();
        auto count_vec = m_data_accumulator.add(raw_data);
        if (count_vec == VECTORS_BATCH_SIZE)
        {
            auto [rate_mean, rate_std] = m_input_rate.get_stats();
            log().info("data rate of last {}: {:.2f} Hz  std:{:.2f} Hz", count_vec, rate_mean, rate_std);

            m_output.addv(m_input_rate.samples());
            m_output.add(rate_mean, rate_std);

            const auto& [data_means, data_stds] = m_data_accumulator.stats();
            m_output.addv(data_means);
            m_output.addv(data_stds);
            m_output.done_line();

            m_input_rate.reset();
            m_data_accumulator.reset();
        }
    }

private:
    DataAnalytics m_data_accumulator;
    RateTracker m_input_rate;
    CvsWriter m_output;
};


// client network interface, implement the binary protocol
class VectorsClient
{
public:
    VectorsClient(boost::asio::io_context& io_context, const tcp::resolver::results_type& endpoints, DataHandler& data_handler)
        : m_io_context(io_context),
          m_socket(io_context),
          m_data_handler(data_handler)
    {
        do_connect(endpoints);
    }

    void close()
    {
        // post needed in case this is called from a different thread than the one that called io_context.run()
        boost::asio::post(m_io_context, 
            [this]() 
            { 
                m_socket.cancel();
                // in windows cancel is sometimes ignored
                m_socket.close();
            });
    }

private:
    void do_connect(const tcp::resolver::results_type& endpoints)
    {
        boost::asio::async_connect(m_socket, endpoints,
            [this](boost::system::error_code ec, tcp::endpoint)
            {
                if (ec)
                {
                    log().error("connect failed: {}", ec.message());
                    return;
                }
                    
                do_read_header();
            });
    }

    void do_read_header()
    {
        boost::asio::async_read(m_socket, boost::asio::buffer(m_read_msg.m_header, m_read_msg.m_header.size()),
            [this](boost::system::error_code ec, std::size_t /*length*/)
            {
                if (ec)
                {
                    m_socket.close();
                    log().error("read header failed: {}", ec.message());
                    return;
                }
                m_read_msg.decode_header();
                do_read_body();

            });
    }

    void do_read_body()
    {
        boost::asio::async_read(m_socket, boost::asio::buffer(m_read_msg.m_data.data(), m_read_msg.m_data.size()),
            [this](boost::system::error_code ec, std::size_t /*length*/)
            {
                if (ec)
                {
                    m_socket.close();
                    log().error("read data failed: {}", ec.message());
                    return;
                }

                m_data_handler.handle_data(m_read_msg.m_data);
                do_read_header();
            });
    }

private:
    boost::asio::io_context& m_io_context;
    tcp::socket m_socket;
    DataPacket m_read_msg;

    DataHandler& m_data_handler;
};



class CmdOptions
{
public:
    static constexpr const char* DEFAULT_ADDRESS = "127.0.0.1";
    static constexpr const char* DEFAULT_PORT = "8888";


    CmdOptions(int argc, char* argv[])
    {
        if (argc >= 1)
            host = argv[0];
        else
            host = DEFAULT_ADDRESS;
        
        if (argc >= 2)
            port = argv[1];
        else
            port = DEFAULT_PORT;
    }

public:
    std::string host;
    std::string port;
};

using SignalCallback = std::function<void(int)>;
// need to use a singleton that holds the callback since the os signal() does not provide any means to get back to the caller
SignalCallback& signal_callback()
{
    static SignalCallback s_callback;
    return s_callback;
}

void set_signal_handler(const std::function<void(int)>& callback)
{
    signal_callback() = callback;
    // lambda with no capture can be converted to function pointer
    signal(SIGINT, [](int signal_number) {
        signal_callback()(signal_number);
    });
}


int main(int argc, char* argv[])
{
    try
    {
        CmdOptions options(argc - 1, argv + 1); // skip the first value

        boost::asio::io_context io_context;

        tcp::resolver resolver(io_context);
        auto endpoints = resolver.resolve(options.host, options.port);

        DataHandler data_handler;
        VectorsClient client(io_context, endpoints, data_handler);

        // this is not strictly necessary since the OS would close the socket and output file of the process when it's killed
        set_signal_handler([&client](int signal_number) {
            log().info("got signal {}", signal_number);
            client.close();
        });
 
        io_context.run(); 
 
        client.close();
        log().info("done.");

    }
    catch (std::exception& e)
    {
        log().error("Exception: {}", e.what());
    }

    return 0;
}