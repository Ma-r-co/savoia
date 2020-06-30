from decimal import Decimal
from queue import Queue
import os

import pandas as pd

from savoia.datafeed.ticker import Ticker
from savoia.event.event import OrderEvent, Event, TickEvent, SignalEvent
from savoia.performance.performance import create_drawdowns
from savoia.portfolio.position import Position
from savoia.config.dir_config import OUTPUT_RESULTS_DIR
from savoia.types.types import Pair

from logging import getLogger, Logger
from typing import Dict, TextIO


class Portfolio(object):
    logger: Logger
    ticker: Ticker
    events_queue: 'Queue[Event]'
    home_currency: str
    leverage: Decimal
    equity: Decimal
    balance: Decimal
    risk_per_trade: Decimal
    isBacktest: bool
    trade_units: Decimal
    positions: Dict[Pair, Position]

    def __init__(
        self, ticker: Ticker, events_queue: 'Queue[Event]', home_currency: str,
        leverage: Decimal, equity: Decimal, risk_per_trade: Decimal,
        isBacktest: bool = True
    ):
        self.logger = getLogger(__name__)
        self.ticker = ticker
        self.events_queue = events_queue
        self.home_currency = home_currency
        self.leverage = leverage
        self.equity = equity
        self.balance = self.equity
        self.risk_per_trade = risk_per_trade
        self.isBacktest = isBacktest
        self.trade_units = self.calc_risk_position_size()
        self.positions = {}
        if self.isBacktest:
            self.backtest_file = self.create_equity_file()

    def calc_risk_position_size(self) -> Decimal:
        return self.equity * self.risk_per_trade

    def add_new_position(self, position_type: str, currency_pair: Pair,
            units: int, ticker: Ticker) -> None:
        ps: Position = Position(
            self.home_currency, position_type,
            currency_pair, units, ticker
        )
        self.positions[currency_pair] = ps

    def add_position_units(self, currency_pair: Pair, units: int) -> bool:
        if currency_pair not in self.positions:
            return False
        else:
            ps = self.positions[currency_pair]
            ps.add_units(units)
            return True

    def remove_position_units(self, currency_pair: Pair, units: int) -> bool:
        if currency_pair not in self.positions:
            return False
        else:
            ps: Position = self.positions[currency_pair]
            pnl: Decimal = ps.remove_units(units)
            self.balance += pnl
            return True

    def close_position(self, currency_pair: Pair) -> bool:
        if currency_pair not in self.positions:
            return False
        else:
            ps: Position = self.positions[currency_pair]
            pnl: Decimal = ps.close_position()
            self.balance += pnl
            del[self.positions[currency_pair]]
            return True

    def create_equity_file(self) -> TextIO:
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

    def update_portfolio(self, tick_event: TickEvent) -> None:
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (PnL).
        """
        currency_pair = tick_event.instrument
        if currency_pair in self.positions:
            ps = self.positions[currency_pair]
            ps.update_position_price()
        if self.isBacktest:
            out_line = "%s,%s" % (tick_event.time, self.balance)
            for pair in self.ticker.pairs:
                if pair in self.positions:
                    out_line += ",%s" % self.positions[pair].profit_base
                else:
                    out_line += ",0.00"
            out_line += "\n"
            self.backtest_file.write(out_line)

    def execute_signal(self, signal_event: SignalEvent) -> None:
        # Check that the prices ticker contains all necessary
        # currency pairs prior to executing an order
        execute = True
        tp = self.ticker.prices
        for pair in tp:
            if tp[pair]["ask"] is None or tp[pair]["bid"] is None:
                execute = False

        # All necessary pricing data is available,
        # we can execute
        if execute:
            side = signal_event.side
            currency_pair = signal_event.instrument
            units = int(self.trade_units)

            # If there is no position, create one
            if currency_pair not in self.positions:
                if side == "buy":
                    position_type = "long"
                else:
                    position_type = "short"
                self.add_new_position(
                    position_type, currency_pair, units, self.ticker
                )

            # If a position exists add or remove units
            else:
                ps = self.positions[currency_pair]

                if side == "buy" and ps.position_type == "long":
                    self.add_position_units(currency_pair, units,)
                elif side == "sell" and ps.position_type == "long":
                    if units == ps.units:
                        self.close_position(currency_pair)
                    elif units < ps.units:
                        self.remove_position_units(currency_pair, units)
                    elif units > ps.units:
                        pass
                        self.close_position(currency_pair)
                        self.add_new_position(
                            "short", currency_pair, units - ps.units,
                            self.ticker
                        )
                elif side == "buy" and ps.position_type == "short":
                    if units == ps.units:
                        self.close_position(currency_pair)
                    elif units < ps.units:
                        self.remove_position_units(currency_pair, units)
                    elif units > ps.units:
                        self.close_position(currency_pair)
                        self.add_new_position(
                            "long", currency_pair, units - ps.units, self.ticker
                        )
                elif side == "sell" and ps.position_type == "short":
                    self.add_position_units(currency_pair, units)
            order = OrderEvent(currency_pair, units, "market", side)
            self.events_queue.put(order)
            self.logger.info("Portfolio Balance: %s", self.balance)
        else:
            self.logger.info(
                "Unable to execute order as price data was insufficient."
            )
