import sys
import time
import argparse
import asyncio
import logging
import numpy as np
import numpy.random as np_rn

import common

logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

VECTOR_LEN = 50
SEND_FREQ_HZ = 1000
HIGH_ACCURACY = True


class ProducerStdNorm:
    """
    Produce standard normal random vectors
    """
    def __init__(self, seed=None):
        self._rng = np_rn.default_rng(seed=seed)
        # reuse the same vector to reduce memory allocation
        self._scratch_pad = np.zeros(VECTOR_LEN)

    def next_vec(self):
        data = self._rng.standard_normal(VECTOR_LEN, out=self._scratch_pad)
        return data


class ProducerTest:
    """
    Produces test data where every consecutive 100 vectors are the same number
    """
    def __init__(self):
        self._count = 0
        self._data = np.zeros(VECTOR_LEN)

    def next_vec(self):
        self._count += 1
        if self._count >= 100:
            self._data += 1


class VectorSendHandler:
    SEND_DELAY_SEC = 1 / SEND_FREQ_HZ

    def __init__(self, producer):
        self.producer = producer

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info("peername")
        logger.info(f"Received connection from {addr}")

        while True:
            start_time = time.perf_counter()
            data = self.producer.next_vec()

            try:
                common.DataPacket(data).serialize(writer)
                await writer.drain()
            except ConnectionError as e:
                logger.info(f"Client disconnected: {str(e)}")
                break

            if not HIGH_ACCURACY:
                # on windows this has resolution of 16 msec, which is not accurate enough
                await asyncio.sleep(self.SEND_DELAY_SEC)
            else:
                # to be more accurate we do an async busy-wait
                while True:
                    await asyncio.sleep(0)
                    now = time.perf_counter()
                    if now - start_time >= self.SEND_DELAY_SEC:
                        break

            # end_time = time.perf_counter()
            # logger.debug(f"send time: {(end_time-start_time}")


def parse_args(argv):
    arg_parser = argparse.ArgumentParser("Server")
    arg_parser.add_argument("address", nargs="?", default="127.0.0.1", help="address to bind to")
    arg_parser.add_argument("port", nargs="?", type=int, default=8888, help="port to bind to")
    return arg_parser.parse_args(argv)


async def main(argv):
    args = parse_args(argv)

    handler = VectorSendHandler(ProducerStdNorm())
    server = await asyncio.start_server(handler.handle_client, host=args.address, port=args.port)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    # Requires at least python 3.7, in 3.11 this also support KeyboardInterrupt from Ctrl+C
    sys.exit(asyncio.run(main(sys.argv[1:])))
