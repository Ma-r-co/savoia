from decimal import Decimal
import pandas as pd
from typing import NewType, Optional
from typing_extensions import TypedDict

Pair = NewType('Pair', str)
EventType = NewType('EventType', str)


class Price(TypedDict):
    """Price type defines the type of currency prices as of the
    specified timestamp
    """
    bid: Optional[Decimal]
    ask: Optional[Decimal]
    time: Optional[pd.Timestamp]
