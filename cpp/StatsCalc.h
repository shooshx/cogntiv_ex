#pragma once
#include <utility>
#include <cmath>

// calculate mean and standard deviation using streaming method
// see https://nestedsoftware.com/2018/03/27/calculating-standard-deviation-on-streaming-data-253l.23919.html
class StatsCalc
{
public:
    void update(double v)
    {
        m_count += 1.0;
        double mean_diff = (v - m_mean) / m_count;
        double new_mean = m_mean + mean_diff;
        double dsq_inc = (v - new_mean) * (v - m_mean);
        double new_dsq = m_dsq + dsq_inc;
        m_mean = new_mean;
        m_dsq = new_dsq;
    }

    // returns mean, standard-deviation
    std::pair<double, double> get_stats() const
    {
        double variance = (m_count > 0) ? (m_dsq / m_count) : 0.0;
        return { m_mean, std::sqrt(variance) };
    }

private:
    double m_count = 0.0;
    double m_mean = 0.0;
    double m_dsq = 0.0;
};
