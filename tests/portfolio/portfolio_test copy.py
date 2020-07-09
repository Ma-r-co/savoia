from decimal import Decimal
import unittest
import os
import pytest

from queue import Queue

from savoia.portfolio.portfolio import Portfolio
from savoia.config.dir_config import OUTPUT_RESULTS_DIR
from savoia.event.event import Event

from typing import Union


class TickerMock(object):
    """
    A mock object that allows a representation of the
    ticker/pricing handler.
    """

    def __init__(self) -> None:
        self.pairs = ["GBPUSD", "EURUSD"]
        self.prices = {
            "GBPUSD": {"bid": Decimal("1.50328"), "ask": Decimal("1.50349")},
            "USDGBP": {"bid": Decimal("0.66521"), "ask": Decimal("0.66512")},
            "EURUSD": {"bid": Decimal("1.07832"), "ask": Decimal("1.07847")}
        }


class MockSignalEvent():
    def __init__(self, instrument: str, order_type: str, side: str, time: str) -> None:
        self.type = 'SIGNAL'
        self.instrument = instrument
        self.order_type = order_type
        self.side = side
        self.time = time  # Time of the last tick that generated the signal

    def __str__(self) -> str:
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s, Time: %s" % (
            str(self.type), str(self.instrument),
            str(self.order_type), str(self.side), str(self.time)
        )

    def __repr__(self) -> str:
        return str(self)


class MockSignalEventSell():
    def __init__(self) -> None:
        self.type = 'SIGNAL'
        self.instrument = "EURUSD"
        self.order_type = "market"
        self.side = "sell"
        self.time = "dummy"  # Time of the last tick that generated the signal

    def __str__(self) -> str:
        return "Type: %s, Instrument: %s, Order Type: %s, Side: %s" % (
            str(self.type), str(self.instrument),
            str(self.order_type), str(self.side)
        )

    def __repr__(self) -> str:
        return str(self)


class TestPortfolio(unittest.TestCase):
    def setUp(self) -> None:
        home_currency = "GBP"
        leverage = Decimal("20")
        equity = Decimal("100000.00")
        risk_per_trade = Decimal("0.02")
        ticker = TickerMock()
        events: 'Queue[Event]' = Queue()
        self.port = Portfolio(
            ticker=ticker,
            events_queue=events,
            home_currency=home_currency,
            leverage=leverage,
            equity=equity,
            risk_per_trade=risk_per_trade)

    def test_calc_risk_position_size(self) -> None:
        assert self.port.trade_units ==\
            self.port.equity * self.port.risk_per_trade

    def test_add_position_long(self) -> None:
        position_type = "long"
        currency_pair = "GBPUSD"
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
        currency_pair = "GBPUSD"
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
        currency_pair = "GBPUSD"
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
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertTrue(apu)
        self.assertEqual(ps.avg_price, Decimal("1.50875333"))

    def test_add_position_units_short(self) -> None:
        position_type = "short"
        currency_pair = "GBPUSD"
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
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertTrue(apu)
        self.assertEqual(ps.avg_price, Decimal("1.50844667"))

    def test_remove_position_units_long(self) -> None:
        position_type = "long"
        currency_pair = "GBPUSD"
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

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("1.51612200"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("100007.99"))

    def test_remove_position_units_short(self) -> None:
        position_type = "short"
        currency_pair = "GBPUSD"
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

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("1.5156800"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("99988.84"))

    def test_close_position_long(self) -> None:
        position_type = "long"
        currency_pair = "GBPUSD"
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

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("1.516122"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("100007.99"))

        # Close the position
        cp = self.port.close_position(currency_pair)
        self.assertTrue(cp)
        self.assertRaises(KeyError, lambda: self.port.positions[currency_pair])
        self.assertEqual(self.port.balance, Decimal("100026.63"))

    def test_close_position_short(self) -> None:
        position_type = "short"
        currency_pair = "GBPUSD"
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

        add_units = Decimal("8000")
        apu = self.port.add_position_units(currency_pair, add_units)
        self.assertEqual(ps.units, 10000)
        self.assertEqual(ps.avg_price, Decimal("1.51568"))

        # Test removal of (some) of the units
        ticker.prices["GBPUSD"]["bid"] = Decimal("1.52017")
        ticker.prices["GBPUSD"]["ask"] = Decimal("1.52134")
        ticker.prices["USDGBP"]["bid"] = Decimal("0.65782")
        ticker.prices["USDGBP"]["ask"] = Decimal("0.65732")

        remove_units = Decimal("3000")
        rpu = self.port.remove_position_units(currency_pair, remove_units)
        self.assertTrue(rpu)
        self.assertEqual(ps.units, Decimal("7000"))
        self.assertEqual(self.port.balance, Decimal("99988.84"))

        # Close the position
        cp = self.port.close_position(currency_pair)
        self.assertTrue(cp)
        self.assertRaises(KeyError, lambda: self.port.positions[currency_pair])
        self.assertEqual(self.port.balance, Decimal("99962.80"))


