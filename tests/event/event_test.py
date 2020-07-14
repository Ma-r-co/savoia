import pytest
from decimal import Decimal
import pandas as pd


class TestEvent():
    @pytest.mark.skip()
    @pytest.mark.parametrize("pair, time, bid, ask", [
        ("JPYUSD", "2018-01-16T20:31:22.579385Z", '98.02', '100.13'),
    ])
    def test_TickEvent(self, pair: str, time: str, bid: str, ask: str) -> None:
        from savoia.event.event import TickEvent, EventType
        t = pd.Timestamp(time)
        b = Decimal(bid)
        a = Decimal(ask)

        tick = TickEvent(pair, t, b, a)

        assert tick.type == EventType("TICK")
        assert tick.pair == pair
        assert tick.time == t
        assert tick.bid == b
        assert tick.ask == a

        assert str(tick) == "Type: TICK, Pair: %s, Time: %s, Bid: %s, Ask: %s" \
                            % (str(pair), str(t), str(b), str(a))

    @pytest.mark.parametrize("ref, pair, order_type, units, time, price", [
        ("REF123", "JPYUSD", "market", "200", "2018-01-16 20:31:22", "102.34"),
    ])
    def test_SignalEvent(self, ref: str, pair: str, order_type: str, units: str,
            time: str, price: str) -> None:
        from savoia.event.event import SignalEvent, EventType
        signal = SignalEvent(ref, pair, pd.Timestamp(time), order_type,
            Decimal(units), Decimal(price))

        assert signal.type == EventType("SIGNAL")
        assert signal.pair == pair
        assert signal.order_type == order_type
        assert signal.units == Decimal(units)
        assert signal.time == pd.Timestamp(time)
        assert signal.price == Decimal(price)

        _form = "Type: %s, Ref: %s, Pair: %s, Time: %s, OrderType: %s, " + \
            "Units: %s, Price: %s"
        assert str(signal) == _form \
            % ('SIGNAL', ref, pair, pd.Timestamp(time), order_type,
                Decimal(units), Decimal(price))

    @pytest.mark.parametrize("ref, pair, order_type, units, time, price", [
        ("REF123", "JPYUSD", "market", "200", "2018-01-16 20:31:22", "102.34"),
    ])
    def test_OrderEvent(self, ref: str, pair: str, order_type: str, units: int,
            time: str, price: str) -> None:
        from savoia.event.event import OrderEvent, EventType

        order = OrderEvent(ref, pair, pd.Timestamp(time), order_type,
            Decimal(units), Decimal(price))

        assert order.type == EventType("ORDER")
        assert order.pair == pair
        assert order.units == Decimal(units)
        assert order.order_type == order_type
        assert order.units == Decimal(units)
        assert order.price == Decimal(price)

        _form = "Type: %s, Ref: %s, Pair: %s, Time: %s, OrderType: %s, " + \
            "Units: %s, Price: %s"
        assert str(order) == _form \
            % (
                'ORDER', ref, pair, pd.Timestamp(time), order_type,
                Decimal(units), Decimal(price))

    @pytest.mark.parametrize("ref, pair, status, units, time, price", [
        ("REF123", "JPYUSD", "filled", "200", "2018-01-16 20:31:22", "102.34"),
    ])
    def test_FillEvent(self, ref: str, pair: str, status: str, units: int,
            time: str, price: str) -> None:
        from savoia.event.event import FillEvent, EventType

        fill = FillEvent(ref, pair, pd.Timestamp(time),
            Decimal(units), Decimal(price), status)

        assert fill.type == EventType("FILL")
        assert fill.pair == pair
        assert fill.units == Decimal(units)
        assert fill.status == status
        assert fill.units == Decimal(units)
        assert fill.price == Decimal(price)

        _form = "Type: %s, Ref: %s, Pair: %s, Time: %s, " + \
            "Units: %s, Price: %s, Status: %s"
        assert str(fill) == _form % (
            'FILL', ref, pair, pd.Timestamp(time),
            Decimal(units), Decimal(price), status)
