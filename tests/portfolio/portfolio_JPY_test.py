from decimal import Decimal
import unittest

from savoia.portfolio.portfolio import Portfolio
from savoia.event.event import Event
from queue import Queue


class TickerMock(object):
    """
    A mock object that allows a representation of the
    ticker/pricing handler.
    """

    def __init__(self) -> None:
        self.pairs = ["GBPUSD", "EURUSD"]
        self.prices = {
            "GBPUSD": {"bid": Decimal("1.50328"), "ask": Decimal("1.50349")},
            "USDGBP": {"bid": Decimal("0.66512"), "ask": Decimal("0.66521")},
            "USDJPY": {"bid": Decimal("110.774"), "ask": Decimal("110.863")},
            "JPYUSD": {"bid": Decimal("0.00902014"), "ask": Decimal("0.00902739")}
        }


class TestPortfolio(unittest.TestCase):
    def setUp(self) -> None:
        home_currency = "JPY"
        leverage = Decimal("20")
        equity = Decimal("1000000.00")
        risk_per_trade = Decimal("0.02")
        ticker = TickerMock()
        events: 'Queue[Event]' = Queue()
        self.port = Portfolio(
            ticker,
            events,
            home_currency=home_currency,
            leverage=leverage,
            equity=equity,
            risk_per_trade=risk_per_trade)

    def test_calc_risk_position_size(self) -> None:
        assert self.port.trade_units ==\
            self.port.equity * self.port.risk_per_trade

    def test_add_position_long(self) -> None:
        position_type = "long"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock()
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]

        self.assertEqual(ps.position_type, position_type)
        self.assertEqual(ps.currency_pair, currency_pair)
        self.assertEqual(ps.units, units)
        self.assertEqual(ps.avg_price, ticker.prices[currency_pair]["ask"])
        self.assertEqual(ps.cur_price, ticker.prices[currency_pair]["bid"])

    def test_add_position_short(self) -> None:
        position_type = "short"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock()
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]

        self.assertEqual(ps.position_type, position_type)
        self.assertEqual(ps.currency_pair, currency_pair)
        self.assertEqual(ps.units, units)
        self.assertEqual(ps.avg_price, ticker.prices[currency_pair]["bid"])
        self.assertEqual(ps.cur_price, ticker.prices[currency_pair]["ask"])

    def test_add_position_units_long(self) -> None:
        position_type = "long"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        add_units = Decimal("1000")
        ticker = TickerMock()

        # Test for no position
        alt_currency_pair = "USDCAD"
        apu = self.port.add_position_units(alt_currency_pair, units)
        self.assertFalse(apu)

        # Add a position and test for real position
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]

        # Test for addition of units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.51878")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.51928")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65842")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65821")
        ticker.prices["USDJPY"]["bid"] = Decimal("110.947")
        ticker.prices["USDJPY"]["ask"] = Decimal("110.961")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00901218")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00901331")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertTrue(apu)
        self.assertEqual(ps.avg_price, Decimal("110.89566667"))

    def test_add_position_units_short(self) -> None:
        position_type = "short"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        add_units = Decimal("1000")
        ticker = TickerMock()

        # Test for no position
        alt_currency_pair = "USDCAD"
        apu = self.port.add_position_units(alt_currency_pair, units)
        self.assertFalse(apu)

        # Add a position and test for real position
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]

        # Test for addition of units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.51878")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.51928")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65842")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65821")
        ticker.prices["USDJPY"]["bid"] = Decimal("110.947")
        ticker.prices["USDJPY"]["ask"] = Decimal("110.961")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00901218")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00901331")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertTrue(apu)
        self.assertEqual(ps.avg_price, Decimal("110.83166667"))

    def test_remove_position_units_long(self) -> None:
        position_type = "long"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock()

        # Test for no position
        alt_currency_pair = "USDCAD"
        apu = self.port.remove_position_units(alt_currency_pair, units)
        self.assertFalse(apu)

        # Add a position and then add units to it
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]
        # Test for addition of units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.51878")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.51928")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65842")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65821")
        ticker.prices["USDJPY"]["bid"] = Decimal("110.947")
        ticker.prices["USDJPY"]["ask"] = Decimal("110.961")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00901218")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00901331")

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("110.94140000"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")
        ticker.prices["USDJPY"]["bid"] = Decimal("108.516")
        ticker.prices["USDJPY"]["ask"] = Decimal("108.605")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00920768")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00921523")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("992723.80"))

    def test_remove_position_units_short(self) -> None:
        position_type = "short"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock()

        # Test for no position
        alt_currency_pair = "USDCAD"
        apu = self.port.remove_position_units(alt_currency_pair, units)
        self.assertFalse(apu)

        # Add a position and then add units to it
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]
        # Test for addition of units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.51878")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.51928")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65842")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65821")
        ticker.prices["USDJPY"]["bid"] = Decimal("110.947")
        ticker.prices["USDJPY"]["ask"] = Decimal("110.961")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00901218")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00901331")

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("110.91240000"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")
        ticker.prices["USDJPY"]["bid"] = Decimal("108.516")
        ticker.prices["USDJPY"]["ask"] = Decimal("108.605")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00920768")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00921523")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("1006922.20"))

    def test_close_position_long(self) -> None:
        position_type = "long"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock()

        # Test for no position
        alt_currency_pair = "USDCAD"
        apu = self.port.remove_position_units(alt_currency_pair, units)
        self.assertFalse(apu)

        # Add a position and then add units to it
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]
        # Test for addition of units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.51878")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.51928")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65842")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65821")
        ticker.prices["USDJPY"]["bid"] = Decimal("110.947")
        ticker.prices["USDJPY"]["ask"] = Decimal("110.961")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00901218")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00901331")

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("110.94140000"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")
        ticker.prices["USDJPY"]["bid"] = Decimal("108.516")
        ticker.prices["USDJPY"]["ask"] = Decimal("108.605")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00920768")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00921523")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("992723.80"))

        # Close the position
        cp = self.port.close_position(currency_pair)
        self.assertTrue(cp)
        self.assertRaises(KeyError, lambda: self.port.positions[currency_pair])
        self.assertEqual(self.port.balance, Decimal("975746.00"))

    def test_close_position_short(self) -> None:
        position_type = "short"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock()

        # Test for no position
        alt_currency_pair = "USDCAD"
        apu = self.port.remove_position_units(alt_currency_pair, units)
        self.assertFalse(apu)

        # Add a position and then add units to it
        self.port.add_new_position(position_type, currency_pair, units, ticker)
        ps = self.port.positions[currency_pair]
        # Test for addition of units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.51878")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.51928")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65842")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65821")
        ticker.prices["USDJPY"]["bid"] = Decimal("110.947")
        ticker.prices["USDJPY"]["ask"] = Decimal("110.961")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00901218")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00901331")

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("110.91240000"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")
        ticker.prices["USDJPY"]["bid"] = Decimal("108.516")
        ticker.prices["USDJPY"]["ask"] = Decimal("108.605")
        ticker.prices["JPYUSD"]["bid"] = Decimal("0.00920768")
        ticker.prices["JPYUSD"]["ask"] = Decimal("0.00921523")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("1006922.20"))

        # Close the position
        cp = self.port.close_position(currency_pair)
        self.assertTrue(cp)
        self.assertRaises(KeyError, lambda: self.port.positions[currency_pair])
        self.assertEqual(self.port.balance, Decimal("1023074.00"))


if __name__ == "__main__":
    unittest.main()
