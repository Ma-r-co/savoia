from savoia.portfolio.position import Position
# from savoia.portfolio.trade import Trade
from savoia.datafeed.ticker import Ticker
from savoia.types.types import Pair

from decimal import Decimal
import pytest


# class TickerMock(Ticker):
#     """
#     A mock object that allows a representation of the
#     ticker/pricing handler.
#     """

#     def __init__(self) -> None:
#         self.pairs = ["GBPUSD", "EURUSD"]
#         self.prices = {
#             "GBPUSD": {"bid": Decimal("1.50328"), "ask": Decimal("1.50349")},
#             "USDJPY": {"bid": Decimal("110.774"), "ask": Decimal("110.863")},
#         }


@pytest.fixture(scope='function')
def TickerMock() -> Ticker:
    _pairs = ["GBPUSD", "EURUSD", "USDJPY"]
    _prices = {
        "GBPUSD": {"bid": Decimal("1.30328"), "ask": Decimal("1.50349")},
        "USDJPY": {"bid": Decimal("105.774"), "ask": Decimal("110.863")},
    }
    tm = Ticker(_pairs)
    # Create decimalaised prices for trade pair
    for pair, price in _prices.items():
        _bid, _ask = price['bid'], price['ask']
        tm.prices[pair]["bid"] = _bid
        tm.prices[pair]["ask"] = _ask
        # Create decimalised prices for inverted pair
        inv_pair, inv_bid, inv_ask = tm.invert_prices(pair, _bid, _ask)
        tm.prices[inv_pair]["bid"] = inv_bid
        tm.prices[inv_pair]["ask"] = inv_ask
    return tm


@pytest.mark.parametrize('home_currency, pair',
                        [('JPY', 'GBPUSD'),
                         ('JPY', 'USDJPY')])
def test_init(home_currency: str, pair: Pair, TickerMock: Ticker) -> None:
    ps = Position(home_currency, pair, TickerMock)
    assert ps.home_currency == home_currency
    assert ps.pair == pair
    assert ps.ticker == TickerMock
    assert ps.units == Decimal('0')
    assert ps.upl == Decimal('0')
    assert ps.price_cur == TickerMock.prices[pair]
    assert ps.price_cur_qh == TickerMock.prices['USDJPY']


@pytest.mark.parametrize('home_currency, pair, price_side',
                        [('JPY', 'GBPUSD', 'ask'),
                         ('JPY', 'GBPUSD', 'bid'),
                         ('JPY', 'USDJPY', 'ask'),
                         ('JPY', 'USDJPY', 'bid')])
def test_get_qh_factor(home_currency: str, pair: Pair, price_side: str,
        TickerMock: Ticker) -> None:
    ps = Position(home_currency, pair, TickerMock)
    if ps.pair == 'GBPUSD':
        assert ps._get_qh_factor() == \
            TickerMock.prices['USDJPY']['bid']
    else:
        assert ps._get_qh_factor() == Decimal('1')


# ================================================================
# _entry_trade()
# ================================================================
data1 = [
    ('JPY', 'GBPUSD', '1.60328', '1200', '0', '-360'),
    ('JPY', 'GBPUSD', '1.40349', '-200', '0', '-20'),
    ('JPY', 'USDJPY', '91.7740', '0.80', '0', '11.2'),
    ('JPY', 'USDJPY', '113.063', '-0.5', '0', '1.1')
]


@pytest.mark.parametrize('home_currency, pair, exec_price, units,' +
                         '_delta_balance, _delta_upl', data1)
def test_entry_trade(home_currency: str, pair: Pair, exec_price: str,
        units: str, _delta_balance: str, _delta_upl: str, TickerMock: Ticker) \
        -> None:
    ps = Position(home_currency, pair, TickerMock)
    first, second = ps._entry_trade(Decimal(exec_price), Decimal(units))
    assert first == Decimal(_delta_balance)
    assert second == Decimal(_delta_upl)


