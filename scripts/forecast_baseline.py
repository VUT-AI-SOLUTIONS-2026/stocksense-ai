"""Produce a seven-day historical demonstration forecast from the last week."""
import argparse
from pathlib import Path

import pandas as pd

from stocksense.data import ITEMS, load_sales, select_scope
from stocksense.forecasting import seasonal_naive_forecast
from scripts.prepare_data import PREPARED, ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PREPARED)
    parser.add_argument("--item", type=int, choices=ITEMS)
    parser.add_argument("--cutoff", help="Last observed day, YYYY-MM-DD; defaults to the last available date.")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "baseline" / "demo_forecast.csv")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("The forecast output must not overwrite its input file.")
    try:
        data = select_scope(load_sales(args.input))
        cutoff = args.cutoff or data["date"].max()
        forecasts = pd.concat([
            seasonal_naive_forecast(data, item=item, cutoff=cutoff)
            for item in ([args.item] if args.item is not None else ITEMS)
        ], ignore_index=True)
    except (ValueError, OSError) as error:
        parser.exit(1, f"Forecast failed: {error}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(args.output, index=False, date_format="%Y-%m-%d")
    print(f"Historical demonstration; cut-off {forecasts['cutoff'].iloc[0]:%Y-%m-%d}.")
    print("These are benchmark estimates, not live forecasts or verified future outcomes.")
    display = forecasts[["item", "date", "prediction"]].copy()
    display["date"] = display["date"].dt.strftime("%Y-%m-%d")
    print(display.to_string(index=False))
    print(f"Saved forecast: {args.output}")


if __name__ == "__main__":
    main()
