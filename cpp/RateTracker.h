#pragma once
#include <chrono>
#include <deque>

#include "StatsCalc.h"

// measure the rate of calls
class RateTrackerBase
{
public:
    void got_packet()
    {
        const auto now = std::chrono::high_resolution_clock::now();
        if (m_last_time == std::chrono::high_resolution_clock::time_point())
        {
            m_last_time = now;
            add(0);
        }
        auto diff = std::chrono::duration<double>(now - m_last_time).count();
        m_last_time = now;
        if (diff != 0)
            add(1.0 / diff);
    }

private:
    virtual void add(double freq) = 0;

private:
    std::chrono::high_resolution_clock::time_point m_last_time;
};

// keep track of the rate of calls using a simple sample queue
class RateTrackerSimple : public RateTrackerBase
{
public:
    void size_hint(size_t count_samples)
    {
        m_freq_samples.reserve(count_samples);
    }

    void add(double freq) override
    {
        m_freq_samples.push_back(freq);
    }

    void reset()
    {
        m_freq_samples.clear();
    }

    std::pair<double, double> get_stats() const
    {
        StatsCalc calc;
        for (auto v : m_freq_samples)
            calc.update(v);
        return calc.get_stats();
    }

    const std::vector<double>& samples() const
    {
        return m_freq_samples;
    }

private:
    std::vector<double> m_freq_samples;
};

using RateTracker = RateTrackerSimple;
