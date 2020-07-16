from decimal import Decimal
from queue import Queue

from savoia.ticker.ticker import Ticker
from savoia.event.event import OrderEvent, Event, TickEvent, \
    SignalEvent, FillEvent
from savoia.portfolio.position import Position
from savoia.types.types import Pair
from savoia.result.result import Result, EquityResult, ExecutionResult

from logging import getLogger, Logger
from typing import Dict, List


class Portfolio(object):
    logger: Logger
    ticker: Ticker
    event_q: 'Queue[Event]'
    result_q: 'Queue[Result]'
    home_currency: str
    equity: Decimal
    balance: Decimal
    upl: Decimal
    pairs: List[Pair]
    positions: Dict[Pair, Position]

    def __init__(
        self, ticker: Ticker, event_q: 'Queue[Event]',
        result_q: 'Queue[Result]', home_currency: str, pairs: List[Pair],
        equity: Decimal
    ):
        self.logger = getLogger(__name__)
        self.ticker = ticker
        self.event_q = event_q
        self.result_q = result_q
        self.home_currency = home_currency
        self.equity = equity
        self.balance = self.equity
        self.upl = Decimal('0')
        self.pairs = pairs
        self.positions = self._initialize_positions()

    def _initialize_positions(self) -> Dict[Pair, Position]:
        _pos = {}
        for _pair in self.pairs:
            _pos[_pair] = Position(self.home_currency, _pair, self.ticker)
        return _pos

    def update_portfolio(self, event: TickEvent) -> None:
        """
        This updates all positions ensuring an up to date
        unrealised profit and loss (upl).
        """
        _upl: Dict[str, Decimal] = {}
        _result: EquityResult

        for _pair in self.pairs:
            _upl[_pair] = self.positions[_pair].update_position_price()
        self.upl = Decimal(str(sum(_upl.values())))
        self._update_equity()
        _upl['total'] = self.upl
        _result = EquityResult(
            time=event.time,
            equity=self.equity,
            balance=self.balance,
            upl=_upl
        )
        self.result_q.put(_result)

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
            order = OrderEvent(
                ref=event.ref, pair=event.pair, units=event.units,
                price=event.price, order_type=event.order_type, time=event.time)
            self.event_q.put(order)
            self.logger.info(f"OrderEvent Issued: {order}")
        else:
            self.logger.error(
                "Unable to execute order as price data was insufficient."
            )

    def execute_fill(self, event: FillEvent) -> None:
        '''Handles FillEvent'''
        _delta_balance: Decimal
        _delta_upl: Decimal

        _delta_balance, _delta_upl = \
            self.positions[event.pair].reflect_filled_order(
                event.units, event.price
            )

        self._update_equity(_delta_balance, _delta_upl)

        _result = ExecutionResult(
            time=event.time,
            pair=event.pair,
            units=event.units,
            price=event.price
        )
        self.result_q.put(_result)

    def _update_equity(self, delta_balance: Decimal = Decimal('0'),
            delta_upl: Decimal = Decimal('0')) -> None:
        self.balance += delta_balance
        self.upl += delta_upl
        self.equity = self.balance + self.upl
