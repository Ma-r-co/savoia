from decimal import Decimal
import pandas as pd
from typing import NewType
from typing_extensions import TypedDict
from enum import IntFlag

Pair = NewType('Pair', str)
EventType = NewType('EventType', str)


class Price(TypedDict):
    """Price type defines the type of currency prices as of the
    specified timestamp
    """
    bid: Decimal
    ask: Decimal
    time: pd.Timestamp


class Side(IntFlag):
    LONG = 0
    SHORT = 1


class TradeType(IntFlag):
    ENTRY = 0
    EXIT = 1
