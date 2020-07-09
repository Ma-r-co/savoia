from decimal import Decimal
from savoia.config.decimal_config import DECIMAL_PLACES
from savoia.datafeed.ticker import Ticker
from savoia.portfolio.trade import Trade
from savoia.types.types import Pair, Price

from typing import List, Tuple


class Position():
    pair: Pair
    quote_home_currency_pair: Pair
    home_currency: str
    units: Decimal
    ticker: Ticker
    price_cur: Price
    price_cur_qh: Price
    upl: Decimal
    trades: List[Trade]
    avg_price: Decimal

    def __init__(self, home_currency: str, pair: Pair, ticker: Ticker) -> None:
        self.home_currency = home_currency
        self.pair = pair
        self.ticker = ticker
        self._set_up_currency_pairs()
        self.units = Decimal('0')
        self.upl = Decimal('0')

    def reflect_filled_order(self, units: Decimal, exp_price: Decimal) \
            -> Tuple[Decimal, Decimal]:
        '''Calculates impact on both balance and upl, then returns the values
        quoted with ome currency.
        '''
        _price_side: str
        _delta_balance: Decimal = Decimal('0')
        _delta_upl: Decimal = Decimal('0')
        _delta_balance_qh: Decimal
        _delta_upl_qh: Decimal

        if units * self.units >= 0:  # if same sign...
            _i, _j = self._entry_trade(exp_price, units)
            _delta_balance += _i
            _delta_upl += _j
        else:  # if opposite sign...
            if abs(units) <= abs(self.units):
                _i, _j = self._exit_trade(exp_price, units)
                _delta_balance += _i
                _delta_upl += _j
            else:
                _i, _j = self._exit_trade(exp_price, -self.units)
                _delta_balance += _i
                _delta_upl += _j
                _i, _j = self._entry_trade(exp_price, units + self.units)
                _delta_balance += _i
                _delta_upl += _j
        self.units += units
        self.upl += _delta_upl
        _price_side = 'bid' if self.units >= 0 else 'ask'
        self.avg_price = Decimal('0') if self.units == 0 else \
            (self.price_cur[_price_side] - self.upl /
             self.units).quantize(DECIMAL_PLACES)
        
        _delta_balance_qh = _delta_balance * self._get_qh_factor()
        _delta_upl_qh = _delta_upl * self._get_qh_factor()
        return _delta_balance_qh, _delta_upl_qh

    def _entry_trade(self, exp_price: Decimal, units: Decimal) \
            -> Tuple[Decimal, Decimal]:
        '''Calculates impacts on both balance and upl for 'entry' trade.'''
        _delta_balance: Decimal
        _delta_upl: Decimal

        _delta_balance = Decimal('0')
        _price_side = 'bid' if units >= 0 else 'ask'
        _delta_upl = (self.price_cur[_price_side] - exp_price) * units
        return _delta_balance, _delta_upl

    def _exit_trade(self, exp_price: Decimal, units: Decimal) \
            -> Tuple[Decimal, Decimal]:
        '''Calculates impacts on both balance and upl for 'exit' trade.'''
        _delta_balance: Decimal
        _delta_upl: Decimal

        _delta_balance = -1 * (exp_price - self.avg_price) * units
        _delta_upl = (self.upl * units / (self.units)).quantize(DECIMAL_PLACES)
        return _delta_balance, _delta_upl

    def _get_qh_factor(self) -> Decimal:
        '''Returns factor to convert prices to ones quoted in home currency.
        In case the pair is already quoted in home currency, it just returns
        '1'.
        '''
        if self.quote_home_currency_pair == self.pair:
            return Decimal('1')
        else:
            return self.price_cur_qh['bid']

    def _set_up_currency_pairs(self) -> None:
        '''set up quote_home_currency_pair and cursors for tickers of
        quote_home_currency_pair and pair.
        '''
        _quote_currency: str = self.pair[3:]
        if _quote_currency == self.home_currency:
            self.quote_home_currency_pair = self.pair
        else:
            self.quote_home_currency_pair = "%s%s" % \
                (_quote_currency, self.home_currency)
        self.price_cur = self.ticker.prices[self.pair]
        self.price_cur_qh = self.ticker.prices[self.quote_home_currency_pair]

    # def settle_open_trades(self, order_id: int, status: str,
    #         exec_price: Decimal) -> Tuple[Decimal, Decimal]:
    #     '''Closes open trades that match order_id provided, and calculates
    #     deviations from tentative impacts on balance and upl, which have been
    #     calculated upon reserve_trades().
    #     In additino, Trade instance is to be removed in the end.
    #     '''
    #     _price_side: str
    #     _delta_balance: Decimal = Decimal('0')
    #     _delta_upl: Decimal = Decimal('0')
    #     _i: int
    #     _t: Trade
    #     _cnt: int = 0
    #     for _i, _t in enumerate(self.trades):
    #         if _t.order_id == order_id:
    #             _price_side = 'bid' if _t.units >= 0 else 'ask'
    #             if _t.status == 'filled':
    #                 _j, _k = _t.fill_trade(exec_price)
    #                 _delta_balance += _j
    #                 _delta_upl += _k
    #             # elif _t.status == 'canceled':
    #             #     _j, _k = _t.cancel_trade()
    #             #     _delta_balance += _j
    #             #     _delta_upl += _k
    #             else:
    #                 raise Exception('Unexpected order status: %s' % status)
    #             self.trades.pop(_i)
    #             _cnt += 1
    #     if _cnt > 0:
    #         self.upl += _delta_upl
    #         _price_side = 'bid' if self.units >= 0 else 'ask'
    #         self.avg_price = self.price_cur(_price_side) - self.upl / \
    #           self.units

    #         _delta_balance_qh = _delta_balance * self._get_qh_factor()
    #         _delta_upl_qh = _delta_upl * self._get_qh_factor()
    #         return _delta_balance_qh, _delta_upl_qh
    #     else:
    #         raise Exception('No such a order with order_id: %s' % order_id)

    def update_position_price(self) -> Decimal:
        '''Updates position price with the latest ticker, and returns deviation
        of upl quoted in home currency'''
        _price_side: str
        _updated_upl: Decimal
        _delta_upl: Decimal
        _delta_upl_qh: Decimal

        # if position is square, no need for update.
        if self.units == 0:
            _delta_upl_qh = Decimal('0')
        else:
            _price_side = 'bid' if self.units >= 0 else 'ask'
            _updated_upl = (self.price_cur[_price_side] - self.avg_price) * \
                self.units
            _delta_upl = _updated_upl - self.upl

            self.upl = _updated_upl
            _delta_upl_qh = _delta_upl * self._get_qh_factor()
        return _delta_upl_qh
