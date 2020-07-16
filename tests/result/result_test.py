import pytest
import py
import os

from savoia.result.result import EquityResult, ExecutionResult, \
    FileResultHandler, Result

from queue import Queue
import pandas as pd
from decimal import Decimal


# =============================================================
# FileResultHandler
# =============================================================
def test_init_(tmpdir: py.path.local) -> None:
    pairs = ['GBPUSD', 'USDJPY']
    result_q: 'Queue[Result]' = Queue()
    equity_file = tmpdir.join('Equity.csv')
    execution_file = tmpdir.join('Execution.csv')

    frh = FileResultHandler(pairs, result_q, tmpdir)
    frh._close()

    assert os.path.isfile(equity_file)
    assert os.path.isfile(execution_file)

    assert equity_file.read() == 'Timestamp,Equity,Balance,UPL[Total],' + \
        'UPL[GBPUSD],UPL[USDJPY]\n'
    assert execution_file.read() == 'Timestamp,Pair,Units,Price\n'


def test_run(tmpdir: py.path.local) -> None:
    pairs = ['GBPUSD', 'USDJPY']
    result_q: 'Queue[Result]' = Queue()
    equity_file = tmpdir.join('Equity.csv')
    execution_file = tmpdir.join('Execution.csv')
    equity_result = EquityResult(
        pd.Timestamp('2020-07-15 22:18:23'),
        Decimal('111.1'),
        Decimal('2222.22'),
        {
            'total': Decimal('33.333'),
            'GBPUSD': Decimal('4.4444'),
            'USDJPY': Decimal('5.55555')
        }
    )
    execution_result = ExecutionResult(
        pd.Timestamp('2020-07-14 22:20:00'),
        'USDJPY',
        Decimal('2.22'),
        Decimal('99.9')
    )

    frh = FileResultHandler(pairs, result_q, tmpdir)
    result_q.put(equity_result)
    result_q.put(execution_result)
    result_q.put(None)
    frh.run()

    equity_file_result = equity_file.readlines()
    execution_file_result = execution_file.readlines()
    assert equity_file_result[0] == 'Timestamp,Equity,Balance,UPL[Total],' + \
        'UPL[GBPUSD],UPL[USDJPY]\n'
    assert equity_file_result[1] == \
        '2020-07-15 22:18:23,111.1,2222.22,33.333,4.4444,5.55555\n'
    assert execution_file_result[0] == 'Timestamp,Pair,Units,Price\n'
    assert execution_file_result[1] == '2020-07-14 22:20:00,USDJPY,2.22,99.9\n'
