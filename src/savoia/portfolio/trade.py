from decimal import Decimal
from savoia.config.decimal_config import DECIMAL_PLACES

from typing import Tuple


class Trade():
    exp_price: Decimal
    units: Decimal
    trade_type: str
    order_id: int

    def __init__(self, exp_price: Decimal, units: Decimal, trade_type: str,
            order_id: int) -> None:
        self.exp_price = exp_price
        self.units = units
        self.trade_type = trade_type
        self.order_id = order_id
    
    def fill_trade(self, exec_price: Decimal) -> Tuple[Decimal, Decimal]:
        '''calculates deviations of balance and PnL which have been tentatively
        calculated based on prices at the timing of order placement.
        These values are quoted in quote currency of the pair.
        '''
        _delta_balance: Decimal
        _delta_upl: Decimal
        if self.trade_type == 'entry':
            _delta_balance = Decimal('0')
            _delta_upl = (self.exp_price - exec_price) * self.units
        elif self.trade_type == 'exit':
            _delta_balance = (self.exp_price - exec_price) * self.units
            _delta_upl = Decimal('0')
        else:
            raise Exception('Unexpected trade_type: %s' % self.trade_type)
        return (_delta_balance.quantize(DECIMAL_PLACES),
                _delta_upl.quantize(DECIMAL_PLACES))

    def cancel_trade(self) -> Tuple[Decimal, Decimal]:
        '''TODO'''
        pass
