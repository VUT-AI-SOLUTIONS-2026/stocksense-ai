"""Score non-overlapping seven-day forecasts on chronological periods."""
import numpy as np
import pandas as pd

from stocksense.forecasting import calendar_date, seasonal_naive_forecast

PERIODS = {
    "validation": ("2016-01-01", "2016-12-31"),
    "test": ("2017-01-01", "2017-12-31"),
}


def _metrics(predictions: pd.DataFrame) -> dict:
    errors = predictions["prediction"].to_numpy() - predictions["actual_sales"].to_numpy()
    weeks = predictions.groupby(["store", "item", "cutoff"])[["prediction", "actual_sales"]].sum()
    weekly_errors = weeks["prediction"] - weeks["actual_sales"]
    return {
        "daily_forecasts": int(len(predictions)),
        "forecast_weeks": int(len(weeks)),
        "mae_units": float(np.abs(errors).mean()),
        "rmse_units": float(np.sqrt(np.mean(errors**2))),
        "weekly_total_mae_units": float(weekly_errors.abs().mean()),
    }


def evaluate_baseline(
    data: pd.DataFrame, *, start: str, end: str,
) -> tuple[pd.DataFrame, dict]:
    return evaluate_forecaster(data, start=start, end=end,
                               forecaster=seasonal_naive_forecast, method="weekly_seasonal_naive")


def evaluate_forecaster(
    data: pd.DataFrame, *, start: str, end: str, forecaster, method: str,
) -> tuple[pd.DataFrame, dict]:
    """Use identical forecast dates and scoring rules for every method."""
    start_date, end_date = calendar_date(start), calendar_date(end)
    if end_date < start_date:
        raise ValueError("Evaluation end must not be before its start.")
    origins = [date for date in pd.date_range(start_date, end_date, freq="7D")
               if date + pd.Timedelta(days=6) <= end_date]
    if not origins:
        raise ValueError("Evaluation requires at least one complete seven-day forecast week.")
    if data.empty:
        raise ValueError("No sales series are available for evaluation.")
    forecasts = []
    for (store, item), series in data.groupby(["store", "item"]):
        for origin in origins:
            forecast = forecaster(
                series, store=int(store), item=int(item),
                cutoff=origin - pd.Timedelta(days=1),
            )
            expected_dates = pd.date_range(origin, periods=7, freq="D")
            if (len(forecast) != 7 or not forecast["date"].reset_index(drop=True).equals(pd.Series(expected_dates))
                    or not forecast["store"].eq(store).all() or not forecast["item"].eq(item).all()):
                raise ValueError("Each forecast must contain seven correctly dated predictions for its series.")
            values = forecast["prediction"].to_numpy(dtype=float)
            if not np.isfinite(values).all() or (values < 0).any():
                raise ValueError("Predictions must be finite and non-negative.")
            forecasts.append(forecast)
    predicted = pd.concat(forecasts, ignore_index=True)
    actual = data[["store", "item", "date", "sales"]].rename(columns={"sales": "actual_sales"})
    # Attach outcomes only after predictions have been created from past history.
    scored = predicted.merge(actual, how="left", on=["store", "item", "date"], validate="one_to_one")
    if scored["actual_sales"].isna().any():
        raise ValueError("Actual sales are missing for an evaluation date; no scores were written.")
    scored["error"] = scored["prediction"] - scored["actual_sales"]
    last_target = origins[-1] + pd.Timedelta(days=6)
    excluded = pd.date_range(last_target + pd.Timedelta(days=1), end_date, freq="D")
    per_item = []
    for (store, item), rows in scored.groupby(["store", "item"]):
        per_item.append({"store": int(store), "item": int(item), **_metrics(rows)})
    summary = {
        "method": method,
        "horizon_days": 7,
        "origin_step_days": 7,
        "period_start": start_date.strftime("%Y-%m-%d"),
        "period_end": end_date.strftime("%Y-%m-%d"),
        "first_scored_date": start_date.strftime("%Y-%m-%d"),
        "last_scored_date": last_target.strftime("%Y-%m-%d"),
        "excluded_incomplete_week_dates": [date.strftime("%Y-%m-%d") for date in excluded],
        "weeks_per_item": len(origins),
        "overall": _metrics(scored),
        "per_item": per_item,
    }
    return scored.sort_values(["store", "item", "date"]).reset_index(drop=True), summary
