from typing import NewType
from typing_extensions import TypedDict
from decimal import Decimal
import pandas as pd


Pair = NewType('Pair', str)

EventType = NewType('EventType', str)


class Price(TypedDict):
    """Price type defines the type of currency prices as of the
    specified timestamp
    """
    bid: Decimal
    ask: Decimal
    time: pd.Timestamp
