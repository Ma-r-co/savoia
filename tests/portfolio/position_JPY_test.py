from decimal import Decimal
import unittest

from savoia.portfolio.position import Position


# =====================================
# Tests for JPY
# =====================================


class TickerMock2(object):
    """
    A mock object that allows a representation of the
    ticker/pricing handler.
    """
    def __init__(self) -> None:
        self.pairs = ["GBPUSD", "USDJPY"]
        self.prices = {
            "GBPUSD": {"bid": Decimal("1.50328"), "ask": Decimal("1.50349")},
            "USDGBP": {"bid": Decimal("0.66521"), "ask": Decimal("0.66512")},
            "USDJPY": {"bid": Decimal("110.774"), "ask": Decimal("110.863")},
            "JPYUSD": {"bid": Decimal("0.00902739"), "ask": Decimal("0.00902014")}
        }


# =====================================
# JPY Home Currency with USD/JPY traded
# =====================================

class TestLongUSDJPYPosition(unittest.TestCase):
    """
    Unit tests that cover going long USD/JPY with an account
    denominated currency of JPY, using 2,000 units of GBP/USD.
    """
    def setUp(self) -> None:
        home_currency = "JPY"
        position_type = "long"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock2()
        self.position = Position(
            home_currency, position_type,
            currency_pair, units, ticker
        )

    def test_calculate_init_pips(self) -> None:
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("-0.08900000"))

    def test_calculate_init_profit_base(self) -> None:
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("-178.00000000"))

    def test_calculate_init_profit_perc(self) -> None:
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("-0.08027926"))

    def test_calculate_updated_values(self) -> None:
        """
        Check that after the bid/ask prices move, that the updated
        pips, profit and percentage profit calculations are correct.
        """
        prices = self.position.ticker.prices
        prices["USDJPY"] = {"bid": Decimal("110.947"), "ask": Decimal("110.961")}
        prices["JPYUSD"] = {"bid": Decimal("0.00901331"), "ask": Decimal("0.00901218")}
        self.position.update_position_price()

        # Check pips
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("0.08400000"))
        # Check profit base
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("168.00000000"))
        # Check profit percentage
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("0.07576919"))


class TestShortUSDJPYPosition(unittest.TestCase):
    """
    Unit tests that cover going short USD/JPY with an account
    denominated currency of JPY, using 2,000 units of USD/JPY.
    """
    def setUp(self) -> None:
        home_currency = "JPY"
        position_type = "short"
        currency_pair = "USDJPY"
        units = Decimal("2000")
        ticker = TickerMock2()
        self.position = Position(
            home_currency, position_type,
            currency_pair, units, ticker
        )

    def test_calculate_init_pips(self) -> None:
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("-0.08900000"))

    def test_calculate_init_profit_base(self) -> None:
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("-178.00000000"))

    def test_calculate_init_profit_perc(self) -> None:
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("-0.08034376"))

    def test_calculate_updated_values(self) -> None:
        """
        Check that after the bid/ask prices move, that the updated
        pips, profit and percentage profit calculations are correct.
        """
        prices = self.position.ticker.prices
        prices["USDJPY"] = {"bid": Decimal("110.947"), "ask": Decimal("110.961")}
        prices["JPYUSD"] = {"bid": Decimal("0.00901331"), "ask": Decimal("0.00901218")}
        self.position.update_position_price()

        # Check pips
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("-0.18700000"))
        # Check profit base
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("-374.00000000"))
        # Check profit percentage
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("-0.16881218"))


# =====================================
# JPY Home Currency with GBP/USD traded
# =====================================

class TestLongGBPUSDPosition(unittest.TestCase):
    """
    Unit tests that cover going long GBP/USD with an account
    denominated currency of JPY, using 2,000 units of GBP/USD.
    """
    def setUp(self) -> None:
        home_currency = "JPY"
        position_type = "long"
        currency_pair = "GBPUSD"
        units = Decimal("2000")
        ticker = TickerMock2()
        self.position = Position(
            home_currency, position_type,
            currency_pair, units, ticker
        )

    def test_calculate_init_pips(self) -> None:
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("-0.00021000"))

    def test_calculate_init_profit_base(self) -> None:
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("-46.52508000"))

    def test_calculate_init_profit_perc(self) -> None:
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("-0.01396750"))

    def test_calculate_updated_values(self) -> None:
        """
        Check that after the bid/ask prices move, that the updated
        pips, profit and percentage profit calculations are correct.
        """
        prices = self.position.ticker.prices
        prices["USDJPY"] = {"bid": Decimal("110.947"), "ask": Decimal("110.961")}
        prices["JPYUSD"] = {"bid": Decimal("0.00901331"), "ask": Decimal("0.00901218")}
        prices["GBPUSD"] = {"bid": Decimal("1.50486"), "ask": Decimal("1.50586")}
        prices["USDGBP"] = {"bid": Decimal("0.66451"), "ask": Decimal("0.66407")}
        self.position.update_position_price()

        # Check pips
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("0.00137000"))
        # Check profit base
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("303.99478"))
        # Check profit percentage
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("0.09112132"))


class TestShortGBPUSDPosition(unittest.TestCase):
    """
    Unit tests that cover going short GBP/USD with an account
    denominated currency of JPY, using 2,000 units of GBP/USD.
    """
    def setUp(self) -> None:
        home_currency = "JPY"
        position_type = "short"
        currency_pair = "GBPUSD"
        units = Decimal("2000")
        ticker = TickerMock2()
        self.position = Position(
            home_currency, position_type,
            currency_pair, units, ticker
        )

    def test_calculate_init_pips(self) -> None:
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("-0.00021000"))

    def test_calculate_init_profit_base(self) -> None:
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("-46.56246000"))

    def test_calculate_init_profit_perc(self) -> None:
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("-0.01396945"))

    def test_calculate_updated_values(self) -> None:
        """
        Check that after the bid/ask prices move, that the updated
        pips, profit and percentage profit calculations are correct.
        """
        prices = self.position.ticker.prices
        prices["USDJPY"] = {"bid": Decimal("110.947"), "ask": Decimal("110.961")}
        prices["JPYUSD"] = {"bid": Decimal("0.00901331"), "ask": Decimal("0.00901218")}
        prices["GBPUSD"] = {"bid": Decimal("1.50486"), "ask": Decimal("1.50586")}
        prices["USDGBP"] = {"bid": Decimal("0.66451"), "ask": Decimal("0.66407")}
        self.position.update_position_price()

        # Check pips
        pos_pips = self.position._calculate_pips()
        self.assertEqual(pos_pips, Decimal("-0.00258000"))
        # Check profit base
        profit_base = self.position._calculate_profit_base()
        self.assertEqual(profit_base, Decimal("-572.55876000"))
        # Check profit percentage
        profit_perc = self.position._calculate_profit_perc()
        self.assertEqual(profit_perc, Decimal("-0.17162471"))


if __name__ == "__main__":
    unittest.main()
