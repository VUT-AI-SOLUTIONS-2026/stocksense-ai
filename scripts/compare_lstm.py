"""Validate the small LSTM, freeze choices, then separately score 2017 once."""
import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter

import joblib

from scripts.prepare_data import PREPARED, ROOT
from stocksense.data import load_sales, select_scope
from stocksense.evaluation import evaluate_baseline, evaluate_forecaster
from stocksense.lstm import LSTMForecast, SETTINGS as LSTM_SETTINGS, fit_lstm
from stocksense.random_forest import SETTINGS as RF_SETTINGS, fit_random_forest


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def choose_method(methods):
    # Dictionary order is benchmark, random forest, LSTM: retain simpler ties.
    return min(methods, key=lambda name: methods[name]["overall"]["mae_units"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("validation", "final"), default="validation")
    parser.add_argument("--input", type=Path, default=PREPARED)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts/forecasters")
    args = parser.parse_args()
    output = args.output_dir
    comparison_path = output / "comparison.json"
    lock_path = output / "selection-lock.json"
    test_path = output / "final-test.json"
    if not comparison_path.exists():
        parser.error("Run scripts.train_forecasters first to create the baseline comparison.")
    if args.stage == "validation" and lock_path.exists():
        parser.error("Model choices are already frozen. Use --stage final, or a new output directory for a separately labelled experiment.")
    if args.stage == "final" and not lock_path.exists():
        parser.error("Run the validation stage and freeze choices before scoring the final year.")
    if args.stage == "final" and test_path.exists():
        parser.error("The final evaluation is already recorded; read final-test.json rather than tuning on it.")
    data = select_scope(load_sales(args.input))
    digest = hashlib.sha256(args.input.read_bytes()).hexdigest()
    development = data.loc[data["date"].le("2016-12-31")].copy()
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    if args.stage == "validation":
        started = perf_counter()
        lstm = fit_lstm(development)
        training_seconds = perf_counter() - started
        predictions, metrics = evaluate_forecaster(development, start="2016-01-01", end="2016-12-31",
                                                   forecaster=lstm.forecast, method="lstm")
        lstm.save(output / "lstm_validation")
        predictions.to_csv(output / "lstm_validation.csv", index=False, date_format="%Y-%m-%d")
        comparison["methods"]["lstm"] = metrics
        chosen = choose_method(comparison["methods"])
        comparison.update(selected_method=chosen, selection_status="Frozen using 2016 daily MAE before the 2017 test.",
                          lstm_training_seconds=training_seconds, lstm_settings=LSTM_SETTINGS)
        lock = {"selected_method": chosen, "source_sha256": digest, "selection_metric": "2016 overall daily MAE",
                "training_end": "2015-12-31", "validation_end": "2016-12-31", "refit_end": "2016-12-31",
                "random_forest_settings": RF_SETTINGS, "lstm_settings": LSTM_SETTINGS,
                "lstm_epochs": {f"{store}:{item}": info["selected_epochs"] for (store, item), info in lstm.details.items()}}
        write_json(comparison_path, comparison)
        write_json(lock_path, lock)
        print(f"LSTM validation MAE: {metrics['overall']['mae_units']:.3f}")
        print(f"Frozen method: {chosen}. Final 2017 test has not been scored.")
        return
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if (digest != lock["source_sha256"] or RF_SETTINGS != lock["random_forest_settings"]
            or LSTM_SETTINGS != lock["lstm_settings"] or comparison["selected_method"] != lock["selected_method"]):
        parser.error("Dataset, settings or selected method changed after freezing; cannot run this final evaluation.")
    epochs = {tuple(map(int, key.split(":"))): value for key, value in lock["lstm_epochs"].items()}
    started = perf_counter()
    forest = fit_random_forest(development, train_end=lock["refit_end"])
    rf_seconds = perf_counter() - started
    started = perf_counter()
    lstm = fit_lstm(development, train_end=lock["refit_end"], fixed_epochs=epochs)
    lstm_seconds = perf_counter() - started
    # Save and reload before scoring so the evaluated models match persisted files.
    joblib.dump(forest, output / "random_forest.joblib")
    lstm.save(output / "lstm_final")
    forest = joblib.load(output / "random_forest.joblib")
    lstm = LSTMForecast.load(output / "lstm_final")
    models = {"weekly_seasonal_naive": None, "random_forest": forest, "lstm": lstm}
    report = {"selected_method": lock["selected_method"], "selection_source": "2016 validation, frozen before final scoring",
              "refit_end": lock["refit_end"], "source_sha256": digest,
              "refit_seconds": {"random_forest": rf_seconds, "lstm": lstm_seconds}, "methods": {}}
    for name, model in models.items():
        if model is None:
            predictions, metrics = evaluate_baseline(data, start="2017-01-01", end="2017-12-31")
        else:
            predictions, metrics = evaluate_forecaster(data, start="2017-01-01", end="2017-12-31",
                                                       forecaster=model.forecast, method=name)
        report["methods"][name] = metrics
        predictions.to_csv(output / f"{name}_final_test.csv", index=False, date_format="%Y-%m-%d")
        print(f"Final 2017 {name}: MAE {metrics['overall']['mae_units']:.3f}, RMSE {metrics['overall']['rmse_units']:.3f}")
    write_json(test_path, report)
    comparison.update(test_year_scored=True, final_test=report, demo_training_end=lock["refit_end"])
    write_json(comparison_path, comparison)
    print(f"Selected method remains {lock['selected_method']}; the final test does not change selection.")


if __name__ == "__main__":
    main()
