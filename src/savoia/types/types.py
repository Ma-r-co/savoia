from typing import NewType


Pair = NewType('Pair', str)

EventType = NewType('EventType', str)


# class Price(TypedDict):
#     """Price type defines the type of currency prices as of the
#     specified timestamp
#     """
#     bid: Decimal
#     ask: Decimal
#     time: pd.Timestamp
