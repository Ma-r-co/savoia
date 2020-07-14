import pandas as pd
from decimal import Decimal

from savoia.types.types import EventType, Pair


class Event(object):
    type: EventType


class TickEvent(Event):
    def __init__(self, pair: Pair, time: pd.Timestamp,
            bid: Decimal, ask: Decimal) -> None:
        self.type = EventType('TICK')
        self.pair: Pair = pair
        self.time: pd.Timestamp = time
        self.bid: Decimal = bid
        self.ask: Decimal = ask

    def __str__(self) -> str:
        return "Type: %s, Pair: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.pair),
            str(self.time), str(self.bid), str(self.ask)
        )

    def __repr__(self) -> str:
        return str(self)


class SignalEvent(Event):
    def __init__(self, ref: str, pair: Pair, time: pd.Timestamp,
            order_type: str, units: Decimal, price: Decimal):
        self.type = EventType('SIGNAL')
        self.ref = ref
        self.pair: Pair = pair
        self.order_type = order_type
        self.units = units
        self.time = time  # Time of the last tick that generated the signal
        self.price = price

    def __str__(self) -> str:
        _form = "Type: %s, Ref: %s, Pair: %s, Time: %s, OrderType: %s, " + \
            "Units: %s, Price: %s"
        return _form \
            % (
                self.type, self.ref, self.pair, self.time, self.order_type,
                self.units, self.price
            )

    def __repr__(self) -> str:
        return str(self)


class OrderEvent(Event):
    def __init__(self, ref: str, pair: Pair, time: pd.Timestamp,
            order_type: str, units: Decimal, price: Decimal):
        self.type = EventType('ORDER')
        self.ref: str = ref
        self.order_type = order_type
        self.pair: Pair = pair
        self.units = units
        self.time = time
        self.price = price

    def __str__(self) -> str:
        _form = "Type: %s, Ref: %s, Pair: %s, Time: %s, OrderType: %s, " + \
            "Units: %s, Price: %s"
        return _form \
            % (
                self.type, self.ref, self.pair, self.time, self.order_type,
                self.units, self.price
            )

    def __repr__(self) -> str:
        return str(self)


class FillEvent(Event):
    def __init__(self, ref: str, pair: Pair, time: pd.Timestamp,
            units: int, price: Decimal, status: str):
        self.type = EventType('FILL')
        self.ref = ref
        self.pair: Pair = pair
        self.units = units
        self.price = price
        self.status = status
        self.time = time

    def __str__(self) -> str:
        _form = "Type: %s, Ref: %s, Pair: %s, Time: %s, " + \
            "Units: %s, Price: %s, Status: %s"
        return _form % (
            self.type, self.ref, self.pair, self.time,
            self.units, self.price, self.status
        )

    def __repr__(self) -> str:
        return str(self)
