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
    # base_currency: str
    # quote_currency: str
    # position_type: str
    units: Decimal
    ticker: Ticker
    price_cur: Price
    price_cur_qh: Price
    upl: Decimal
    trades: List[Trade]
    avg_price: Decimal

    def __init__(
        self, home_currency: str, pair: Pair, ticker: Ticker,
        units: Decimal = Decimal('0')
    ) -> None:
        self.home_currency = home_currency
        # self.position_type = position_type
        self.pair = pair
        self.ticker = ticker
        self._set_up_currency_pairs()
        self.units = units
        self.upl = Decimal('0')
        self.trades = []

    # def get_upl_qh(self) -> Decimal:
    #     '''Returns upl quoted in home currency'''
    #     _price_side: str = 'bid' if self.units >= 0 else 'ask'
    #     return self.upl * self._get_qh_factor(_price_side)

    def reserve_trades(self, units: Decimal, exp_price: Decimal,
            order_id: int) -> Tuple[Decimal, Decimal]:
        '''Creates Trade instance and add it to self.trades.
        In addition, Calculates and Returns tentative impacts on both balance
        and upl.
        '''
        _price_side: str
        _delta_balance: Decimal = Decimal('0')
        _delta_upl: Decimal = Decimal('0')
        _delta_balance_qh: Decimal
        _delta_upl_qh: Decimal

        if units * self.units >= 0:  # if same sign...
            _i, _j = self._entry_trade(exp_price, units, order_id)
            _delta_balance += _i
            _delta_upl += _j
        else:  # if opposite sign...
            if abs(units) <= abs(self.units):
                _i, _j = self._exit_trade(exp_price, units, order_id)
                _delta_balance += _i
                _delta_upl += _j
            else:
                _i, _j = self._exit_trade(exp_price, -self.units, order_id)
                _delta_balance += _i
                _delta_upl += _j
                _i, _j = self._entry_trade(
                    exp_price, units + self.units, order_id
                )
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

    def _entry_trade(self, exp_price: Decimal, units: Decimal, order_id: int) \
            -> Tuple[Decimal, Decimal]:
        '''Creates Trade instance of 'entry' and add it to self.trades[].
        In addition, Calculates and Returns tentative impacts on both balance
        and upl.
        '''
        _delta_balance: Decimal
        _delta_upl: Decimal

        self.trades.append(Trade(exp_price, units, 'entry', order_id))
        _delta_balance = Decimal('0')
        _price_side = 'bid' if units >= 0 else 'ask'
        _delta_upl = (self.price_cur[_price_side] - exp_price) * units
        return _delta_balance, _delta_upl

    def _exit_trade(self, exp_price: Decimal, units: Decimal, order_id: int) \
            -> Tuple[Decimal, Decimal]:
        '''Creates Trade instance of 'exit' and add it to self.trades[].
        In addition, Calculates and Returns tentative impacts on both balance
        and upl.
        '''
        _delta_balance: Decimal
        _delta_upl: Decimal

        self.trades.append(Trade(exp_price, units, 'exit', order_id))
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

    def settle_open_trades(self, order_id: int, status: str,
            exec_price: Decimal) -> Tuple[Decimal, Decimal]:
        '''Closes open trades that match order_id provided, and calculates
        deviations from tentative impacts on balance and upl, which have been
        calculated upon reserve_trades().
        In additino, Trade instance is to be removed in the end.
        '''
        _price_side: str
        _delta_balance: Decimal = Decimal('0')
        _delta_upl: Decimal = Decimal('0')
        _i: int
        _t: Trade
        _cnt: int = 0
        for _i, _t in enumerate(self.trades):
            if _t.order_id == order_id:
                _price_side = 'bid' if _t.units >= 0 else 'ask'
                if _t.status == 'filled':
                    _j, _k = _t.fill_trade(exec_price)
                    _delta_balance += _j
                    _delta_upl += _k
                elif _t.status == 'canceled':
                    _j, _k = _t.cancel_trade()
                    _delta_balance += _j
                    _delta_upl += _k
                else:
                    raise Exception('Unexpected order status: %s' % status)
                self.trades.pop(_i)
                _cnt += 1
        if _cnt > 0:
            _delta_balance *= self._get_qh_factor()
            _delta_upl *= self._get_qh_factor()
            self.upl += _delta_upl
            _price_side = 'bid' if self.units >= 0 else 'ask'
            self.avg_price = self.price_cur(_price_side) - (self.upl /
                self._get_qh_factor()) / self.units
            return _delta_balance, _delta_upl
        else:
            raise Exception('No such a order with order_id: %s' % order_id)

    def update_position_price(self) -> Decimal:
        _price_side: str
        _delta_upl: Decimal
        
        _price_side = 'bid' if self.units >= 0 else 'ask'
        _delta_upl = self.upl - (
            self.price_cur[_price_side] - self.avg_price
        ) * self.units * self._get_qh_factor()
        self.upl += _delta_upl
        return _delta_upl

    # def _calculate_pips(self) -> Decimal:
    #     if self.position_type == "long":
    #         mult = Decimal("1")
    #     elif self.position_type == "short":
    #         mult = Decimal("-1")
    #     else:
    #         raise ValueError("Expected 'long' or 'short'. position_type = %s"
    #             % str(self.position_type))
    #     pips = (mult * (self.cur_price - self.avg_price)).quantize(
    #         DECIMAL_PLACES)
    #     return pips

    # def _calculate_profit_base(self) -> Decimal:
    #     pips = self._calculate_pips()
    #     if self.quote_home_currency_pair == self.pair:
    #         profit = pips * self.units
    #     else:
    #         ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
    #         if self.position_type == "long":
    #             qh_close = ticker_qh["bid"]
    #         else:
    #             qh_close = ticker_qh["ask"]
    #         profit = pips * qh_close * self.units
    #     return profit.quantize(DECIMAL_PLACES)

    # def _calculate_profit_perc(self) -> Decimal:
    #     pips = self._calculate_pips()
    #     return (pips / self.avg_price * Decimal("100.00")).quantize(
    #         DECIMAL_PLACES)

    # def update_position_price(self) -> None:
    #     ticker_cur = self.ticker.prices[self.pair]
    #     if self.position_type == "long":
    #         self.cur_price = Decimal(str(ticker_cur["bid"]))
    #     else:
    #         self.cur_price = Decimal(str(ticker_cur["ask"]))
    #     self.profit_base = self._calculate_profit_base()
    #     self.profit_perc = self._calculate_profit_perc()

    # def add_units(self, units: int) -> None:
    #     cp = self.ticker.prices[self.pair]
    #     if self.position_type == "long":
    #         add_price = cp["ask"]
    #     else:
    #         add_price = cp["bid"]
    #     new_total_units = self.units + units
    #     new_total_cost = self.avg_price * self.units + add_price * units
    #     self.avg_price = (new_total_cost / new_total_units).quantize(
    #         DECIMAL_PLACES)
    #     self.units = new_total_units
    #     self.update_position_price()

    # def remove_units(self, units: int) -> Decimal:
    #     self.units -= units
    #     self.update_position_price()
    #     if self.quote_home_currency_pair == self.pair:
    #         pnl = self._calculate_pips() * units
    #     else:
    #         ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
    #         if self.position_type == "long":
    #             qh_close = ticker_qh["bid"]
    #         else:
    #             qh_close = ticker_qh["ask"]
    #         pnl = self._calculate_pips() * qh_close * units
    #     return pnl.quantize(Decimal("0.01"))

    # def close_position(self) -> Decimal:
    #     if self.quote_home_currency_pair == self.pair:
    #         pnl = self._calculate_pips() * self.units
    #     else:
    #         ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
    #         if self.position_type == "long":
    #             qh_close = ticker_qh["bid"]
    #         else:
    #             qh_close = ticker_qh["ask"]
    #         pnl = self._calculate_pips() * qh_close * self.units
    #     return pnl.quantize(Decimal("0.01"))
