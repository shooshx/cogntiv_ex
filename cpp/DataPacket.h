#pragma once

#include <vector>
#include <array>

// Helper for the binary protocol
// see also class DataPacketBin in common.py
class DataPacket
{
public:
    static constexpr std::size_t HEADER_LENGTH = sizeof(uint64_t);

    size_t decode_header()
    {
        // assumes both are the same endianes
        auto sz = static_cast<size_t>(*reinterpret_cast<uint64_t*>(m_header.data()));
        m_data.resize(sz);
        return sz;
    }

public:
    std::array<char, HEADER_LENGTH> m_header;
    std::vector<std::byte> m_data;
};