class TestPortfolio2():
    @pytest.fixture()
    def port(request) -> Portfolio:
        home_currency = "GBP"
        leverage = Decimal("20")
        equity = Decimal("100000.00")
        risk_per_trade = Decimal("0.02")
        ticker = TickerMock()
        events: 'Queue[Event]' = Queue()
        port = Portfolio(
            ticker,
            events,
            home_currency=home_currency,
            leverage=leverage,
            equity=equity,
            risk_per_trade=risk_per_trade)
        return port

    def test_create_equity_file(self, port: Portfolio) -> None:
        out_file = port.create_equity_file()
        filepath = os.path.join(OUTPUT_RESULTS_DIR, "backtest.csv")
        assert out_file.name == str(filepath)
        assert os.path.isfile(filepath)

        out_file.close()
        with open(filepath, "r") as f:
            assert f.read() == "Timestamp,Balance,GBPUSD,EURUSD\n"

    @pytest.mark.parametrize("instrument, order_type, side, time, quote", [
        ("GBPUSD", "market", "buy", "dummy", "ask"),
        ("EURUSD", "market", "sell", "dummy", "bid"),
    ])
    def test_execute_signal_lackofticker(self,
                                        port: Portfolio,
                                        instrument: str,
                                        order_type: str,
                                        side: str,
                                        time: str,
                                        quote: str) -> None:
        from testfixtures import LogCapture

        tmp = port.ticker.prices[instrument][quote]
        port.ticker.prices[instrument][quote] = None
        with LogCapture() as log:
            port.execute_signal(signal_event=MockSignalEvent(instrument, order_type, side, time))
            log.check(
                ('savoia.portfolio.portfolio', 'INFO', "Unable to execute order as price data was insufficient.")
            )
        port.ticker.prices[instrument][quote] = tmp

    @pytest.mark.parametrize("instrument, order_type, side, time, position_type", [
        ("GBPUSD", "market", "buy", "dummy", "long"),
        ("EURUSD", "market", "sell", "dummy", "short"),
    ])
    def test_execute_signal_NoPositionCreateOne(self,
                                                port: Portfolio,
                                                instrument: str,
                                                order_type: str,
                                                side: str,
                                                time: str,
                                                position_type: str) -> None:
        port.execute_signal(signal_event=MockSignalEvent(instrument, order_type, side, time))
        assert port.positions[instrument].home_currency == 'GBP'
        assert port.positions[instrument].position_type == position_type
        assert port.positions[instrument].currency_pair == instrument
        assert port.positions[instrument].units == int(port.trade_units)
        assert port.positions[instrument].ticker == port.ticker

    @pytest.mark.parametrize("instrument, order_type, side1, time, side2, trade_units_offset, ex_position_type, ex_units", [
        ("GBPUSD", "market", "buy", "dummy", "buy", 0, "long", 4000),
        ("GBPUSD", "market", "buy", "dummy", "buy", +1, "long", 4001),
        ("GBPUSD", "market", "buy", "dummy", "buy", -1, "long", 3999),
        ("GBPUSD", "market", "buy", "dummy", "sell", 0, "square", "dummy"),
        ("GBPUSD", "market", "buy", "dummy", "sell", +1, "short", 1),
        ("GBPUSD", "market", "buy", "dummy", "sell", -1, "long", 1),
        ("GBPUSD", "market", "sell", "dummy", "buy", 0, "square", "dummy"),
        ("GBPUSD", "market", "sell", "dummy", "buy", +1, "long", 1),
        ("GBPUSD", "market", "sell", "dummy", "buy", -1, "short", 1),
        ("GBPUSD", "market", "sell", "dummy", "sell", 0, "short", 4000),
        ("GBPUSD", "market", "sell", "dummy", "sell", +1, "short", 4001),
        ("GBPUSD", "market", "sell", "dummy", "sell", -1, "short", 3999),
        ("EURUSD", "market", "buy", "dummy", "buy", 0, "long", 4000),
        ("EURUSD", "market", "buy", "dummy", "buy", +1, "long", 4001),
        ("EURUSD", "market", "buy", "dummy", "buy", -1, "long", 3999),
        ("EURUSD", "market", "buy", "dummy", "sell", 0, "square", "dummy"),
        ("EURUSD", "market", "buy", "dummy", "sell", +1, "short", 1),
        ("EURUSD", "market", "buy", "dummy", "sell", -1, "long", 1),
        ("EURUSD", "market", "sell", "dummy", "buy", 0, "square", "dummy"),
        ("EURUSD", "market", "sell", "dummy", "buy", +1, "long", 1),
        ("EURUSD", "market", "sell", "dummy", "buy", -1, "short", 1),
        ("EURUSD", "market", "sell", "dummy", "sell", 0, "short", 4000),
        ("EURUSD", "market", "sell", "dummy", "sell", +1, "short", 4001),
        ("EURUSD", "market", "sell", "dummy", "sell", -1, "short", 3999),
    ])
    def test_execute_signal_IfPositionExsists(
        self, port: Portfolio, instrument: str, order_type: str, side1: str, time: str,
        side2: str, trade_units_offset: int, ex_position_type: str, ex_units: Union[int, str]
    ) -> None:
        port.execute_signal(signal_event=MockSignalEvent(instrument, order_type, side1, time))

        port.trade_units = port.trade_units + trade_units_offset
        port.execute_signal(signal_event=MockSignalEvent(instrument, order_type, side2, time))

        if ex_position_type == "square":
            with pytest.raises(KeyError):
                port.positions[instrument]
        else:
            assert port.positions[instrument].position_type == ex_position_type
            assert port.positions[instrument].units == ex_units


if __name__ == "__main__":
    unittest.main()
