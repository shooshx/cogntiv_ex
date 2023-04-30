#pragma once
#include <fstream>
#include <chrono>
#include <iomanip>
#include "common_util.h"

class CvsWriter
{
public:
    CvsWriter()
    {
        auto filename = fmt::format("out_{}.csv", std::chrono::duration_cast<std::chrono::seconds>(std::chrono::system_clock::now().time_since_epoch()).count());
        log().info("Opening output {}", filename);
        m_of = std::ofstream(filename.c_str());
        m_of << std::setprecision(std::numeric_limits<double>::digits10 + 1);
    }

    template<typename... T>
    void add(T... v)
    {
        ((m_of << v << ","), ...);
    }

    template<typename T>
    void addv(const T& vv)
    {
        for (const auto v : vv)
            m_of << v << ",";
        // line is going to have a trailing comma, for implementation simplicity
    }
    void done_line()
    {
        // flush output to the file. In case the process is killed we don't want to los
        m_of << std::endl;
    }

private:
    std::ofstream m_of;
};
