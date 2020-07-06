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
    assert ps.trades == []
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
@pytest.mark.parametrize('home_currency, pair, exp_price, units,' +
                         'order_id, _delta_balance, _delta_upl',
                        [('JPY', 'GBPUSD', Decimal('1.60328'), Decimal('1200'),
                          9999, Decimal('0'), Decimal('-360')),
                         ('JPY', 'GBPUSD', Decimal('1.40349'), Decimal('-200'),
                          9999, Decimal('0'), Decimal('-20')),
                         ('JPY', 'USDJPY', Decimal('91.774'), Decimal('0.8'),
                          9999, Decimal('0'), Decimal('11.2')),
                         ('JPY', 'USDJPY', Decimal('113.063'), Decimal('-0.5'),
                          9999, Decimal('0'), Decimal('1.1'))])
def test_entry_trade(home_currency: str, pair: Pair, exp_price: Decimal,
        units: Decimal, order_id: int, _delta_balance: Decimal,
        _delta_upl: Decimal, TickerMock: Ticker) -> None:
    ps = Position(home_currency, pair, TickerMock)
    first, second = ps._entry_trade(exp_price, units, order_id)
    assert first == _delta_balance
    assert second == _delta_upl

    assert ps.trades[0].exp_price == exp_price
    assert ps.trades[-1].units == units
    assert ps.trades[0].trade_type == 'entry'
    assert ps.trades[-1].order_id == order_id


# ================================================================
# _exit_trade()
# ================================================================
@pytest.mark.parametrize('home_currency, pair, exp_price, units,' +
                         'order_id, exit_price, exit_units,' +
                         '_delta_balance, _delta_upl',
                        [('JPY', 'GBPUSD', Decimal('1.60328'), Decimal('1200'),
                          9999, Decimal('1.7'), Decimal('-200'),
                          Decimal('19.344'), Decimal('60')),
                         ('JPY', 'GBPUSD', Decimal('1.40349'), Decimal('-200'),
                          9999, Decimal('1.20349'), Decimal('200'),
                          Decimal('40.0'), Decimal('20.0')),
                         ('JPY', 'USDJPY', Decimal('91.774'), Decimal('0.8'),
                          9999, Decimal('81.774'), Decimal('-0.8'),
                          Decimal('-8.000'), Decimal('-11.2')),
                         ('JPY', 'USDJPY', Decimal('113.063'), Decimal('-0.5'),
                          9999, Decimal('115.063'), Decimal('0.3'),
                          Decimal('-0.6'), Decimal('-0.66'))])
def test_exit_trade(home_currency: str, pair: Pair, exp_price: Decimal,
        units: Decimal, order_id: int, exit_price: Decimal, exit_units: Decimal,
        _delta_balance: Decimal, _delta_upl: Decimal, TickerMock: Ticker) \
        -> None:
    ps = Position(home_currency, pair, TickerMock)
    balance, ps.upl = ps._entry_trade(exp_price, units, order_id)
    ps.units = units
    ps.avg_price = exp_price

    first, second = ps._exit_trade(exit_price, exit_units, order_id - 1)
    assert first == _delta_balance
    assert second == _delta_upl

    assert ps.trades[1].exp_price == exit_price
    assert ps.trades[-1].units == exit_units
    assert ps.trades[1].trade_type == 'exit'
    assert ps.trades[-1].order_id == order_id - 1


# ================================================================
# reserve_trade()
# ================================================================

# pair, home_currency, exp_price, units, order_id, exp_delta_balance_qh
# exp_delta_upl_qh, exp_avg_price, exp_upl, exp_unit
data1 = [
    ('GBPUSD', 'JPY', '1.60328', '1200', 9999, '0', '-38078.64',
    '1.60328', '-360', '1200'),
    ('GBPUSD', 'JPY', '1.40349', '-200', 8888, '0', '-2115.48',
    '1.40349', '-20', '-200'),
    ('USDJPY', 'JPY', '91.774', '0.8', 7777, '0', '11.2',
    '91.774', '11.2', '0.8'),
    ('USDJPY', 'JPY', '113.063', '-0.5', 6666, '0', '1.1',
    '113.063', '1.1', '-0.5')
]


@pytest.mark.parametrize('pair, home_currency, exp_price, units, order_id,' +
                    'exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price,' +
                    'exp_upl, exp_units', data1)
def test_reserve_trade_init(
        pair: Pair, home_currency: str, exp_price: str, units: str,
        order_id: int, exp_delta_balance_qh: str, exp_delta_upl_qh: str,
        exp_avg_price: str, exp_upl: str, exp_units: str, TickerMock: Ticker) \
        -> None:
    _exp_price = Decimal(exp_price)
    _units = Decimal(units)
    _exp_delta_balance_qh = Decimal(exp_delta_balance_qh)
    _exp_delta_upl_qh = Decimal(exp_delta_upl_qh)
    _exp_avg_price = Decimal(exp_avg_price)
    _exp_upl = Decimal(exp_upl)
    _exp_units = Decimal(exp_units)

    ps = Position(home_currency, pair, TickerMock)
    _delta_balance_qh, _delta_upl_qh = ps.reserve_trades(
        _units, _exp_price, order_id)
    
    assert _delta_balance_qh == _exp_delta_balance_qh
    assert _delta_upl_qh == _exp_delta_upl_qh
    assert ps.avg_price == _exp_avg_price
    assert ps.upl == _exp_upl
    assert ps.units == _exp_units
    assert ps.trades[0].exp_price == _exp_price
    assert ps.trades[-1].units == _exp_units
    assert ps.trades[0].trade_type == 'entry'
    assert ps.trades[-1].order_id == order_id


