import pytest
from savoia.feed.price import PriceHandler, HistoricCSVPriceHandler
from queue import Queue
from decimal import Decimal
import pandas as pd
import os


@pytest.fixture(scope='function')
def ph() -> PriceHandler:
    pairs = ["USDJPY", "GBPUSD"]
    instance = PriceHandler()
    instance.pairs = pairs
    return instance


def test_set_up_prices_dict(ph: PriceHandler) -> None:
    """_set_up_prices_dict should return both prices dict and inv-prices dict """
    prices_dict = ph._set_up_prices_dict()
    assert sorted(list(prices_dict.keys())) == sorted(["USDJPY", "JPYUSD", "GBPUSD", "USDGBP"])
    for v in prices_dict.values():
        assert v == {'bid': None, 'ask': None, 'time': None}


@pytest.mark.parametrize('pair, bid, ask, return_pair, return_bid, return_ask',
                        [("USDJPY", Decimal('106.87'), Decimal('106.90'),
                        "JPYUSD", Decimal('0.00935454'), Decimal('0.00935716')),
                        ("EURGBP", Decimal('0.90473'), Decimal('0.90561'),
                        "GBPEUR", Decimal('1.10422809'), Decimal('1.10530213'))])
def test_invert_prices(ph: PriceHandler, pair: str, bid: Decimal, ask: Decimal, return_pair: str, return_bid: Decimal, return_ask: Decimal) -> None:
    """ invert_prices should return inverted pair, bid and ask prices"""
    inv_pair, inv_bid, inv_ask = ph.invert_prices(pair, bid, ask)
    assert inv_pair == return_pair
    assert inv_bid == return_bid
    assert inv_ask == return_ask

# ---------------------------------------------------------------
# ---------------------------------------------------------------
@pytest.fixture(scope='function')
def hcph() -> HistoricCSVPriceHandler:
    pairs = ["USDJPY", "GBPUSD"]
    return HistoricCSVPriceHandler(pairs, Queue(), './tests/feed')


def test_list_all_csv_files(hcph: HistoricCSVPriceHandler) -> None:
    """ _list_all_csv_files should return a sorted list of csv files in a directory"""
    files = hcph._list_all_csv_files()
    assert files == sorted([
        'GBPUSD_20140101.csv',
        'GBPUSD_20140102.csv',
        'USDJPY_20140101.csv',
        'USDJPY_20140102.csv'
    ])


def test_list_all_file_dates(hcph: HistoricCSVPriceHandler) -> None:
    """
    _list_all_file_dates should return a sorted and not-duplicated list of
    dates in the feed directory.
    """
    dates = hcph._list_all_file_dates()
    assert dates == sorted([
        '20140101',
        '20140102',
    ])


@pytest.mark.parametrize('date', ['20140101', '20140102'])
def test_open_convert_csv_files_for_day(hcph: HistoricCSVPriceHandler, date: str) -> None:
    """_open_convert_csv_files_for_day should return a consolidated
    frame including all the ticks of a specified date.
    """
    expected_frame = pd.io.parsers.read_csv(
        os.path.join(hcph.csv_dir, 'expected_frame_%s.csv' % (date)),
        header=0,
        index_col=0,
        parse_dates=["Time"],
        dayfirst=True,
        names=("Time", "Ask", "Bid", "AskVolume", "BidVolume", "Pair")
    )
    actual_frame = hcph._open_convert_csv_files_for_day(date)
    for (a0, a1), (e0, e1) in zip(actual_frame, expected_frame.iterrows()):
        assert a0 == e0
        pd.testing.assert_series_equal(a1, e1)


def test_update_csv_for_day(hcph: HistoricCSVPriceHandler) -> None:
    """_update_csv_for_day should update both self.cur_date_pairs and
    self.cur_date_idx.
    """
    assert hcph._update_csv_for_day() is True
    
    expected_frame = pd.io.parsers.read_csv(
        os.path.join(hcph.csv_dir, 'expected_frame_%s.csv' % (20140102)),
        header=0,
        index_col=0,
        parse_dates=["Time"],
        dayfirst=True,
        names=("Time", "Ask", "Bid", "AskVolume", "BidVolume", "Pair")
    )
    for (a0, a1), (e0, e1) in zip(hcph.cur_date_pairs, expected_frame.iterrows()):
        assert a0 == e0
        pd.testing.assert_series_equal(a1, e1)

    assert hcph._update_csv_for_day() is False


def test_stream_next_tick(hcph: HistoricCSVPriceHandler) -> None:
    """stream_next_tick should update self.prices with the fetched
    values. It shoud also feed a tick event to the queue accordingly.
    """
    hcph.stream_next_tick()
    pair = 'GBPUSD'
    ask = Decimal('1.50054')
    bid = Decimal('1.49854')
    time = pd.Timestamp('01.01.2014 00:02:24.967')
    inv_pair = 'USDGBP'
    inv_ask = (Decimal('1') / bid).quantize(Decimal('0.00000001'))
    inv_bid = (Decimal('1') / ask).quantize(Decimal('0.00000001'))
    assert hcph.prices[pair]["bid"] == bid
    assert hcph.prices[pair]["ask"] == ask
    assert hcph.prices[pair]["time"] == time
    assert hcph.prices[inv_pair]["bid"] == inv_bid
    assert hcph.prices[inv_pair]["ask"] == inv_ask
    assert hcph.prices[inv_pair]["time"] == time
