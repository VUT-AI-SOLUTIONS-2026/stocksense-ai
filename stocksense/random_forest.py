"""Seven-output random forests using past sales and known calendar dates."""
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from stocksense.forecasting import calendar_date

LOOKBACK = 28
SETTINGS = dict(n_estimators=100, max_depth=10, min_samples_leaf=3, random_state=42, n_jobs=1)


def features(history: np.ndarray, cutoff: pd.Timestamp) -> np.ndarray:
    """Lag 1 is the last observed day. No target sales enter the features."""
    history = np.asarray(history, dtype=float)
    if history.shape != (LOOKBACK,) or not np.isfinite(history).all() or (history < 0).any():
        raise ValueError("A complete 28-day history of finite non-negative sales is required.")
    targets = pd.date_range(cutoff + pd.Timedelta(days=1), periods=7, freq="D")
    weekday = 2 * np.pi * targets.dayofweek.to_numpy() / 7
    annual = 2 * np.pi * (targets.dayofyear.to_numpy() - 1) / 365.25
    return np.concatenate([history[::-1], [history[-7:].mean(), history[-14:].mean(), history.mean()],
                           np.sin(weekday), np.cos(weekday), np.sin(annual), np.cos(annual)])


def training_windows(series: pd.DataFrame, train_end: str | pd.Timestamp):
    """Build daily windows only after filtering away every post-training row."""
    train_end = calendar_date(train_end)
    rows = series.loc[series["date"].le(train_end)].sort_values("date")
    if len(rows) < LOOKBACK + 7:
        raise ValueError("Training requires at least 35 observed days per item.")
    if not rows["date"].reset_index(drop=True).equals(pd.Series(pd.date_range(rows["date"].min(), rows["date"].max()))):
        raise ValueError("Training history must contain one record per calendar day.")
    sales = rows["sales"].to_numpy(dtype=float)
    x, y, cutoffs = [], [], []
    for stop in range(LOOKBACK, len(rows) - 6):
        cutoff = rows.iloc[stop - 1]["date"]
        x.append(features(sales[stop - LOOKBACK:stop], cutoff))
        y.append(sales[stop:stop + 7])
        cutoffs.append(cutoff)
    return np.asarray(x), np.asarray(y), pd.DatetimeIndex(cutoffs)


@dataclass
class RandomForestForecast:
    models: dict
    train_end: pd.Timestamp
    training_counts: dict

    def forecast(self, data: pd.DataFrame, *, item: int, cutoff, store: int = 1) -> pd.DataFrame:
        cutoff = calendar_date(cutoff)
        if cutoff < self.train_end:
            raise ValueError("The forecast cut-off precedes this model's training boundary.")
        key = (store, item)
        if key not in self.models:
            raise ValueError("No trained model is available for this store and item.")
        rows = data.loc[data["store"].eq(store) & data["item"].eq(item) & data["date"].le(cutoff)]
        if rows["date"].duplicated().any():
            raise ValueError("History contains duplicate daily records.")
        series = rows.set_index("date")["sales"]
        dates = pd.date_range(cutoff - pd.Timedelta(days=LOOKBACK - 1), cutoff)
        x = features(series.reindex(dates).to_numpy(dtype=float), cutoff)
        prediction = np.maximum(0, self.models[key].predict(x.reshape(1, -1))[0])
        return pd.DataFrame({"store": store, "item": item, "cutoff": cutoff,
                             "date": pd.date_range(cutoff + pd.Timedelta(days=1), periods=7),
                             "prediction": prediction})


def fit_random_forest(data: pd.DataFrame, *, train_end="2015-12-31") -> RandomForestForecast:
    boundary = calendar_date(train_end)
    models, counts = {}, {}
    for (store, item), series in data.groupby(["store", "item"]):
        x, y, _ = training_windows(series, boundary)
        if not np.isfinite(y).all() or (y < 0).any():
            raise ValueError("Training targets must be finite and non-negative.")
        model = RandomForestRegressor(**SETTINGS)
        model.fit(x, y)
        key = (int(store), int(item))
        models[key], counts[key] = model, len(x)
    if not models:
        raise ValueError("No sales series are available for training.")
    return RandomForestForecast(models, boundary, counts)
