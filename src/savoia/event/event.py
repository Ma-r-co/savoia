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
    def __init__(self, instrument: Pair, order_type: str, side: str,
            time: pd.Timestamp):
        self.type = EventType('SIGNAL')
        self.instrument: Pair = instrument
        self.order_type = order_type
        self.side = side
        self.time = time  # Time of the last tick that generated the signal

    def __str__(self) -> str:
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s, Time: %s" \
            % (
                str(self.type), str(self.instrument),
                str(self.order_type), str(self.side), str(self.time)
            )

    def __repr__(self) -> str:
        return str(self)


class OrderEvent(Event):
    def __init__(self, instrument: Pair, units: int, order_type: str,
            side: str):
        self.type = EventType('ORDER')
        self.instrument: Pair = instrument
        self.units = units
        self.order_type = order_type
        self.side = side

    def __str__(self) -> str:
        return "Type: %s, Instrument: %s, Units: %s, Order Type: %s, Side: %s" \
            % (
                str(self.type), str(self.instrument), str(self.units),
                str(self.order_type), str(self.side)
            )

    def __repr__(self) -> str:
        return str(self)


class FillEvent(Event):
    def __init__(self, instrument: Pair, units: int, price: Decimal, side: str,
            status: str):
        self.type = EventType('FILL')
        self.instrument: Pair = instrument
        self.units = units
        self.price = price
        self.side = side
        self.status = status

    def __str__(self) -> str:
        return ("Type: %s, Instrument: %s, Units: %s, price: %s, Side: %s" +
            ", Status: %s") % (
                str(self.type), str(self.instrument), str(self.units),
                str(self.price), str(self.side), str(self.status)
        )

    def __repr__(self) -> str:
        return str(self)