# ================================================================
# _exit_trade()
# ================================================================
data2 = [
    ('JPY', 'GBPUSD', '1.60328', '1200', '1.7', '-200', '19.344', '60'),
    ('JPY', 'GBPUSD', '1.40349', '-200', '1.20349', '200', '40', '20'),
    ('JPY', 'USDJPY', '91.7740', '0.80', '81.774', '-0.8', '-8', '-11.2'),
    ('JPY', 'USDJPY', '113.063', '-0.5', '115.063', '0.3', '-0.6', '-0.66')
]


@pytest.mark.parametrize('home_currency, pair, exec_price, units,' +
                         'exit_price, exit_units,' +
                         '_delta_balance, _delta_upl', data2)
def test_exit_trade(home_currency: str, pair: Pair, exec_price: str,
        units: str, exit_price: str, exit_units: str,
        _delta_balance: str, _delta_upl: str, TickerMock: Ticker) \
        -> None:
    ps = Position(home_currency, pair, TickerMock)
    balance, ps.upl = ps._entry_trade(Decimal(exec_price), Decimal(units))
    ps.units = Decimal(units)
    ps.avg_price = Decimal(exec_price)

    first, second = ps._exit_trade(Decimal(exit_price), Decimal(exit_units))
    assert first == Decimal(_delta_balance)
    assert second == Decimal(_delta_upl)


# ================================================================
# reflect_filled_order()
# ================================================================

# pair, home_currency, exp_price, units, exp_delta_balance_qh
# exp_delta_upl_qh, exp_avg_price, exp_upl, exp_unit
data3 = [
    ('GBPUSD', 'JPY', '1.60328', '1200', '0', '-38078.64',
    '1.60328', '-360', '1200'),
    ('GBPUSD', 'JPY', '1.40349', '-200', '0', '-2115.48',
    '1.40349', '-20', '-200'),
    ('USDJPY', 'JPY', '91.774', '0.8', '0', '11.2',
    '91.774', '11.2', '0.8'),
    ('USDJPY', 'JPY', '113.063', '-0.5', '0', '1.1',
    '113.063', '1.1', '-0.5')
]


@pytest.mark.parametrize('pair, home_currency, exp_price, units,' +
                    'exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price,' +
                    'exp_upl, exp_units', data3)
def test_reflect_filled_order_init(
        pair: Pair, home_currency: str, exp_price: str, units: str,
        exp_delta_balance_qh: str, exp_delta_upl_qh: str,
        exp_avg_price: str, exp_upl: str, exp_units: str, TickerMock: Ticker) \
        -> None:

    ps = Position(home_currency, pair, TickerMock)
    _delta_balance_qh, _delta_upl_qh = ps.reflect_filled_order(
        Decimal(units), Decimal(exp_price))
    
    assert _delta_balance_qh == Decimal(exp_delta_balance_qh)
    assert _delta_upl_qh == Decimal(exp_delta_upl_qh)
    assert ps.avg_price == Decimal(exp_avg_price)
    assert ps.upl == Decimal(exp_upl)
    assert ps.units == Decimal(exp_units)


# pair, home_currency, exp_price, units, exit_price, exit_units,
# exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price, exp_upl, exp_units
data4 = [
    ('GBPUSD', 'JPY', '1.60328', '1200', '1.7', '-200',
     '2046.092256', '6346.44', '1.60328', '-300.0 ', '1000'),
    ('GBPUSD', 'JPY', '1.40349', '-200', '1.20349', '200',
    '4230.96', '2115.48', '0', '0', '0'),
    ('USDJPY', 'JPY', '91.774', '0.8', '81.774', '-0.8',
     '-8', '-11.2', '0', '0.0', '0'),
    ('USDJPY', 'JPY', '113.063', '-0.5', '115.063', '0.3',
    '-0.6', '-0.66', '113.063', '0.440', '-0.2')
]


@pytest.mark.parametrize('pair, home_currency, exp_price, units,' +
                    'exit_price, exit_units,' +
                    'exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price,' +
                    'exp_upl, exp_units', data4)
