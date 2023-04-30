#pragma once
#include <stdexcept>
#include <string_view>
#include <iostream>
// using fmt format instead of std format since gcc-11 doesn't yet have it
#define FMT_HEADER_ONLY
#include <fmt/format.h>

#define REQUIRE(cond, msg) do { if (!(cond)) throw std::runtime_error(msg); } while(false)
#define REQUIRE_FMT(cond, format_str, ...) REQUIRE(cond, fmt::format(format_str, __VA_ARGS__))


class Logger
{
public:
    template<typename... Args >
    void info(const std::string_view format_str, Args&&... args)
    {
        std::cout << fmt::vformat(format_str, fmt::make_format_args(args...)) << "\n";
    }
    template<typename... Args >
    void error(const std::string_view format_str, Args&&... args)
    {
        std::cerr << "Error: " << fmt::vformat(format_str, fmt::make_format_args(args...)) << std::endl;
    }
};

Logger& log()
{
    static Logger s_log;
    return s_log;
}

