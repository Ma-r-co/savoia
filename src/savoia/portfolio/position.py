from decimal import Decimal
from savoia.config.decimal_config import initializeDecimalContext, DECIMAL_PLACES
from savoia.feed.price import PriceHandler
from savoia.types.types import Pair


class Position():
    home_currency: str
    position_type: str
    currency_pair: Pair
    units: int
    ticker: PriceHandler
    profit_base: Decimal
    profit_perc: Decimal
    base_currency: str
    quote_currency: str
    quote_home_currency_pair: Pair

    def __init__(
        self, home_currency: str, position_type: str,
        currency_pair: Pair, units: int, ticker: PriceHandler
    ) -> None:
        self.home_currency = home_currency
        self.position_type = position_type
        self.currency_pair = currency_pair
        self.units = units
        self.ticker = ticker
        self._set_up_currencies()
        self.profit_base = self._calculate_profit_base()
        self.profit_perc = self._calculate_profit_perc()
        initializeDecimalContext()

    def _set_up_currencies(self) -> None:
        self.base_currency = self.currency_pair[:3]
        self.quote_currency = self.currency_pair[3:]
        if self.quote_currency == self.home_currency:
            self.quote_home_currency_pair = self.currency_pair
        else:
            self.quote_home_currency_pair = "%s%s" % \
                (self.quote_currency, self.home_currency)

        ticker_cur = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            self.avg_price = Decimal(str(ticker_cur["ask"]))
            self.cur_price = Decimal(str(ticker_cur["bid"]))
        else:
            self.avg_price = Decimal(str(ticker_cur["bid"]))
            self.cur_price = Decimal(str(ticker_cur["ask"]))

    def _calculate_pips(self) -> Decimal:
        if self.position_type == "long":
            mult = Decimal("1")
        elif self.position_type == "short":
            mult = Decimal("-1")
        else:
            raise ValueError("Expected 'long' or 'short'. position_type = %s" % str(self.position_type))
        pips = (mult * (self.cur_price - self.avg_price)).quantize(DECIMAL_PLACES)
        return pips

    def _calculate_profit_base(self) -> Decimal:
        pips = self._calculate_pips()
        if self.quote_home_currency_pair == self.currency_pair:
            profit = pips * self.units
        else:
            ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
            if self.position_type == "long":
                qh_close = ticker_qh["bid"]
            else:
                qh_close = ticker_qh["ask"]
            profit = pips * qh_close * self.units
        return profit.quantize(DECIMAL_PLACES)

    def _calculate_profit_perc(self) -> Decimal:
        pips = self._calculate_pips()
        return (pips / self.avg_price * Decimal("100.00")).quantize(DECIMAL_PLACES)

    def update_position_price(self) -> None:
        ticker_cur = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            self.cur_price = Decimal(str(ticker_cur["bid"]))
        else:
            self.cur_price = Decimal(str(ticker_cur["ask"]))
        self.profit_base = self._calculate_profit_base()
        self.profit_perc = self._calculate_profit_perc()

    def add_units(self, units: int) -> None:
        cp = self.ticker.prices[self.currency_pair]
        if self.position_type == "long":
            add_price = cp["ask"]
        else:
            add_price = cp["bid"]
        new_total_units = self.units + units
        new_total_cost = self.avg_price * self.units + add_price * units
        self.avg_price = (new_total_cost / new_total_units).quantize(DECIMAL_PLACES)
        self.units = new_total_units
        self.update_position_price()

    def remove_units(self, units: int) -> Decimal:
        self.units -= units
        self.update_position_price()
        if self.quote_home_currency_pair == self.currency_pair:
            pnl = self._calculate_pips() * units
        else:
            ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
            if self.position_type == "long":
                qh_close = ticker_qh["bid"]
            else:
                qh_close = ticker_qh["ask"]
            pnl = self._calculate_pips() * qh_close * units
        return pnl.quantize(Decimal("0.01"))

    def close_position(self) -> Decimal:
        if self.quote_home_currency_pair == self.currency_pair:
            pnl = self._calculate_pips() * self.units
        else:
            ticker_qh = self.ticker.prices[self.quote_home_currency_pair]
            if self.position_type == "long":
                qh_close = ticker_qh["bid"]
            else:
                qh_close = ticker_qh["ask"]
            pnl = self._calculate_pips() * qh_close * self.units
        return pnl.quantize(Decimal("0.01"))
