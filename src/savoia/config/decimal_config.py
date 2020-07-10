from decimal import ROUND_HALF_EVEN, FloatOperation, \
    DefaultContext, BasicContext, setcontext, Decimal


def initializeDecimalContext() -> None:
    DefaultContext.prec = 18
    DefaultContext.rounding = ROUND_HALF_EVEN
    DefaultContext.traps = BasicContext.traps.copy()
    DefaultContext.traps[FloatOperation] = True
    setcontext(DefaultContext)


DECIMAL_PLACES: Decimal = Decimal("1E-8")
