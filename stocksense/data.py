"""Validate daily sales and select the five series used by the prototype."""
from pathlib import Path

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = ("date", "store", "item", "sales")
STORE = 1
ITEMS = (1, 2, 3, 4, 5)


class DataValidationError(ValueError):
    """A sales file cannot safely be used for forecasting."""


def validate_sales(frame: pd.DataFrame) -> pd.DataFrame:
    """Return sorted, typed records; reject gaps instead of filling with zeros.

    Every series must cover the same date range, with one record per day.
    Extra input columns are ignored after checking the required fields.
    """
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise DataValidationError(f"Missing required columns: {', '.join(sorted(missing))}.")
    data = frame.loc[:, list(REQUIRED_COLUMNS)].copy()
    if data.empty:
        raise DataValidationError("The sales file is empty.")
    if data.isna().any().any():
        raise DataValidationError("The sales file contains missing values.")

    if pd.api.types.is_datetime64_any_dtype(data["date"]):
        dates = data["date"]
        if dates.dt.tz is not None or not dates.eq(dates.dt.normalize()).all():
            raise DataValidationError("Dates must be calendar days without times or time zones.")
    else:
        date_strings = data["date"].astype(str)
        if not date_strings.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
            raise DataValidationError("Dates must use YYYY-MM-DD format.")
        dates = pd.to_datetime(date_strings, format="%Y-%m-%d", errors="coerce")
    if dates.isna().any():
        raise DataValidationError("The sales file contains invalid dates.")
    data["date"] = dates

    for column in ("store", "item", "sales"):
        values = pd.to_numeric(data[column], errors="coerce")
        array = values.to_numpy(dtype=float)
        if not np.isfinite(array).all():
            raise DataValidationError(f"{column} must contain finite numbers.")
        if (array % 1 != 0).any():
            raise DataValidationError(f"{column} must contain whole numbers.")
        minimum = 0 if column == "sales" else 1
        if (array < minimum).any() or (array >= 2**63).any():
            raise DataValidationError(f"{column} must contain valid {'non-negative quantities' if minimum == 0 else 'positive IDs'}.")
        data[column] = values.astype("int64")

    if data.duplicated(["date", "store", "item"]).any():
        raise DataValidationError("Duplicate date-store-item keys were found.")
    data = data.sort_values(["store", "item", "date"]).reset_index(drop=True)
    span = data.groupby(["store", "item"])["date"].agg(["min", "max", "count"])
    start, end = data["date"].min(), data["date"].max()
    expected_days = (end - start).days + 1
    complete = span["min"].eq(start) & span["max"].eq(end) & span["count"].eq(expected_days)
    if not complete.all():
        examples = list(span.index[~complete][:3])
        raise DataValidationError(f"Incomplete daily histories for store/item pairs {examples}. Check missing dates.")
    return data


def load_sales(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Sales file not found: {path}. Place Kaggle train.csv in data/raw/ or supply --source.")
    return validate_sales(pd.read_csv(path))


def select_scope(data: pd.DataFrame) -> pd.DataFrame:
    selected = data.loc[data["store"].eq(STORE) & data["item"].isin(ITEMS)].copy()
    missing = set(ITEMS) - set(selected["item"].unique())
    if missing:
        raise DataValidationError(f"Store {STORE} is missing required item IDs: {sorted(missing)}.")
    return validate_sales(selected)


def audit_sales(data: pd.DataFrame) -> dict:
    """Summarise records already accepted by validate_sales."""
    counts = data.groupby(["store", "item"]).size()
    return {
        "rows": int(len(data)),
        "columns": list(REQUIRED_COLUMNS),
        "start_date": data["date"].min().strftime("%Y-%m-%d"),
        "end_date": data["date"].max().strftime("%Y-%m-%d"),
        "stores": sorted(int(value) for value in data["store"].unique()),
        "items": sorted(int(value) for value in data["item"].unique()),
        "series": int(len(counts)),
        "min_days_per_series": int(counts.min()),
        "max_days_per_series": int(counts.max()),
        "missing_cells": int(data.isna().sum().sum()),
        "duplicate_keys": int(data.duplicated(["date", "store", "item"]).sum()),
        "negative_sales": int(data["sales"].lt(0).sum()),
        "zero_sales": int(data["sales"].eq(0).sum()),
        "sales_min": int(data["sales"].min()),
        "sales_max": int(data["sales"].max()),
        "complete_daily_histories": True,
    }
