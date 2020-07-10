import pytest
from decimal import Decimal
import pandas as pd


class TestEvent():
    @pytest.mark.skip()
    @pytest.mark.parametrize("instrument, time, bid, ask", [
        ("JPYUSD", "2018-01-16T20:31:22.579385Z", '98.02', '100.13'),
    ])
    def test_TickEvent(self, instrument: str, time: str, bid: str, ask: str) -> None:
        from savoia.event.event import TickEvent, EventType
        t = pd.Timestamp(time)
        b = Decimal(bid)
        a = Decimal(ask)

        tick = TickEvent(instrument, t, b, a)

        assert tick.type == EventType("TICK")
        assert tick.instrument == instrument
        assert tick.time == t
        assert tick.bid == b
        assert tick.ask == a

        assert str(tick) == "Type: TICK, Instrument: %s, Time: %s, Bid: %s, Ask: %s" \
                            % (str(instrument), str(t), str(b), str(a))

    @pytest.mark.skip()
    @pytest.mark.parametrize("instrument, order_type, side, time", [
        ("JPYUSD", "market", "buy", "2018-01-16T20:31:22.579385Z"),
    ])
    def test_SignalEvent(self, instrument: str, order_type: str, side: str, time: str) -> None:
        from savoia.event.event import SignalEvent, EventType
        t = pd.Timestamp(time)
        signal = SignalEvent(instrument, order_type, side, t)

        assert signal.type == EventType("SIGNAL")
        assert signal.instrument == instrument
        assert signal.order_type == order_type
        assert signal.side == side
        assert signal.time == t

        assert str(signal) == "Type: SIGNAL, Instrument: %s, Order Type: %s, Side: %s, Time: %s" \
            % (str(instrument), str(order_type), str(side), str(t))

    @pytest.mark.skip()
    @pytest.mark.parametrize("instrument, units, order_type, side", [
        ("JPYUSD", 100, "market", "buy"),
    ])
    def test_OrderEvent(self, instrument: str, units: int, order_type: str, side: str) -> None:
        from savoia.event.event import OrderEvent, EventType

        order = OrderEvent(instrument, units, order_type, side)

        assert order.type == EventType("ORDER")
        assert order.instrument == instrument
        assert order.units == units
        assert order.order_type == order_type
        assert order.side == side

        assert str(order) == "Type: ORDER, Instrument: %s, Units: %s, Order Type: %s, Side: %s" \
            % (str(instrument), str(units), str(order_type), str(side))
