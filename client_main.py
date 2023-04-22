import sys
import time
import argparse
import asyncio
import socket
import collections
import itertools
import abc
import logging
import numpy as np
import csv

import common

logging.basicConfig(format='%(asctime)s: %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


VECTORS_BATCH_SIZE = 100


class RateTrackerBase(abc.ABC):
    def __init__(self):
        self.last_time = None

    @abc.abstractmethod
    def _add(self, v):
        pass

    def got_packet(self):
        now = time.perf_counter()
        if self.last_time is None:
            self.last_time = now
            return  # first ever sample is skipped since we can't add a rate measure in the first sample
        diff = now - self.last_time
        self.last_time = now
        if diff != 0:
            self._add(1/diff)  # convert to frequency
        #print(f"packet {self.size()}  {diff}")


class RateTrackerSimple(RateTrackerBase):
    def __init__(self):
        super().__init__()
        self.samples = collections.deque()

    def _add(self, v):
        self.samples.append(v)

    def size(self):
        return len(self.samples)

    def reset(self):
        self.samples.clear()

    def stats(self):
        a = np.array(self.samples)
        mean = np.mean(a)
        std = np.std(a)
        return mean, std


class DataAnalytics:
    def __init__(self):
        self.reset()

    def add(self, v):
        self.vectors.append(v)

    def size(self):
        return len(self.vectors)

    def reset(self):
        self.vectors = []

    def stats(self):
        mat = np.array(self.vectors)
        means = np.mean(mat, axis=0)
        stds = np.std(mat, axis=0)
        return means, stds



async def main(argv):
    arg_parser = argparse.ArgumentParser('Client')
    arg_parser.add_argument('host', nargs='?', default='127.0.0.1', help='host to connect to')
    arg_parser.add_argument('port', nargs='?', type=int, default=8888, help='port to connect to')
    arg_parser.add_argument('out_file', nargs='?', default=None, help='name of output file (default: out_<timestamp>.csv)')
    args = arg_parser.parse_args(argv)

    logger.info(f'Connecting to {args.host}:{args.port}')

    #client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    #client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 10000)
    #client_socket.connect((host, port))

    reader, writer = await asyncio.open_connection(host=args.host, port=args.port) #sock=client_socket)
    logger.info(f'My address: {writer.get_extra_info("sockname")}')

    input_rate = RateTrackerSimple()
    accum_data = DataAnalytics()

    out_name = args.out_file if args.out_file is not None else f'out_{int(time.time())}.csv'
    logger.info(f'Opening output: {out_name}')
    out_file = open(out_name, 'w', newline='')
    csv_writer = csv.writer(out_file)
    # not write a csv header since we don't know the size of the vector at this point

    while True:
        try:
            data = await common.DataPacket().deserialize(reader)
        except asyncio.exceptions.CancelledError:  # happens when pressing Ctrl+C
            logger.info(f'cancelled')
            break

        input_rate.got_packet()
        accum_data.add(data)
        if accum_data.size() >= VECTORS_BATCH_SIZE:
            rate_mean, rate_std = input_rate.stats()
            logger.debug(f"data rate of last {input_rate.size()}: {rate_mean:.2f} Hz  std:{rate_std:.2f} Hz")
            data_means, data_std = accum_data.stats()

            def row_gen():  # output using generator to avoid copying everything to a long row
                yield rate_mean
                yield rate_std
                for d in data_means:
                    yield d
                for d in data_std:
                    yield d

            csv_writer.writerow(row_gen())
            input_rate.reset()
            accum_data.reset()


    print('Close the connection')
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
