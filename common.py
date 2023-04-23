import struct
import pickle
import asyncio


class DataPacket:
    """
    serialize and deserialize data in a packet for sending on a stream
    """
    HEADER_FORMAT = "<Q"

    def __init__(self, data=None):
        self.data = data

    # stream protocol is |--size--|----data---|--size--|----data----|...
    # where size is 8 bytes, data is the size specified

    def serialize(self, writer: asyncio.StreamWriter):
        data_s = pickle.dumps(self.data)
        writer.write(struct.pack(self.HEADER_FORMAT, len(data_s)))
        writer.write(data_s)

    async def deserialize(self, reader: asyncio.StreamReader):
        hdr = await reader.readexactly(struct.calcsize(self.HEADER_FORMAT))
        hdr_fields = struct.unpack(self.HEADER_FORMAT, hdr)
        data_len = hdr_fields[0]
        data_s = await reader.readexactly(data_len)
        # print(f"Got {data_len}, {len(data_s)}")
        self.data = pickle.loads(data_s)
        return self.data

