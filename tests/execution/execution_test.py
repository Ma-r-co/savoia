import pytest

from savoia.execution.execution import SimulatedExecution
from savoia.event.event import Event, OrderEvent, FillEvent

from queue import Queue
from typing import Tuple
from decimal import Decimal
import pandas as pd


# ================================================================
# SimulatedExecution
# ================================================================
@pytest.fixture(scope='function')
def setupSE() -> Tuple['Queue[Event]', 'Queue[Event]', SimulatedExecution]:
    event_q: 'Queue[Event]' = Queue()
    exec_q: 'Queue[Event]' = Queue()
    return event_q, exec_q, SimulatedExecution(event_q, exec_q)


def test__init__(setupSE: Tuple['Queue[Event]', 'Queue[Event]',
        SimulatedExecution]) -> None:
    event_q, exec_q, se = setupSE
    assert isinstance(se, SimulatedExecution)


def test_return_fill_event(setupSE: Tuple['Queue[Event]', 'Queue[Event]',
        SimulatedExecution]) -> None:
    event_q, exec_q, se = setupSE
    
    exec_q.put(OrderEvent('ID1234', "USDJPY", Decimal('0.5'), Decimal('107.89'),
        'market', pd.Timestamp('2020-07-10 20:59:32')))
    exec_q.put(None)
    se.run()
    
    fe: FillEvent = event_q.get(False)
    assert fe.ref == 'ID1234'
    assert fe.instrument == 'USDJPY'
    assert fe.units == Decimal('0.5')
    assert fe.status == 'filled'