# pair, home_currency, exp_price, units, order_id, exit_price, exit_units,
# exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price, exp_upl, exp_units
data2 = [
    ('GBPUSD', 'JPY', '1.60328', '1200', 9999, '1.7', '-200',
     '2046.092256', '6346.44', '1.60328', '-300.0 ', '1000'),
    ('GBPUSD', 'JPY', '1.40349', '-200', 8888, '1.20349', '200',
    '4230.96', '2115.48', '0', '0', '0'),
    ('USDJPY', 'JPY', '91.774', '0.8', 7777, '81.774', '-0.8',
     '-8', '-11.2', '0', '0.0', '0'),
    ('USDJPY', 'JPY', '113.063', '-0.5', 6666, '115.063', '0.3',
    '-0.6', '-0.66', '113.063', '0.440', '-0.2')
]


@pytest.mark.parametrize('pair, home_currency, exp_price, units, order_id,' +
                    'exit_price, exit_units,' +
                    'exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price,' +
                    'exp_upl, exp_units', data2)
def test_reserve_trade_exit(
        pair: Pair, home_currency: str, exp_price: str, units: str,
        order_id: int, exit_price: str, exit_units: str,
        exp_delta_balance_qh: str, exp_delta_upl_qh: str,
        exp_avg_price: str, exp_upl: str, exp_units: str, TickerMock: Ticker) \
        -> None:
    _exp_price = Decimal(exp_price)
    _units = Decimal(units)
    _exit_price = Decimal(exit_price)
    _exit_units = Decimal(exit_units)
    _exp_delta_balance_qh = Decimal(exp_delta_balance_qh)
    _exp_delta_upl_qh = Decimal(exp_delta_upl_qh)
    _exp_avg_price = Decimal(exp_avg_price)
    _exp_upl = Decimal(exp_upl)
    _exp_units = Decimal(exp_units)

    ps = Position(home_currency, pair, TickerMock)
    ps.reserve_trades(_units, _exp_price, order_id)
    _delta_balance_qh, _delta_upl_qh = ps.reserve_trades(
        _exit_units, _exit_price, order_id + 1)
    
    assert _delta_balance_qh == _exp_delta_balance_qh
    assert _delta_upl_qh == _exp_delta_upl_qh
    assert ps.avg_price == _exp_avg_price
    assert ps.upl == _exp_upl
    assert ps.units == _exp_units
    assert ps.trades[1].exp_price == _exit_price
    assert ps.trades[-1].units == _exit_units
    assert ps.trades[1].trade_type == 'exit'
    assert ps.trades[-1].order_id == order_id + 1


# pair, home_currency, exp_price, units, order_id, exit_price, exit_units,
# exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price, exp_upl, exp_units
data3 = [
    ('GBPUSD', 'JPY', '1.60328', '1200', 9999, '1.7', '-1400',
     '12276.5535360', '42235.7697480', '1.7', '39.3020000', '-200'),
    ('USDJPY', 'JPY', '113.063', '-0.5', 6666, '115.063', '1.7',
    '-1', '-12.24680', '115.063', '-11.14680 ', '1.2')
]


@pytest.mark.parametrize('pair, home_currency, exp_price, units, order_id,' +
                    'exit_price, exit_units,' +
                    'exp_delta_balance_qh, exp_delta_upl_qh, exp_avg_price,' +
                    'exp_upl, exp_units', data3)
def test_reserve_trade_exit_entry(
        pair: Pair, home_currency: str, exp_price: str, units: str,
        order_id: int, exit_price: str, exit_units: str,
        exp_delta_balance_qh: str, exp_delta_upl_qh: str,
        exp_avg_price: str, exp_upl: str, exp_units: str, TickerMock: Ticker) \
        -> None:
    _exp_price = Decimal(exp_price)
    _units = Decimal(units)
    _exit_price = Decimal(exit_price)
    _exit_units = Decimal(exit_units)
    _exp_delta_balance_qh = Decimal(exp_delta_balance_qh)
    _exp_delta_upl_qh = Decimal(exp_delta_upl_qh)
    _exp_avg_price = Decimal(exp_avg_price)
    _exp_upl = Decimal(exp_upl)
    _exp_units = Decimal(exp_units)

    ps = Position(home_currency, pair, TickerMock)
    ps.reserve_trades(_units, _exp_price, order_id)
    _delta_balance_qh, _delta_upl_qh = ps.reserve_trades(
        _exit_units, _exit_price, order_id + 1)
    
    assert _delta_balance_qh == _exp_delta_balance_qh
    assert _delta_upl_qh == _exp_delta_upl_qh
    assert ps.avg_price == _exp_avg_price
    assert ps.upl == _exp_upl
    assert ps.units == _exp_units
    assert len(ps.trades) == 3
    assert ps.trades[0].trade_type == 'entry'
    assert ps.trades[1].trade_type == 'exit'
    assert ps.trades[2].trade_type == 'entry'
