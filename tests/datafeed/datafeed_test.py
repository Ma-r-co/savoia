import pytest
from savoia.datafeed.datafeed import DataFeeder, HistoricCSVDataFeeder
from savoia.ticker.ticker import Ticker
from queue import Queue
from decimal import Decimal
import pandas as pd
import os
from typing import Tuple


@pytest.fixture(scope='function')
def setupDataFeeder() -> Tuple[Ticker, DataFeeder]:
    pairs = ["USDJPY", "GBPUSD"]
    ticker = Ticker(pairs)
    datafeeder = HistoricCSVDataFeeder(ticker, Queue(), './tests/datafeed')
    return ticker, datafeeder


# ---------------------------------------------------------------
# DataFeeder
# ---------------------------------------------------------------
def test_list_all_csv_files(setupDataFeeder: Tuple[Ticker, DataFeeder]) -> None:
    """_list_all_csv_files should return a sorted list of csv files in a
    directory
    """
    ticker, df = setupDataFeeder
    files = df._list_all_csv_files()
    assert files == sorted([
        'GBPUSD_20140101.csv',
        'GBPUSD_20140102.csv',
        'USDJPY_20140101.csv',
        'USDJPY_20140102.csv'
    ])


def test_list_all_file_dates(setupDataFeeder: Tuple[Ticker, DataFeeder]) \
        -> None:
    """_list_all_file_dates should return a sorted and not-duplicated list of
    dates in the feed directory.
    """
    ticker, df = setupDataFeeder
    dates = df._list_all_file_dates()
    assert dates == sorted([
        '20140101',
        '20140102',
    ])


@pytest.mark.parametrize('date', ['20140101', '20140102'])
def test_open_convert_csv_files_for_day(
        setupDataFeeder: Tuple[Ticker, DataFeeder],
        date: str) -> None:
    """_open_convert_csv_files_for_day should return a consolidated
    frame including all the ticks of a specified date.
    """
    ticker, df = setupDataFeeder
    expected_frame = pd.io.parsers.read_csv(
        os.path.join(df.csv_dir, 'expected_frame_%s.csv' % (date)),
        header=0,
        index_col=0,
        parse_dates=["Time"],
        dayfirst=True,
        names=("Time", "Ask", "Bid", "AskVolume", "BidVolume", "Pair")
    )
    actual_frame = df._open_convert_csv_files_for_day(date)
    for (a0, a1), (e0, e1) in zip(actual_frame, expected_frame.iterrows()):
        assert a0 == e0
        pd.testing.assert_series_equal(a1, e1)


def test_update_csv_for_day(setupDataFeeder: Tuple[Ticker, DataFeeder]) -> None:
    """_update_csv_for_day should update both self.cur_date_pairs and
    self.cur_date_idx.
    """
    ticker, df = setupDataFeeder
    assert df._update_csv_for_day() is True
    
    expected_frame = pd.io.parsers.read_csv(
        os.path.join(df.csv_dir, 'expected_frame_%s.csv' % (20140102)),
        header=0,
        index_col=0,
        parse_dates=["Time"],
        dayfirst=True,
        names=("Time", "Ask", "Bid", "AskVolume", "BidVolume", "Pair")
    )
    for (a0, a1), (e0, e1) in zip(df.cur_date_pairs,
                                  expected_frame.iterrows()):
        assert a0 == e0
        pd.testing.assert_series_equal(a1, e1)

    assert df._update_csv_for_day() is False


def test_stream_next_tick(setupDataFeeder: Tuple[Ticker, DataFeeder]) -> None:
    """stream_next_tick should update self.prices with the fetched
    values. It shoud also feed a tick event to the queue accordingly.
    """
    ticker, df = setupDataFeeder
    df.stream_next_tick()
    pair = 'GBPUSD'
    ask = Decimal('1.50054')
    bid = Decimal('1.49854')
    time = pd.Timestamp('01.01.2014 00:02:24.967')
    inv_pair = 'USDGBP'
    inv_ask = (Decimal('1') / bid).quantize(Decimal('0.00000001'))
    inv_bid = (Decimal('1') / ask).quantize(Decimal('0.00000001'))
    assert ticker.prices[pair]["bid"] == bid
    assert ticker.prices[pair]["ask"] == ask
    assert ticker.prices[pair]["time"] == time
    assert ticker.prices[inv_pair]["bid"] == inv_bid
    assert ticker.prices[inv_pair]["ask"] == inv_ask
    assert ticker.prices[inv_pair]["time"] == time
