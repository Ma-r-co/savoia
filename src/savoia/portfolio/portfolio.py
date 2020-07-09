from decimal import Decimal
from queue import Queue
import os

import pandas as pd

from savoia.ticker.ticker import Ticker
from savoia.event.event import OrderEvent, Event, TickEvent, \
    SignalEvent, FillEvent
from savoia.performance.performance import create_drawdowns
from savoia.portfolio.position import Position
from savoia.config.dir_config import OUTPUT_RESULTS_DIR
from savoia.types.types import Pair

from logging import getLogger, Logger
from typing import Dict, TextIO, List


class Portfolio(object):
    logger: Logger
    ticker: Ticker
    events_queue: 'Queue[Event]'
    home_currency: str
    equity: Decimal
    balance: Decimal
    upl: Decimal
    isBacktest: bool
    pairs: List[Pair]
    positions: Dict[Pair, Position]

    def __init__(
        self, ticker: Ticker, events_queue: 'Queue[Event]', home_currency: str,
        pairs: List[Pair], equity: Decimal, isBacktest: bool = True
    ):
        self.logger = getLogger(__name__)
        self.ticker = ticker
        self.events_queue = events_queue
        self.home_currency = home_currency
        self.equity = equity
        self.balance = self.equity
        self.upl = Decimal('0')
        self.pairs = pairs
        self.isBacktest = isBacktest
        self.positions = self._initialize_positions()
        if self.isBacktest:
            self.backtest_file = self._create_equity_file()

    def _initialize_positions(self) -> Dict[Pair, Position]:
        _pos = {}
        for _pair in self.pairs:
            _pos[_pair] = Position(self.home_currency, _pair, self.ticker)
        return _pos

    def _create_equity_file(self) -> TextIO:
        filename: str = "backtest.csv"
        out_file: TextIO = open(os.path.join(OUTPUT_RESULTS_DIR, filename), "w")
        header: str = "Timestamp,Balance"
        for pair in self.ticker.pairs:
            header += ",%s" % pair
        header += "\n"
        out_file.write(header)
        if self.isBacktest:
            self.logger.info("Created equity file. Header as: %s", header[:-1])
        return out_file

    def output_results(self) -> None:
        # Closes off the Backtest.csv file so it can be
        # read via Pandas without problems
        self.backtest_file.close()

        in_filename = "backtest.csv"
        out_filename = "equity.csv"
        in_file = os.path.join(OUTPUT_RESULTS_DIR, in_filename)
        out_file = os.path.join(OUTPUT_RESULTS_DIR, out_filename)

        # Create equity curve dataframe
        df = pd.read_csv(in_file, index_col=0)
        df.dropna(inplace=True)
        df["Total"] = df.sum(axis=1)
        df["Returns"] = df["Total"].pct_change()
        df["Equity"] = (1.0 + df["Returns"]).cumprod()

        # Create drawdown statistics
        drawdown, max_dd, dd_duration = create_drawdowns(df["Equity"])
        df["Drawdown"] = drawdown
        df.to_csv(out_file, index=True)

        self.logger.info("Simulation complete and results exported to %s",
            out_filename)

    def update_portfolio(self, event: TickEvent) -> None:
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (upl).
        """
        _upl: Decimal = Decimal('0')

        for _pos in self.positions.values():
            _upl += _pos.update_position_price()
        self.upl = _upl
        self._update_equity()
        if self.isBacktest:
            out_line = f'{event.time}, {self.equity}'
            for pair in self.ticker.pairs:
                out_line += ",{self.positions[pair].upl}"
            out_line += "\n"
            self.backtest_file.write(out_line)

    def execute_signal(self, event: SignalEvent) -> None:
        '''Handles SignalEvent'''
        # Check that the prices ticker contains all necessary
        # currency pairs prior to executing an order
        _execute = True
        for pair in self.ticker.prices:
            if None in self.ticker.prices[pair].values():
                _execute = False

        # All necessary pricing data is available,
        # we can execute
        if _execute:
            order = OrderEvent(event.ref, event.instrument, event.units,
                event.order_type, event.time, event.price)
            self.events_queue.put(order)
            self.logger.info(f"OrderEvent Issued: {order}")
        else:
            self.logger.info(
                "Unable to execute order as price data was insufficient."
            )

    def execute_fill(self, event: FillEvent) -> None:
        '''Handles FillEvent'''
        _delta_balance: Decimal
        _delta_upl: Decimal

        _delta_balance, _delta_upl = \
            self.positions[event.instrument].reflect_filled_order(
                event.units, event.price
            )

        self._update_equity(_delta_balance, _delta_upl)

    def _update_equity(self, delta_balance: Decimal = Decimal('0'),
            delta_upl: Decimal = Decimal('0')) -> None:
        self.balance += delta_balance
        self.upl += delta_upl
        self.equity = self.balance + self.upl
