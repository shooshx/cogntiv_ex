import struct
import pickle
import asyncio


class DataPacketPickle:
    """
    serialize and deserialize data in a packet for sending on a stream
    """
    HEADER_FORMAT = "<Q"
    HEADER_LEN = struct.calcsize(HEADER_FORMAT)

    def __init__(self, data=None):
        self.data = data

    # stream protocol is |--size--|----data---|--size--|----data----|...
    # where size is 8 bytes, data is the size specified just before
    # using pickle for data serialization assumes the same python version on client and server

    def serialize(self, writer: asyncio.StreamWriter):
        data_s = pickle.dumps(self.data)
        writer.write(struct.pack(self.HEADER_FORMAT, len(data_s)))
        writer.write(data_s)

    async def deserialize(self, reader: asyncio.StreamReader):
        hdr = await reader.readexactly(struct.calcsize(self.HEADER_FORMAT))
        hdr_fields = struct.unpack(self.HEADER_FORMAT, hdr)
        data_len = hdr_fields[0]
        data_s = await reader.readexactly(data_len)
        self.data = pickle.loads(data_s)
        return self.data


class DataPacketBin:
    """
    serialize and deserialize data in a packet for sending on a stream
    """
    HEADER_FORMAT = "<Q"
    HEADER_LEN = struct.calcsize(HEADER_FORMAT)
    SINGLE_NUM_LEN = struct.calcsize('d')

    def __init__(self, data: list[float] = None):
        self.data = data

    # stream protocol is |--size--|----data---|--size--|----data----|...
    # where size is 8 bytes, data is the size specified just before
    # and data is a concatenation of binary floats

    def serialize(self, writer: asyncio.StreamWriter):
        data_s = struct.pack(f"{len(self.data)}d", *self.data)
        writer.write(struct.pack(self.HEADER_FORMAT, len(data_s)))
        writer.write(data_s)

    async def deserialize(self, reader: asyncio.StreamReader):
        hdr = await reader.readexactly(self.HEADER_LEN)
        hdr_fields = struct.unpack(self.HEADER_FORMAT, hdr)
        data_len = hdr_fields[0]
        if data_len % self.SINGLE_NUM_LEN != 0:
            raise RuntimeError(f"unexpected data length not a whole number of doubles {data_len}")
        count_nums = int(data_len / self.SINGLE_NUM_LEN)
        data_s = await reader.readexactly(data_len)
        self.data = struct.unpack(f"{count_nums}d", data_s)
        return self.data


DataPacket = DataPacketBin
