import threading
from savoia.config.decimal_config import initializeDecimalContext
from decimal import getcontext
from typing import List


def test_initializeDecimalContext() -> None:
    def worker(testList: List[str]) -> None:
        testList.append(str(getcontext()))

    initializeDecimalContext()

    testlist: List[str] = []
    t1 = threading.Thread(target=worker, args=(testlist,))
    t2 = threading.Thread(target=worker, args=(testlist,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert testlist[0] == (
        'Context(prec=18, rounding=ROUND_HALF_EVEN, Emin=-999999, ' +
        'Emax=999999, capitals=1, clamp=0, flags=[], ' +
        'traps=[Clamped, InvalidOperation, DivisionByZero, FloatOperation, Overflow, Underflow])'
    )
    assert testlist[1] == (
        'Context(prec=18, rounding=ROUND_HALF_EVEN, Emin=-999999, ' +
        'Emax=999999, capitals=1, clamp=0, flags=[], ' +
        'traps=[Clamped, InvalidOperation, DivisionByZero, FloatOperation, Overflow, Underflow])'
    )
