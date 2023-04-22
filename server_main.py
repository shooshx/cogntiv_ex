# TODO: type hints, requirements
# need 3.11
import sys
import time
import argparse
import asyncio
import socket
import logging
import numpy as np
import numpy.random as np_rn

import common

logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

VECTOR_LEN = 50
SEND_FREQ_HZ = 1000


SEND_DELAY_SEC = 1/SEND_FREQ_HZ

ACCURATE_TIMING = True

# based on TCP echo server example in asyncio documentation


class VectorSendHandler:
    def __init__(self):
        self.rng = np_rn.default_rng()

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')

        logger.info(f"Received connection from {addr!r}")
        scratch_pad = np.zeros(VECTOR_LEN)

        while True:
            start_time = time.perf_counter()
            data = self.rng.standard_normal(VECTOR_LEN, out=scratch_pad)

            try:
                common.DataPacket(data).serialize(writer)
                await writer.drain()
            except ConnectionError as e:
                logger.info(f'Client disconnected: {str(e)}')
                break

            if not ACCURATE_TIMING:
                await asyncio.sleep(SEND_DELAY_SEC)
            else:
                while True:
                    await asyncio.sleep(0)
                    now = time.perf_counter()
                    if now - start_time >= SEND_DELAY_SEC:
                        break

            now = time.perf_counter()
            #print(f"send times {now-start_time}")

        #print("Close the connection")
        #writer.close()
        #await writer.wait_closed()

async def main(argv):
    arg_parser = argparse.ArgumentParser('Server')
    arg_parser.add_argument('address', nargs='?', default='127.0.0.1', help='address to bind to')
    arg_parser.add_argument('port', nargs='?', type=int, default=8888, help='port to bind to')
    args = arg_parser.parse_args(argv)

    #server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #server_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    #server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10)
    #server_socket.bind((address, args.port))
    #server_socket.listen()

    handler = VectorSendHandler()
    server = await asyncio.start_server(handler.handle_client, host=args.address, port=args.port) #sock=server_socket)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    print(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()



if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
