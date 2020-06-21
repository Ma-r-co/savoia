import pytest


class TestEvent():
    @pytest.mark.parametrize("instrument, time, bid, ask", [
        ("JPYUSD", "2018-01-16T20:31:22.579385Z", 98.02, 100.13),
    ])
    def test_TickEvent(self, instrument, time, bid, ask):
        from savoia.event.event import TickEvent

        tick = TickEvent(instrument, time, bid, ask)

        assert tick.type == "TICK"
        assert tick.instrument == instrument
        assert tick.time == time
        assert tick.bid == bid
        assert tick.ask == ask

        assert str(tick) == "Type: TICK, Instrument: %s, Time: %s, Bid: %s, Ask: %s" \
                            % (str(instrument), str(time), str(bid), str(ask))

    @pytest.mark.parametrize("instrument, order_type, side, time", [
        ("JPYUSD", "market", "buy", "2018-01-16T20:31:22.579385Z"),
    ])
    def test_SignalEvent(self, instrument, order_type, side, time):
        from savoia.event.event import SignalEvent

        signal = SignalEvent(instrument, order_type, side, time)

        assert signal.type == "SIGNAL"
        assert signal.instrument == instrument
        assert signal.order_type == order_type
        assert signal.side == side
        assert signal.time == time

        assert str(signal) == "Type: SIGNAL, Instrument: %s, Order Type: %s, Side: %s, Time: %s" \
            % (str(instrument), str(order_type), str(side), str(time))

    @pytest.mark.parametrize("instrument, units, order_type, side", [
        ("JPYUSD", 100, "market", "buy"),
    ])
    def test_OrderEvent(self, instrument, units, order_type, side):
        from savoia.event.event import OrderEvent

        order = OrderEvent(instrument, units, order_type, side)

        assert order.type == "ORDER"
        assert order.instrument == instrument
        assert order.units == units
        assert order.order_type == order_type
        assert order.side == side

        assert str(order) == "Type: ORDER, Instrument: %s, Units: %s, Order Type: %s, Side: %s" \
            % (str(instrument), str(units), str(order_type), str(side))
