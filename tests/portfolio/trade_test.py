from savoia.portfolio.trade import Trade
import pytest

from decimal import Decimal


@pytest.mark.parametrize('exp_price, unit, trade_type, order_id',
    [(Decimal('10020'), Decimal('0.21'), 'entry', 1332),
     (Decimal('9972'), Decimal('-0.33'), 'exit', 32)]
)
def test_init_(exp_price: Decimal, unit: Decimal, trade_type: str,
        order_id: int) -> None:
    trade = Trade(exp_price, unit, trade_type, order_id)
    assert trade.exp_price == exp_price
    assert trade.unit == unit
    assert trade.trade_type == trade_type
    assert trade.order_id == order_id


@pytest.mark.parametrize('exp_price, unit, trade_type, order_id, ' +
                        'exec_price, delta_balance, delta_upl',
    [(Decimal('10020'), Decimal('0.21'), 'entry', 1332,
      Decimal('10349'), Decimal('0'), Decimal('-69.09')),
     (Decimal('10020'), Decimal('0.21'), 'entry', 1332,
      Decimal('9405'), Decimal('0'), Decimal('129.15')),
     (Decimal('10020'), Decimal('0.21'), 'exit', 1332,
      Decimal('10349'), Decimal('-69.090'), Decimal('0')),
     (Decimal('10020'), Decimal('0.21'), 'exit', 1332,
      Decimal('9405'), Decimal('129.150'), Decimal('0'))]
)
def test_fill_trade_long(exp_price: Decimal, unit: Decimal, trade_type: str,
        order_id: int, exec_price: Decimal, delta_balance: Decimal,
        delta_upl: Decimal) -> None:
    trade = Trade(exp_price, unit, trade_type, order_id)
    first, second = trade.fill_trade(exec_price)
    assert first == delta_balance
    assert second == delta_upl


@pytest.mark.parametrize('exp_price, unit, trade_type, order_id, ' +
                        'exec_price, delta_balance, delta_upl',
    [(Decimal('10130'), Decimal('-0.43'), 'entry', 1332,
      Decimal('10456'), Decimal('0'), Decimal('140.180')),
     (Decimal('10130'), Decimal('-0.43'), 'entry', 1332,
      Decimal('10021'), Decimal('0'), Decimal('-46.870')),
     (Decimal('10130'), Decimal('-0.43'), 'exit', 1332,
      Decimal('10456'), Decimal('140.180'), Decimal('0')),
     (Decimal('10130'), Decimal('-0.43'), 'exit', 1332,
      Decimal('10021'), Decimal('-46.870'), Decimal('0'))]
)
def test_fill_trade_short(exp_price: Decimal, unit: Decimal, trade_type: str,
        order_id: int, exec_price: Decimal, delta_balance: Decimal,
        delta_upl: Decimal) -> None:
    trade = Trade(exp_price, unit, trade_type, order_id)
    first, second = trade.fill_trade(exec_price)
    assert first == delta_balance
    assert second == delta_upl
