from queue import Queue, Empty
import time

from savoia.config.dir_config import CSV_DATA_DIR
from savoia.types.types import Pair
from savoia.event.event import Event
from savoia.feed.price import PriceHandler
from savoia.strategy.strategy import Strategy
from savoia.portfolio.portfolio import Portfolio
from savoia.execution.execution import SimulatedExecution


from logging import getLogger, Logger
from typing import List, Dict, Union
from decimal import Decimal


class Backtest(object):
    """
    Enscapsulates the settings and components for carrying out
    an event-driven backtest on the foreign exchange markets.
    """
    pairs: List[Pair]
    data_handler: PriceHandler
    strategy: Strategy
    strategy_params: Dict[str, Union[Decimal, str, bool]]
    portfolio: Portfolio
    execution: SimulatedExecution
    equity: Decimal
    home_currency: str
    leverage: Decimal
    risk_per_trade: Decimal
    heartbeat: float
    max_iters: int
    iters: int
    logger: Logger
    events: 'Queue[Event]'

    def __init__(
        self, pairs: List[Pair], data_handler: PriceHandler, strategy: Strategy,
        strategy_params: Dict[str, Union[Decimal, str, bool]], portfolio: Portfolio,
        execution: SimulatedExecution, equity: Decimal, home_currency: str,
        leverage: Decimal, risk_per_trade: Decimal, heartbeat: float = 0.0,
        max_iters: int = 100000000
    ):
        """
        Initializes the backtest.
        """
        self.pairs = pairs
        self.events = Queue()
        self.csv_dir = CSV_DATA_DIR
        self.ticker = data_handler(self.pairs, self.events, self.csv_dir)
        self.strategy_params = strategy_params
        self.strategy = strategy(
            pairs=self.pairs,
            events=self.events,
            **self.strategy_params
        )
        self.equity = equity
        self.heartbeat = heartbeat
        self.max_iters = max_iters
        self.portfolio = portfolio(
            ticker=self.ticker,
            events_queue=self.events,
            home_currency=home_currency,
            leverage=leverage,
            equity=self.equity,
            risk_per_trade=risk_per_trade,
            isBacktest=True
        )
        self.execution = execution()
        self.logger = getLogger(__name__)
        self.iters = 0

    def _run_backtest(self) -> None:
        """
        Carries out an infinite while loop that polls the
        events queue and directs each event to either the
        strategy component of the execution handler. The
        loop will then pause for "heartbeat" seconds and
        continue until the maximum number of iterations is
        exceeded.
        """
        self.logger.info("Running Backtest...")
        while self.iters < self.max_iters and self.ticker.continue_backtest:
            try:
                event = self.events.get(False)
            except Empty:
                self.ticker.stream_next_tick()
            else:
                if event is not None:
                    if event.type == 'TICK':
                        self.strategy.calculate_signals(event)
                        self.portfolio.update_portfolio(event)
                    elif event.type == 'SIGNAL':
                        self.portfolio.execute_signal(event)
                    elif event.type == 'ORDER':
                        self.logger.info("Excecution order! :%s" % event)
                        self.execution.execute_order(event)
                    else:
                        raise Exception
            time.sleep(self.heartbeat)
            self.iters += 1

    def _output_performance(self) -> None:
        """
        Outputs the strategy performance from the backtest.
        """
        self.logger.info("Calculating Performance Metrics...")
        self.portfolio.output_results()

    def simulate_trading(self) -> None:
        """
        Simulates the backtest and outputs portfolio performance.
        """
        self._run_backtest()
        self._output_performance()
        self.logger.info("Backtest complete.")
