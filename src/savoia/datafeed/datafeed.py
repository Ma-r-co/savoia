from decimal import Decimal
from savoia.config.decimal_config \
    import initializeDecimalContext, DECIMAL_PLACES

import os
import re
# import numpy as np
import pandas as pd

from savoia.event.event import Event, TickEvent
from savoia.types.types import Pair

from logging import getLogger, Logger
from typing import List, Iterator, Tuple
from queue import Queue
from abc import ABCMeta, abstractmethod
import time


class DataFeeder(metaclass=ABCMeta):
    """
    DataFeeder is an abstract base class providing an interface for
    all subsequent (inherited) data feeders (both live and historic).

    The goal of a (derived) DataFeeder object is to output a set of
    bid/ask/timestamp "ticks" for each currency pair and place them into
    an feed queue.
    The latest prices for each currencies will be held within Ticker
    object.

    This will replicate how a live strategy would function as current
    tick data would be streamed via a brokerage. Thus a historic and live
    system will be treated identically by the rest of the savoia
    backtesting suite.
    """
    logger: Logger
    feed_q: 'Queue[Event]'
    pairs: List[Pair]
    continue_backtest: bool

    @abstractmethod
    def __init__(self, pairs: List[Pair], feed_q: 'Queue[Event]'):
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class HistoricCSVDataFeeder(DataFeeder):
    """
    HistoricCSVDataFeeder is designed to read CSV files of
    tick data for each requested currency pair and stream those
    to the provided events queue.
    """
    logger: Logger
    pairs: List[Pair]
    feed_q: 'Queue[Event]'
    csv_dir: str
    pair_frames: List[str]
    file_dates: List[str]
    cur_date_idx: int
    cur_date_pairs: pd.DataFrame
    count: int

    def __init__(self, pairs: List[Pair], feed_q: 'Queue[Event]',
            csv_dir: str):
        """
        Initialises the HistoricCSVDataFeeder by requesting
        the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form
        'pair.csv', where "pair" is the currency pair. For
        GBP/USD the filename is GBPUSD.csv.

        Parameters:
        pairs - The list of currency pairs to obtain.
        feed_q - The events queue to send the ticks to.
        csv_dir - Absolute directory path to the CSV files.
        """
        self.logger = getLogger(__name__)
        self.pairs = pairs
        self.feed_q = feed_q
        self.csv_dir = csv_dir
        self.file_dates = self._list_all_file_dates()
        self.continue_backtest = True
        self.cur_date_idx = 0
        self.cur_date_pairs = self._open_convert_csv_files_for_day(
            self.file_dates[self.cur_date_idx]
        )
        initializeDecimalContext()
        self.count = 0

    def _list_all_csv_files(self) -> List[str]:
        files = os.listdir(self.csv_dir)
        pattern = re.compile(r"[A-Z]{6}_\d{8}.csv")
        matching_files = [f for f in files if pattern.search(f)]
        matching_files.sort()
        return matching_files

    def _list_all_file_dates(self) -> List[str]:
        """
        Removes the pair, underscore and '.csv' from the
        dates and eliminates duplicates. Returns a list
        of date strings of the form "YYYYMMDD".
        """
        csv_files = self._list_all_csv_files()
        de_dup_csv = list(set([f[7:-4] for f in csv_files]))
        de_dup_csv.sort()
        return de_dup_csv

    def _open_convert_csv_files_for_day(self, date_str: str) \
            -> Iterator[Tuple[str, str, str, str]]:
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a pairs dictionary.

        The function then concatenates all of the separate pairs
        for a single day into a single data frame that is time
        ordered, allowing tick data events to be added to the queue
        in a chronological fashion.
        """
        # for p in self.pairs:
        #    pair_path = os.path.join(self.csv_dir, '%s_%s.csv' % (p, date_str))
        #     self.logger.info("start read: %s", str(pair_path))
        #     with open(pair_path, 'r') as f:

        #     self.pair_frames[p] = pd.read_csv(
        #         pair_path,
        #         header=0,
        #         index_col=0,
        #         parse_dates=["Time"],
        #         dayfirst=True,
        #         names=("Time", "Ask", "Bid", "AskVolume", "BidVolume")
        #     )
        #     self.pair_frames[p]["Pair"] = p
        #     self.logger.info("end read: %s", str(pair_path))
        # return pd.concat(self.pair_frames.values()).sort_index().iterrows()
        self.pair_frames = []
        for p in self.pairs:
            pair_path = os.path.join(self.csv_dir, '%s_%s.csv' % (p, date_str))
            self.logger.info("start read: %s", str(pair_path))
            with open(pair_path, 'r') as f:
                f.__next__()
                for line in f:
                    self.pair_frames.append(line + f',{p}')
            self.logger.info("end read: %s", str(pair_path))
        self.logger.info('start sort')
        self.pair_frames.sort()

        def _gen() -> Iterator[Tuple[str, str, str, str]]:
            for row in self.pair_frames:
                date, ask, bid, ask_volume, bid_volume, pair = row.split(',')
                yield date, ask, bid, pair

        return _gen()

    def _update_csv_for_day(self) -> bool:
        try:
            dt = self.file_dates[self.cur_date_idx + 1]
        except IndexError:  # End of file dates
            return False
        else:
            self.cur_date_pairs = self._open_convert_csv_files_for_day(dt)
            self.cur_date_idx += 1
            return True

    def _stream_next_tick(self) -> None:
        try:
            date, ask, bid, pair = next(self.cur_date_pairs)
        except StopIteration:
            # End of the current days data
            if self._update_csv_for_day():
                date, ask, bid, pair = next(self.cur_date_pairs)
            else:  # End of the data
                self.continue_backtest = False
                return
        date = pd.Timestamp(date)
        bid = Decimal(bid).quantize(DECIMAL_PLACES)
        ask = Decimal(ask).quantize(DECIMAL_PLACES)

        tev = TickEvent(pair, date, bid, ask)
        self.feed_q.put(tev)

    def run(self) -> None:
        """
        Carries out an infinite while loop that read data and inject
        Tick events to event_q.
        """
        _start = time.time()
        self.logger.info('Start datafeed')
        while self.continue_backtest:
            self._stream_next_tick()
            self.count += 1
            if self.count % 1000 == 0:
                self.logger.info(f'Feeded {self.count}th data.')
        self.feed_q.put(None)
        self.logger.info('Finish datafeed: Elapsed Time[sec]: ' +
            f'{time.time() - _start}')
