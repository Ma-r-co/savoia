from savoia.backtest.backtest import Backtest

from savoia.types.types import Pair
from savoia.event.event import Event, TickEvent
from savoia.feed.price import PriceHandler
from savoia.strategy.strategy import DummyStrategy, Strategy
from savoia.portfolio.portfolio import Portfolio
from savoia.execution.execution import SimulatedExecution

from typing import List, Dict
from queue import Queue
from decimal import Decimal
from logging import Logger
import pandas as pd
from datetime import datetime

import pytest


class MockDataHandler(PriceHandler):
    def __init__(self, pairs: List[Pair], events_queue: 'Queue[Event]', csv_dir: str) -> None:
        self.pairs: List[Pair] = pairs
        self.events_queue: Queue['Event'] = events_queue
        self.prices = self._set_up_prices_dict()
        self.continue_backtest: bool = True
    
    def stream_next_tick(self) -> None:
        bid: Decimal = Decimal('102.3')
        ask: Decimal = Decimal('103.4')
        time: pd.Timestamp = pd.Timestamp(datetime.now())
        pair = self.pairs[0]
        self.prices[pair]["bid"] = bid
        self.prices[pair]["ask"] = ask
        self.prices[pair]["time"] = time
        inv_pair, inv_bid, inv_ask = self.invert_prices(pair, bid, ask)
        self.prices[inv_pair]["bid"] = inv_bid
        self.prices[inv_pair]["ask"] = inv_ask
        self.prices[inv_pair]["time"] = time
        te: TickEvent = TickEvent(
            pair, time, Decimal('102.3'), Decimal('103.4')
        )
        self.events_queue.put(te)


@pytest.fixture(scope='function')
def bt1() -> Backtest:
    pairs: List[Pair] = [Pair('USDJPY')]
    data_handler: PriceHandler = MockDataHandler
    strategy: Strategy = DummyStrategy
    strategy_params: Dict[str, Decimal] = {}
    portfolio: Portfolio = Portfolio
    execution: SimulatedExecution = SimulatedExecution
    equity: Decimal = Decimal('12345678.9')
    home_currency: str = 'JPY'
    leverage: Decimal = Decimal('1.0')
    risk_per_trade: Decimal = Decimal('0.8')
    heartbeat: float = 0.001
    max_iters: int = 105
    return Backtest(
        pairs, data_handler, strategy, strategy_params, portfolio, execution, equity, home_currency, leverage, risk_per_trade,
        heartbeat, max_iters
    )


def test_Backtest__init__(bt1: Backtest) -> None:
    assert bt1.pairs == ['USDJPY']
    assert isinstance(bt1.events, Queue)
    assert isinstance(bt1.csv_dir, str)
    assert isinstance(bt1.ticker, MockDataHandler)
    assert bt1.strategy_params == {}
    assert isinstance(bt1.strategy, DummyStrategy)
    assert bt1.equity == Decimal('12345678.9')
    assert bt1.heartbeat == 0.001
    assert bt1.max_iters == 105
    assert isinstance(bt1.portfolio, Portfolio)
    assert bt1.portfolio.isBacktest
    assert isinstance(bt1.execution, SimulatedExecution)
    assert isinstance(bt1.logger, Logger)


def test_max_run_backtest(bt1: Backtest) -> None:
    bt1._run_backtest()
    assert bt1.iters == 105
