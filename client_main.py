import sys
import time
import argparse
import asyncio
import collections
import abc
import math
import logging
import numpy as np
import csv

import common

logging.basicConfig(format="%(asctime)s: %(message)s", level=logging.DEBUG)
logger = logging.getLogger(__name__)

VECTORS_BATCH_SIZE = 100


class RateTrackerBase(abc.ABC):
    def __init__(self):
        self.last_time = None

    @abc.abstractmethod
    def _add(self, v: float):
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
        # print(f"packet {self.size()}  {diff}")


class RateTrackerSimple(RateTrackerBase):
    """
    Track the rate of packet arrival by simply keeping all the data in a queue
    """
    def __init__(self):
        super().__init__()
        self._samples = collections.deque()

    def _add(self, v: float):
        self._samples.append(v)

    def size(self) -> int:
        return len(self._samples)

    def reset(self):
        self._samples.clear()

    def stats(self):
        a = np.array(self._samples)
        mean = np.mean(a)
        std = np.std(a)
        return mean, std


class RateTrackerRolling(RateTrackerBase):
    """
    Track the rate of packet arrival using O(1) memory rolling mean and std calculation
    see https://nestedsoftware.com/2018/03/27/calculating-standard-deviation-on-streaming-data-253l.23919.html
    """
    def __init__(self):
        super().__init__()
        self.reset()

    def reset(self):
        self._count = 0
        self._mean = 0
        self._dsq = 0

    def size(self) -> int:
        return self._count

    def _add(self, v: float):
        self._count += 1
        mean_diff = (v - self._mean) / self._count
        new_mean = self._mean + mean_diff
        dsq_inc = (v - new_mean) * (v - self._mean)
        new_dsq = self._dsq + dsq_inc
        self._mean = new_mean
        self._dsq = new_dsq

    def stats(self):
        variance = (self._dsq / self._count) if self._count > 0 else 0
        return self._mean, math.sqrt(variance)


class DataAnalytics:
    """
    Keep track of the last N vectors in a numpy matrix and calculation stats on it
    """
    def __init__(self):
        self.reset()

    def reset(self):
        self.vectors = []

    def add(self, v):
        self.vectors.append(v)

    def size(self):
        return len(self.vectors)

    def stats(self):
        mat = np.array(self.vectors)
        # stats on the temporal axis
        means = np.mean(mat, axis=0)
        stds = np.std(mat, axis=0)
        return means, stds


def parse_args(argv):
    arg_parser = argparse.ArgumentParser("Client")
    arg_parser.add_argument("host", nargs="?", default="127.0.0.1", help="host to connect to")
    arg_parser.add_argument("port", nargs="?", type=int, default=8888, help="port to connect to")
    arg_parser.add_argument("out_file", nargs="?", default=None, help="name of output file (default: out_<time>.csv)")
    return arg_parser.parse_args(argv)


async def main(argv):
    args = parse_args(argv)

    logger.info(f"Connecting to {args.host}:{args.port}")

    reader, writer = await asyncio.open_connection(host=args.host, port=args.port)
    myaddr = writer.get_extra_info("sockname")
    logger.info(f"My address: {myaddr}")

    # input_rate = RateTrackerSimple()
    input_rate = RateTrackerRolling()
    accum_data = DataAnalytics()

    out_name = args.out_file if args.out_file is not None else f"out_{int(time.time())}.csv"
    logger.info(f"Opening output: {out_name}")
    out_file = open(out_name, "w", newline='')
    csv_writer = csv.writer(out_file)
    # not write a csv header since we don't know the size of the vector at this point

    while True:
        try:
            data = await common.DataPacket().deserialize(reader)
        except asyncio.exceptions.CancelledError:  # happens when pressing Ctrl+C (python 3.11)
            logger.info("cancelled")
            break

        input_rate.got_packet()
        accum_data.add(data)
        if accum_data.size() >= VECTORS_BATCH_SIZE:
            # assume that we want to output the rate stats at the same cadence as the data analytics
            rate_mean, rate_std = input_rate.stats()
            logger.debug(f"data rate of last {input_rate.size()}: {rate_mean:.2f} Hz  std:{rate_std:.2f} Hz")
            data_means, data_std = accum_data.stats()

            def row_gen() -> float:  # output using generator to avoid copying everything to a long row
                yield rate_mean
                yield rate_std
                for d in data_means:
                    yield d
                for d in data_std:
                    yield d

            csv_writer.writerow(row_gen())
            input_rate.reset()
            accum_data.reset()

    logger.info(f"Closing the connection {myaddr}")
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
