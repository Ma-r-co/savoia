from decimal import Decimal
from savoia.config.decimal_config import DECIMAL_PLACES

import pandas as pd

from savoia.types.types import Pair, Price
from savoia.event.event import TickEvent

from logging import getLogger, Logger
from typing import List, Dict, Tuple


class Ticker(object):
    """
    Ticker is responsible for holding latest prices for each
    currencies.
    """
    logger: Logger
    pairs: List[Pair]
    prices: Dict[Pair, Price]

    def __init__(self, pairs: List[Pair]) -> None:
        """
        Initialises the Ticker
        """
        self.logger = getLogger(__name__)
        self.pairs = pairs
        self.prices = self._set_up_prices_dict()

    def _set_up_prices_dict(self) -> Dict[Pair, Price]:
        prices_dict = dict((Pair(k), v)
                           for k, v in [(p, Price({
                               "bid": Decimal(0),
                               "ask": Decimal(0),
                               "time": pd.Timestamp(0)
                           })) for p in self.pairs])
        inv_prices_dict = dict((Pair(k), v)
                               for k, v in [("%s%s" % (p[3:], p[:3]), Price({
                                   "bid": Decimal(0),
                                   "ask": Decimal(0),
                                   "time": pd.Timestamp(0)
                               })) for p in self.pairs])
        prices_dict.update(inv_prices_dict)
        return prices_dict

    @classmethod
    def invert_prices(cls, pair: Pair, bid: Decimal, ask: Decimal) \
            -> Tuple[Pair, Decimal, Decimal]:
        inv_pair = Pair("%s%s" % (pair[3:], pair[:3]))
        inv_bid = (Decimal("1.0") / ask).quantize(DECIMAL_PLACES)
        inv_ask = (Decimal("1.0") / bid).quantize(DECIMAL_PLACES)
        return inv_pair, inv_bid, inv_ask

    def update_ticker(self, event: TickEvent) -> None:
        '''Updates prices upon TickEvent'''
        _pair: Pair
        _bid: Decimal
        _ask: Decimal
        _time: pd.Timestamp

        if event.type != 'TICK':
            raise Exception(f"Incorrect EventType: {event.type}, " +
                "expected 'TICK' event.")
        else:
            _pair = event.pair
            _bid = event.bid
            _ask = event.ask
            _time = event.time
            self.prices[_pair]['bid'] = _bid
            self.prices[_pair]['ask'] = _ask
            self.prices[_pair]['time'] = _time
            inv_pair, inv_bid, inv_ask = self.invert_prices(_pair, _bid, _ask)
            self.prices[inv_pair]["bid"] = inv_bid
            self.prices[inv_pair]["ask"] = inv_ask
            self.prices[inv_pair]['time'] = _time
