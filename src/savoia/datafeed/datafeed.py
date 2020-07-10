from decimal import Decimal
from savoia.config.decimal_config \
    import initializeDecimalContext, DECIMAL_PLACES
from savoia.ticker.ticker import Ticker

import os
import re
# import numpy as np
import pandas as pd

from savoia.event.event import Event, TickEvent
from savoia.types.types import Pair

from logging import getLogger, Logger
from typing import List, Dict, Iterator
from queue import Queue
from abc import ABCMeta, abstractmethod


class DataFeeder(metaclass=ABCMeta):
    """
    DataFeeder is an abstract base class providing an interface for
    all subsequent (inherited) data feeders (both live and historic).

    The goal of a (derived) DataFeeder object is to output a set of
    bid/ask/timestamp "ticks" for each currency pair and place them into
    an event queue.
    The latest prices for each currencies will be held within Ticker
    object.

    This will replicate how a live strategy would function as current
    tick data would be streamed via a brokerage. Thus a historic and live
    system will be treated identically by the rest of the savoia
    backtesting suite.
    """
    logger: Logger
    event_q: 'Queue[Event]'
    continue_backtest: bool

    @abstractmethod
    def stream_next_tick(self) -> None:
        pass


class HistoricCSVDataFeeder(DataFeeder):
    """
    HistoricCSVDataFeeder is designed to read CSV files of
    tick data for each requested currency pair and stream those
    to the provided events queue and update a Ticker object.
    """
    ticker: Ticker
    event_q: 'Queue[Event]'
    csv_dir: str
    pair_frames: Dict[Pair, pd.DataFrame]
    file_dates: List[str]
    cur_date_idx: int
    cur_date_pairs: pd.DataFrame

    def __init__(self, ticker: Ticker, event_q: 'Queue[Event]',
            csv_dir: str) -> None:
        """
        Initialises the HistoricCSVDataFeeder by requesting
        the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form
        'pair.csv', where "pair" is the currency pair. For
        GBP/USD the filename is GBPUSD.csv.

        Parameters:
        pairs - The list of currency pairs to obtain.
        event_q - The events queue to send the ticks to.
        csv_dir - Absolute directory path to the CSV files.
        """
        self.logger = getLogger(__name__)
        self.ticker = ticker
        self.event_q = event_q
        self.csv_dir = csv_dir
        self.pair_frames = {}
        self.file_dates = self._list_all_file_dates()
        self.continue_backtest = True
        self.cur_date_idx = 0
        self.cur_date_pairs = self._open_convert_csv_files_for_day(
            self.file_dates[self.cur_date_idx]
        )
        initializeDecimalContext()

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
            -> Iterator[pd.DataFrame]:
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a pairs dictionary.

        The function then concatenates all of the separate pairs
        for a single day into a single data frame that is time
        ordered, allowing tick data events to be added to the queue
        in a chronological fashion.
        """
        for p in self.ticker.pairs:
            pair_path = os.path.join(self.csv_dir, '%s_%s.csv' % (p, date_str))
            self.logger.info("start read: %s", str(pair_path))
            self.pair_frames[p] = pd.io.parsers.read_csv(
                pair_path,
                header=0,
                index_col=0,
                parse_dates=["Time"],
                dayfirst=True,
                names=("Time", "Ask", "Bid", "AskVolume", "BidVolume")
            )
            self.logger.info("end read: %s", str(pair_path))
            self.pair_frames[p]["Pair"] = p
        return pd.concat(self.pair_frames.values()).sort_index().iterrows()

    def _update_csv_for_day(self) -> bool:
        try:
            dt = self.file_dates[self.cur_date_idx + 1]
        except IndexError:  # End of file dates
            return False
        else:
            self.cur_date_pairs = self._open_convert_csv_files_for_day(dt)
            self.cur_date_idx += 1
            return True

    def stream_next_tick(self) -> None:
        try:
            index, row = next(self.cur_date_pairs)
        except StopIteration:
            # End of the current days data
            if self._update_csv_for_day():
                index, row = next(self.cur_date_pairs)
            else:  # End of the data
                self.continue_backtest = False
                return
        pair = row["Pair"]
        bid = Decimal(str(row["Bid"])).quantize(DECIMAL_PLACES)
        ask = Decimal(str(row["Ask"])).quantize(DECIMAL_PLACES)

        # Create decimalaised prices for trade pair
        self.ticker.prices[pair]["bid"] = bid
        self.ticker.prices[pair]["ask"] = ask
        self.ticker.prices[pair]["time"] = index

        # Create decimalised prices for inverted pair
        inv_pair, inv_bid, inv_ask = self.ticker.invert_prices(pair, bid, ask)
        self.ticker.prices[inv_pair]["bid"] = inv_bid
        self.ticker.prices[inv_pair]["ask"] = inv_ask
        self.ticker.prices[inv_pair]["time"] = index

        tev = TickEvent(pair, index, bid, ask)
        self.event_q.put(tev)
