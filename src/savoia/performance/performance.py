import pandas as pd
from typing import Tuple


def create_drawdowns(pnl: pd.Series) -> Tuple[pd.Series, float, int]:
    """
    Calculate the largest peak-to-trough drawdown of the PnL curve
    as well as the duration of the drawdown. Requires that the
    pnl_returns is a pandas Series.

    Parameters:
    pnl - A pandas Series representing period percentage returns.

    Returns:
    drawdown, duration - Highest peak-to-trough drawdown and duration.
    """

    # Calculate the cumulative returns curve
    # and set up the High Water Mark
    hwm = [0]

    # Create the drawdown and duration series
    idx = pnl.index
    drawdown = pd.Series(index=idx)
    duration = pd.Series(index=idx)

    # Loop over the index range
    for t in range(1, len(idx)):
        hwm.append(max(hwm[t - 1], pnl.iloc[t]))
        drawdown.iloc[t] = (hwm[t] - pnl.iloc[t])
        duration.iloc[t] = (0 if drawdown.iloc[t] == 0 else duration.iloc[t - 1] + 1)
    return drawdown, drawdown.max(), duration.max()