def test_reflect_filled_order_exit(
        pair: Pair, home_currency: str, exp_price: str, units: str,
        exit_price: str, exit_units: str,
        exp_delta_balance_qh: str, exp_delta_upl_qh: str,
        exp_avg_price: str, exp_upl: str, exp_units: str, TickerMock: Ticker) \
        -> None:

    ps = Position(home_currency, pair, TickerMock)
    ps.reflect_filled_order(Decimal(units), Decimal(exp_price))
    _ret = ps.reflect_filled_order(Decimal(exit_units), Decimal(exit_price))
    
    assert _ret[0] == Decimal(exp_delta_balance_qh)
    assert _ret[1] == Decimal(exp_delta_upl_qh)
    assert ps.avg_price == Decimal(exp_avg_price)
    assert ps.upl == Decimal(exp_upl)
    assert ps.units == Decimal(exp_units)


# pair, home_currency, exp_price, units, order_id, exit_price, exit_units,
# exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price, exp_upl, exp_units
data5 = [
    ('GBPUSD', 'JPY', '1.60328', '1200', '1.7', '-1400',
     '12276.5535360', '42235.7697480', '1.7', '39.3020000', '-200'),
    ('USDJPY', 'JPY', '113.063', '-0.5', '115.063', '1.7',
    '-1', '-12.24680', '115.063', '-11.14680 ', '1.2')
]


@pytest.mark.parametrize('pair, home_currency, exp_price, units,' +
                    'exit_price, exit_units,' +
                    'exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price,' +
                    'exp_upl, exp_units', data5)
def test_reflect_filled_order_exit_entry(
        pair: Pair, home_currency: str, exp_price: str, units: str,
        exit_price: str, exit_units: str,
        exp_delta_balance_qh: str, exp_delta_upl_qh: str,
        exp_avg_price: str, exp_upl: str, exp_units: str, TickerMock: Ticker) \
        -> None:

    ps = Position(home_currency, pair, TickerMock)
    ps.reflect_filled_order(Decimal(units), Decimal(exp_price))
    _ret = ps.reflect_filled_order(Decimal(exit_units), Decimal(exit_price))
    
    assert _ret[0] == Decimal(exp_delta_balance_qh)
    assert _ret[1] == Decimal(exp_delta_upl_qh)
    assert ps.avg_price == Decimal(exp_avg_price)
    assert ps.upl == Decimal(exp_upl)
    assert ps.units == Decimal(exp_units)


# ================================================================
# update_position_price()
# ================================================================
@pytest.fixture(scope='function')
def TickerMock2() -> Ticker:
    _pairs = ["GBPUSD", "EURUSD", "USDJPY"]
    _prices = {
        "GBPUSD": {"bid": Decimal("1.2541"), "ask": Decimal("1.2543")},
        "USDJPY": {"bid": Decimal("107.25"), "ask": Decimal("107.80")},
    }
    tm = Ticker(_pairs)
    # Create decimalaised prices for trade pair
    for pair, price in _prices.items():
        _bid, _ask = price['bid'], price['ask']
        tm.prices[pair]["bid"] = _bid
        tm.prices[pair]["ask"] = _ask
        # Create decimalised prices for inverted pair
        inv_pair, inv_bid, inv_ask = tm.invert_prices(pair, _bid, _ask)
        tm.prices[inv_pair]["bid"] = inv_bid
        tm.prices[inv_pair]["ask"] = inv_ask
    return tm


data6 = [
    ('JPY', 'GBPUSD', '1.60328', '1200', '-419.016', '-44939.466'),
    ('JPY', 'GBPUSD', '1.40349', '-200', '29.838', '3200.1255'),
    ('JPY', 'USDJPY', '91.7740', '0.80', '12.3808', '12.3808'),
    ('JPY', 'USDJPY', '113.063', '-0.5', '2.6315', '2.6315')
]


@pytest.mark.parametrize('home_currency, pair, exec_price, units,' +
                         'exp_upl, exp_upl_qh', data6)
def test_update_position_price(home_currency: str, pair: Pair, exec_price: str,
        units: str, exp_upl: str, exp_upl_qh: str,
        TickerMock: Ticker, TickerMock2: Ticker) \
        -> None:
    ps = Position(home_currency, pair, TickerMock)
    ps.reflect_filled_order(Decimal(units), Decimal(exec_price))
    
    ps.ticker = TickerMock2
    ps._set_up_currency_pairs()
    _upl_qh = ps.update_position_price()

    assert _upl_qh == Decimal(exp_upl_qh)
    assert ps.upl == Decimal(exp_upl)
