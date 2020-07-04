import pytest

from savoia.execution.execution import SimulatedExecution
from savoia.event.event import Event

from queue import Queue
from typing import Tuple
from decimal import Decimal


@pytest.fixture(scope='function')
def setupSE() -> Tuple['Queue[Event]', SimulatedExecution]:
    q: 'Queue[Event]' = Queue()
    return q, SimulatedExecution(q)


def test__init__(setupSE: Tuple['Queue[Event]', SimulatedExecution]) \
        -> None:
    q, se = setupSE
    assert isinstance(se, SimulatedExecution)


def test_return_fill_event(setupSE: Tuple['Queue[Event]', SimulatedExecution]) \
        -> None:
    q, se = setupSE
    se._return_fill_event("USDJPY", Decimal('0.5'), Decimal('107.89'), 'buy',
    'filled')
