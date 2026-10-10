"""Compare the random forest with the benchmark on 2016 validation only."""
import argparse
import json
from pathlib import Path
from time import perf_counter

import joblib
from scripts.prepare_data import PREPARED, ROOT
from stocksense.data import load_sales, select_scope
from stocksense.evaluation import evaluate_baseline, evaluate_forecaster
from stocksense.random_forest import SETTINGS, fit_random_forest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=PREPARED)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "forecasters")
    args = parser.parse_args()
    if (args.output_dir / "selection-lock.json").exists():
        parser.error("Model choices are frozen in this output directory. Read the existing results or use a new output directory for a separately labelled experiment.")
    if args.input.resolve().is_relative_to(args.output_dir.resolve()):
        parser.error("The output directory must not contain the input CSV.")
    try:
        data = select_scope(load_sales(args.input))
        # Test-year rows are never passed to training or validation.
        development = data.loc[data["date"].le("2016-12-31")].copy()
        started = perf_counter()
        forest = fit_random_forest(development)
        training_seconds = perf_counter() - started
        predictions, rf = evaluate_forecaster(development, start="2016-01-01", end="2016-12-31",
                                               forecaster=forest.forecast, method="random_forest")
        baseline_predictions, baseline = evaluate_baseline(development, start="2016-01-01", end="2016-12-31")
        chosen = "random_forest" if rf["overall"]["mae_units"] < baseline["overall"]["mae_units"] else "weekly_seasonal_naive"
        summary = {"selection_status": "Provisional: baseline versus random forest; LSTM comparison pending.",
                   "selection_metric": "Overall daily validation MAE; ties retain the benchmark.",
                   "selected_method": chosen, "training_start": "2013-01-01", "training_end": "2015-12-31",
                   "training_seconds": training_seconds, "settings": SETTINGS,
                   "training_windows_per_item": {str(item): count for (_, item), count in forest.training_counts.items()},
                   "methods": {"weekly_seasonal_naive": baseline, "random_forest": rf},
                   "test_year_scored": False}
        # Save a separate refit for demonstration after 2016. Do not score 2017 here.
        started = perf_counter()
        demo = fit_random_forest(development, train_end="2016-12-31")
        summary["demo_refit_seconds"] = perf_counter() - started
        summary["demo_training_end"] = "2016-12-31"
    except (ValueError, OSError) as error:
        parser.exit(1, f"Training failed: {error}\n")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(demo, args.output_dir / "random_forest.joblib")
    predictions.to_csv(args.output_dir / "random_forest_validation.csv", index=False, date_format="%Y-%m-%d")
    baseline_predictions.to_csv(args.output_dir / "baseline_validation.csv", index=False, date_format="%Y-%m-%d")
    (args.output_dir / "comparison.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"Baseline validation MAE: {baseline['overall']['mae_units']:.3f} units")
    print(f"Random forest validation MAE: {rf['overall']['mae_units']:.3f} units")
    print(f"Provisional dashboard method: {chosen}")
    print(f"Training: {training_seconds:.3f}s; demo refit: {summary['demo_refit_seconds']:.3f}s")
    print("2017 final test not scored. LSTM comparison remains pending.")
    print(f"Saved model and comparison: {args.output_dir}")


if __name__ == "__main__":
    main()
