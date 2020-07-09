import pytest
from savoia.ticker.ticker import Ticker
from savoia.event.event import TickEvent
from decimal import Decimal
import pandas as pd


# ---------------------------------------------------------------
# Ticker
# ---------------------------------------------------------------
def test_set_up_prices_dict() -> None:
    """
    _set_up_prices_dict should return both prices dict and
    inv-prices dict
    """
    pairs = ['USDJPY', 'GBPUSD']
    ticker = Ticker(pairs)
    prices_dict = ticker._set_up_prices_dict()
    assert sorted(list(prices_dict.keys())) == sorted(
        ["USDJPY", "JPYUSD", "GBPUSD", "USDGBP"])
    for v in prices_dict.values():
        assert v == {'bid': Decimal(0), 'ask': Decimal(0),
                    'time': pd.Timestamp(0)}


@pytest.mark.parametrize('pair, bid, ask, return_pair, return_bid, return_ask',
                    [("USDJPY", Decimal('106.87'), Decimal('106.90'),
                    "JPYUSD", Decimal('0.00935454'), Decimal('0.00935716')),
                    ("EURGBP", Decimal('0.90473'), Decimal('0.90561'),
                    "GBPEUR", Decimal('1.10422809'), Decimal('1.10530213'))])
def test_invert_prices(pair: str,
        bid: Decimal, ask: Decimal, return_pair: str, return_bid: Decimal,
        return_ask: Decimal) -> None:
    """ invert_prices should return inverted pair, bid and ask prices"""
    pairs = ['USDJPY', 'GBPUSD']
    ticker = Ticker(pairs)
    inv_pair, inv_bid, inv_ask = ticker.invert_prices(pair, bid, ask)
    assert inv_pair == return_pair
    assert inv_bid == return_bid
    assert inv_ask == return_ask


def test_update_ticker() -> None:
    pairs = ['GBPUSD', 'USDJPY']
    time = pd.Timestamp('2020-07-09 12:23:10')
    ticker = Ticker(pairs)

    # pair, ask, bid, GBPUSD(ask, bid), USDGBP(ask, bid),
    # USDJPY(ask, bid), JPYUSD(ask, bid)
    tick1 = ['GBPUSD', '1.50349', '1.30328', '1.50349', '1.30328',
            '0.76729483', '0.66511916', '0', '0', '0', '0']
    tick2 = ['USDJPY', '110.863', '105.774', '1.50349', '1.30328',
            '0.76729483', '0.66511916', '110.863', '105.774',
            '0.00945412', '0.00902014']
    tick3 = ['GBPUSD', '1.2543', '1.2541', '1.2543', '1.2541',
            '0.79738458', '0.79725743', '110.863', '105.774',
            '0.00945412', '0.00902014']
    tick4 = ['USDJPY', '107.8', '107.25', '1.2543', '1.2541',
            '0.79738458', '0.79725743', '107.8', '107.25',
            '0.00932401', '0.00927644']
    tick = [tick1, tick2, tick3, tick4]

    for t in tick:
        event = TickEvent(t[0], time, Decimal(t[2]), Decimal(t[1]))
        ticker.update_ticker(event)
        result = []
        for p in ['GBPUSD', 'USDGBP', 'USDJPY', 'JPYUSD']:
            for q in ['ask', 'bid']:
                result.append(ticker.prices[p][q])
        assert result == list(map(Decimal, t[3:]))
