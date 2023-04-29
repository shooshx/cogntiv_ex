#pragma once
#include <stdexcept>
#include <string_view>
#include <iostream>
#include <format>

#define REQUIRE(cond, msg) do { if (!(cond)) throw std::runtime_error(msg); } while(false)

class Logger
{
public:
    template<typename... Args >
    void info(const std::string_view fmt, Args&&... args)
    {
        std::cout << std::vformat(fmt, std::make_format_args(args...)) << "\n";
    }
    template<typename... Args >
    void error(const std::string_view fmt, Args&&... args)
    {
        std::cerr << "Error: " << std::vformat(fmt, std::make_format_args(args...)) << std::endl;
    }
};

Logger& log()
{
    static Logger s_log;
    return s_log;
}

