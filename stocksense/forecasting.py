"""The weekly seasonal naive benchmark: repeat the last observed week."""
import re

import numpy as np
import pandas as pd


def calendar_date(value: str | pd.Timestamp) -> pd.Timestamp:
    if isinstance(value, str) and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Use a YYYY-MM-DD calendar date.")
    date = pd.Timestamp(value)
    if pd.isna(date) or date.tz is not None or date != date.normalize():
        raise ValueError("Use a calendar date without a time or time zone.")
    return date


def seasonal_naive_forecast(
    data: pd.DataFrame,
    *,
    item: int,
    cutoff: str | pd.Timestamp,
    store: int = 1,
    horizon: int = 7,
) -> pd.DataFrame:
    """Forecast only from information observed on or before cutoff.

    For horizons of one to seven days, each target copies the sales from
    exactly seven days earlier. A full week ending on cutoff is required.
    """
    if isinstance(horizon, bool) or not isinstance(horizon, int) or not 1 <= horizon <= 7:
        raise ValueError("Forecast horizon must be a whole number from 1 to 7 days.")
    cutoff = calendar_date(cutoff)
    series = data.loc[
        data["store"].eq(store) & data["item"].eq(item) & data["date"].le(cutoff)
    ].set_index("date")["sales"]
    if series.empty:
        raise ValueError(f"No history is available for store {store}, item {item}, at this cut-off.")
    if not series.index.is_unique:
        raise ValueError("History contains duplicate daily records.")
    history_dates = pd.date_range(cutoff - pd.Timedelta(days=6), cutoff, freq="D")
    week = series.reindex(history_dates)
    if week.isna().any():
        raise ValueError("A complete seven-day history ending on the cut-off date is required.")
    quantities = week.to_numpy(dtype=float)
    if not np.isfinite(quantities).all() or (quantities < 0).any():
        raise ValueError("Observed sales must be finite and non-negative.")
    dates = pd.date_range(cutoff + pd.Timedelta(days=1), periods=horizon, freq="D")
    return pd.DataFrame({
        "store": store,
        "item": item,
        "cutoff": cutoff,
        "date": dates,
        "prediction": quantities[:horizon],
    })
