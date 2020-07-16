import copy

from savoia.event.event import SignalEvent, TickEvent, Event
from savoia.types.types import Pair


from typing import List, Dict
from typing_extensions import TypedDict
from queue import Queue
from decimal import Decimal
from abc import ABCMeta, abstractmethod


class Strategy(metaclass=ABCMeta):
    @abstractmethod
    def calculate_signals(self, event: TickEvent) -> None:
        pass


class DummyStrategy(object):
    def __init__(self, pairs: List[Pair], event_q: 'Queue[Event]') -> None:
        self.pairs = pairs
        self.event_q = event_q
        self.ticks = 0
        self.invested = False

    def calculate_signals(self, event: TickEvent) -> None:
        if event.type == 'TICK' and event.pair == self.pairs[0]:
            if self.ticks % 100 == 0:
                if self.invested is False:
                    signal = SignalEvent(
                        ref=str(self.ticks),
                        pair=self.pairs[0],
                        order_type="market",
                        units=Decimal(100),
                        time=event.time,
                        price=event.bid
                    )
                    self.event_q.put(signal)
                    self.invested = True
                else:
                    signal = SignalEvent(
                        ref=str(self.ticks),
                        pair=self.pairs[0],
                        order_type="market",
                        units=Decimal(-100),
                        time=event.time,
                        price=event.bid
                    )
                    self.event_q.put(signal)
                    self.invested = False
            self.ticks += 1


class MACSAttr(TypedDict):
    ticks: int
    invested: bool
    short_sma: Decimal
    long_sma: Decimal


class MovingAverageCrossStrategy(object):
    def __init__(
        self, pairs: List[Pair], event_q: 'Queue[Event]',
        short_window: int = 500, long_window: int = 2000
    ) -> None:
        self.pairs: List[Pair] = pairs
        self.pairs_dict = self.create_pairs_dict()
        self.event_q = event_q
        self.short_window = short_window
        self.long_window = long_window

    def create_pairs_dict(self) -> Dict[Pair, MACSAttr]:
        attr_dict: MACSAttr = {
            "ticks": 0,
            "invested": False,
            "short_sma": Decimal(0),
            "long_sma": Decimal(0)
        }
        pairs_dict = {}
        for p in self.pairs:
            pairs_dict[p] = copy.deepcopy(attr_dict)
        return pairs_dict

    def calc_rolling_sma(self, sma_m_1: Decimal, window: int, price: Decimal) \
            -> Decimal:
        return ((sma_m_1 * (window - 1)) + price) / window

    def calculate_signals(self, event: TickEvent) -> None:
        if event.type == 'TICK':
            pair = event.pair
            price = event.bid
            pd = self.pairs_dict[pair]
            if pd["ticks"] == 0:
                pd["short_sma"] = price
                pd["long_sma"] = price
            else:
                pd["short_sma"] = self.calc_rolling_sma(
                    pd["short_sma"], self.short_window, price)
                pd["long_sma"] = self.calc_rolling_sma(pd["long_sma"],
                                                       self.long_window, price)
            if pd["ticks"] > self.short_window:
                if pd["short_sma"] > pd["long_sma"] and not pd["invested"]:
                    signal = SignalEvent(pair, "market", "buy",
                                         event.time)
                    self.event_q.put(signal)
                    pd["invested"] = True
                if pd["short_sma"] < pd["long_sma"] and pd["invested"]:
                    signal = SignalEvent(pair, "market", "sell",
                                         event.time)
                    self.event_q.put(signal)
                    pd["invested"] = False
            pd["ticks"] += 1
