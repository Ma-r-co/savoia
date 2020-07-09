import pandas as pd
from typing import Union
from datetime import datetime
from decimal import Decimal

from savoia.types.types import EventType, Pair


class Event(object):
    type: EventType


class TickEvent(Event):
    def __init__(self, instrument: Pair, time: Union[pd.Timestamp, datetime],
            bid: Decimal, ask: Decimal) -> None:
        self.type = EventType('TICK')
        self.instrument: Pair = instrument
        self.time: Union[pd.Timestamp, datetime] = time
        self.bid: Decimal = bid
        self.ask: Decimal = ask

    def __str__(self) -> str:
        return "Type: %s, Instrument: %s, Time: %s, Bid: %s, Ask: %s" % (
            str(self.type), str(self.instrument),
            str(self.time), str(self.bid), str(self.ask)
        )

    def __repr__(self) -> str:
        return str(self)


class SignalEvent(Event):
    def __init__(self, ref: str, instrument: Pair, order_type: str,
            units: Decimal, time: pd.Timestamp,
            price: Union[Decimal, None] = None):
        self.type = EventType('SIGNAL')
        self.ref = ref
        self.instrument: Pair = instrument
        self.order_type = order_type
        self.units = units
        self.time = time  # Time of the last tick that generated the signal
        self.price = price

    def __str__(self) -> str:
        return "Type: %s, Instrument: %s, Order Type: %s, Units: %s, Time: %s" \
            % (
                str(self.type), str(self.instrument),
                str(self.order_type), str(self.units), str(self.time)
            )

    def __repr__(self) -> str:
        return str(self)


class OrderEvent(Event):
    def __init__(self, ref: str, instrument: Pair, units: int, order_type: str,
            time: pd.Timestamp, price: Union[Decimal, None] = None):
        self.type = EventType('ORDER')
        self.ref = ref
        self.instrument: Pair = instrument
        self.units = units
        self.order_type = order_type
        self.time = time
        self.price = price

    def __str__(self) -> str:
        return "Type: %s, Instrument: %s, Units: %s, Order Type: %s, Price: %s"\
            % (
                str(self.type), str(self.instrument), str(self.units),
                str(self.order_type), str(self.price)
            )

    def __repr__(self) -> str:
        return str(self)


class FillEvent(Event):
    def __init__(self, ref: str, instrument: Pair, units: int, price: Decimal,
            status: str, time: pd.Timestamp):
        self.type = EventType('FILL')
        self.ref = ref
        self.instrument: Pair = instrument
        self.units = units
        self.price = price
        self.status = status
        self.time = time

    def __str__(self) -> str:
        return ("Type: %s, Instrument: %s, Units: %s, Price: %s, Time: %s" +
            ", Status: %s") % (
                str(self.type), str(self.instrument), str(self.units),
                str(self.price), str(self.time), str(self.status)
        )

    def __repr__(self) -> str:
        return str(self)
