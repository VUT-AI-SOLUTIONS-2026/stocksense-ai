"""Measure the weekly seasonal naive baseline; validation is the default."""
import argparse
import json
from pathlib import Path
from time import perf_counter

from stocksense.data import load_sales, select_scope
from stocksense.evaluation import PERIODS, evaluate_baseline
from scripts.prepare_data import PREPARED, ROOT


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PREPARED)
    parser.add_argument("--period", choices=PERIODS, default="validation")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    output = args.output_dir or ROOT / "artifacts" / "baseline" / args.period
    try:
        data = select_scope(load_sales(args.input))
        started = perf_counter()
        predictions, summary = evaluate_baseline(data, start=PERIODS[args.period][0], end=PERIODS[args.period][1])
    except (ValueError, OSError) as error:
        parser.exit(1, f"Evaluation failed: {error}\n")
    summary["period"] = args.period
    summary["evaluation_seconds"] = perf_counter() - started
    summary["training_required"] = False
    output.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output / "predictions.csv", index=False, date_format="%Y-%m-%d")
    (output / "metrics.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"{args.period.title()}: {summary['first_scored_date']} to {summary['last_scored_date']}")
    print(f"{summary['weeks_per_item']} weeks per item; {len(predictions):,} daily forecasts.")
    print(f"{'Item':<8}{'MAE (units)':>14}{'RMSE (units)':>16}{'Weekly MAE':>16}")
    for row in summary["per_item"]:
        print(f"{row['item']:<8}{row['mae_units']:>14.3f}{row['rmse_units']:>16.3f}{row['weekly_total_mae_units']:>16.3f}")
    overall = summary["overall"]
    print(f"{'Overall':<8}{overall['mae_units']:>14.3f}{overall['rmse_units']:>16.3f}{overall['weekly_total_mae_units']:>16.3f}")
    print(f"Excluded dates: {', '.join(summary['excluded_incomplete_week_dates']) or 'none'}")
    print(f"Saved results: {output}")


if __name__ == "__main__":
    main()
