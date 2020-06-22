from decimal import Decimal
from savoia.config.decimal_config import initializeDecimalContext, DECIMAL_PLACES

import os
import re
# import numpy as np
import pandas as pd

from savoia.event.event import Event, TickEvent
from savoia.types.types import Pair, Price

from logging import getLogger, Logger
from typing import List, Dict, Tuple, Iterator
from queue import Queue


class PriceHandler(object):
    """
    PriceHandler is an abstract base class providing an interface for
    all subsequent (inherited) data handlers (both live and historic).

    The goal of a (derived) PriceHandler object is to output a set of
    bid/ask/timestamp "ticks" for each currency pair and place them into
    an event queue.
    It's also responsible for holding the latest prices for each currency
    pair.

    This will replicate how a live strategy would function as current
    tick data would be streamed via a brokerage. Thus a historic and live
    system will be treated identically by the rest of the savoia
    backtesting suite.
    """
    logger: Logger
    pairs: List[Pair]
    events_queue: 'Queue[Event]'
    prices: Dict[Pair, Price]
    continue_backtest: bool
    
    def _set_up_prices_dict(self) -> Dict[Pair, Price]:
        prices_dict = dict((Pair(k), v)
                           for k, v in [(p, Price({
                               "bid": None,
                               "ask": None,
                               "time": None
                           })) for p in self.pairs])
        inv_prices_dict = dict((Pair(k), v)
                               for k, v in [("%s%s" % (p[3:], p[:3]), Price({
                                   "bid": None,
                                   "ask": None,
                                   "time": None
                               })) for p in self.pairs])
        prices_dict.update(inv_prices_dict)
        return prices_dict

    def invert_prices(self, pair: Pair, bid: Decimal, ask: Decimal) -> Tuple[Pair, Decimal, Decimal]:
        inv_pair = Pair("%s%s" % (pair[3:], pair[:3]))
        inv_bid = (Decimal("1.0") / ask).quantize(DECIMAL_PLACES)
        inv_ask = (Decimal("1.0") / bid).quantize(DECIMAL_PLACES)
        return inv_pair, inv_bid, inv_ask


class HistoricCSVPriceHandler(PriceHandler):
    """
    HistoricCSVPriceHandler is designed to read CSV files of
    tick data for each requested currency pair and stream those
    to the provided events queue.
    """
    csv_dir: str
    pair_frames: Dict[Pair, pd.DataFrame]
    file_dates: List[str]
    cur_date_idx: int
    cur_date_pairs: pd.DataFrame

    def __init__(self, pairs: List[Pair], events_queue: 'Queue[Event]', csv_dir: str) -> None:
        """
        Initialises the historic data handler by requesting
        the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form
        'pair.csv', where "pair" is the currency pair. For
        GBP/USD the filename is GBPUSD.csv.

        Parameters:
        pairs - The list of currency pairs to obtain.
        events_queue - The events queue to send the ticks to.
        csv_dir - Absolute directory path to the CSV files.
        """
        self.logger = getLogger(__name__)
        self.pairs = pairs
        self.events_queue = events_queue
        self.csv_dir = csv_dir
        self.prices = self._set_up_prices_dict()
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

    def _open_convert_csv_files_for_day(self, date_str: str) -> Iterator[pd.DataFrame]:
        """
        Opens the CSV files from the data directory, converting
        them into pandas DataFrames within a pairs dictionary.

        The function then concatenates all of the separate pairs
        for a single day into a single data frame that is time
        ordered, allowing tick data events to be added to the queue
        in a chronological fashion.
        """
        for p in self.pairs:
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
        self.prices[pair]["bid"] = bid
        self.prices[pair]["ask"] = ask
        self.prices[pair]["time"] = index

        # Create decimalised prices for inverted pair
        inv_pair, inv_bid, inv_ask = self.invert_prices(pair, bid, ask)
        self.prices[inv_pair]["bid"] = inv_bid
        self.prices[inv_pair]["ask"] = inv_ask
        self.prices[inv_pair]["time"] = index

        tev = TickEvent(pair, index, bid, ask)
        self.events_queue.put(tev)
