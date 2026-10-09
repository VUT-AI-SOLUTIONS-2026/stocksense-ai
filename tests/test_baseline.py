import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pandas as pd

from stocksense.data import DataValidationError, load_sales, select_scope, validate_sales
from stocksense.evaluation import evaluate_baseline
from stocksense.forecasting import seasonal_naive_forecast


def sales_fixture(start="2016-01-01", end="2016-01-30", items=(1,)):
    return pd.DataFrame([
        {"date": date, "store": 1, "item": item, "sales": day + item}
        for item in items
        for day, date in enumerate(pd.date_range(start, end, freq="D"))
    ])


class DataTests(unittest.TestCase):
    def test_csv_is_parsed_sorted_and_scoped(self):
        data = sales_fixture(items=(1, 2, 3, 4, 5, 6)).sample(frac=1, random_state=42)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sales.csv"
            data.to_csv(path, index=False)
            scoped = select_scope(load_sales(path))
        self.assertEqual(len(scoped), 150)
        self.assertEqual(scoped["item"].unique().tolist(), [1, 2, 3, 4, 5])
        self.assertEqual(scoped.iloc[0]["date"], pd.Timestamp("2016-01-01"))
        self.assertEqual(scoped.iloc[-1]["date"], pd.Timestamp("2016-01-30"))

    def test_missing_required_column_is_rejected(self):
        with self.assertRaisesRegex(DataValidationError, "Missing required columns: sales"):
            validate_sales(sales_fixture().drop(columns="sales"))

    def test_duplicate_key_is_rejected_even_with_different_sales(self):
        data = sales_fixture()
        duplicate = data.iloc[[0]].copy()
        duplicate["sales"] = 999
        with self.assertRaisesRegex(DataValidationError, "Duplicate date-store-item"):
            validate_sales(pd.concat([data, duplicate], ignore_index=True))

    def test_missing_internal_day_and_boundary_day_are_rejected(self):
        for missing_date in ["2016-01-10", "2016-01-01", "2016-01-30"]:
            with self.subTest(missing_date=missing_date):
                data = sales_fixture(items=(1, 2))
                data = data.loc[~(data["item"].eq(2) & data["date"].eq(missing_date))]
                with self.assertRaisesRegex(DataValidationError, "Incomplete daily histories"):
                    validate_sales(data)

    def test_missing_selected_item_is_rejected(self):
        with self.assertRaisesRegex(DataValidationError, "missing required item IDs: \\[5\\]"):
            select_scope(validate_sales(sales_fixture(items=(1, 2, 3, 4))))

    def test_bad_quantities_are_rejected(self):
        for value in [-1, 1.5, np.inf, np.nan]:
            with self.subTest(value=value):
                data = sales_fixture()
                data["sales"] = data["sales"].astype(float)
                data.loc[0, "sales"] = value
                with self.assertRaises(DataValidationError):
                    validate_sales(data)

    def test_zero_sales_is_retained(self):
        data = sales_fixture()
        data.loc[0, "sales"] = 0
        self.assertEqual(validate_sales(data).iloc[0]["sales"], 0)

    def test_invalid_or_ambiguous_dates_are_rejected(self):
        for value in ["2016-02-30", "01/02/2016", "2016-01-01 12:00:00"]:
            with self.subTest(value=value):
                data = sales_fixture()
                data["date"] = data["date"].dt.strftime("%Y-%m-%d")
                data.loc[0, "date"] = value
                with self.assertRaises(DataValidationError):
                    validate_sales(data)


class ForecastTests(unittest.TestCase):
    def test_matching_weekdays_and_seven_dates(self):
        forecast = seasonal_naive_forecast(sales_fixture(), item=1, cutoff="2016-01-14")
        self.assertEqual(forecast["prediction"].tolist(), [8., 9., 10., 11., 12., 13., 14.])
        self.assertEqual(forecast["date"].dt.strftime("%Y-%m-%d").tolist(),
                         [f"2016-01-{day}" for day in range(15, 22)])

    def test_forecast_is_unchanged_when_future_sales_change(self):
        original = sales_fixture()
        changed = original.copy()
        changed.loc[changed["date"].gt("2016-01-14"), "sales"] = 1_000_000
        expected = seasonal_naive_forecast(original, item=1, cutoff="2016-01-14")
        observed = seasonal_naive_forecast(changed, item=1, cutoff="2016-01-14")
        pd.testing.assert_frame_equal(expected, observed)

    def test_missing_day_or_stale_cutoff_is_rejected(self):
        data = sales_fixture()
        data = data.loc[~data["date"].eq("2016-01-12")]
        with self.assertRaisesRegex(ValueError, "complete seven-day history"):
            seasonal_naive_forecast(data, item=1, cutoff="2016-01-14")
        with self.assertRaisesRegex(ValueError, "complete seven-day history"):
            seasonal_naive_forecast(sales_fixture(), item=1, cutoff="2016-01-31")

    def test_unsupported_item_and_horizons_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "No history"):
            seasonal_naive_forecast(sales_fixture(), item=6, cutoff="2016-01-14")
        for horizon in [0, 8, 1.5, True]:
            with self.subTest(horizon=horizon):
                with self.assertRaisesRegex(ValueError, "horizon"):
                    seasonal_naive_forecast(sales_fixture(), item=1, cutoff="2016-01-14", horizon=horizon)


class EvaluationTests(unittest.TestCase):
    def test_metrics_against_known_daily_and_weekly_errors(self):
        scored, summary = evaluate_baseline(sales_fixture(), start="2016-01-15", end="2016-01-30")
        self.assertEqual(summary["overall"]["mae_units"], 7)
        self.assertEqual(summary["overall"]["rmse_units"], 7)
        self.assertEqual(summary["overall"]["weekly_total_mae_units"], 49)
        self.assertEqual(summary["overall"]["daily_forecasts"], 14)
        self.assertEqual(summary["weeks_per_item"], 2)
        self.assertEqual(summary["excluded_incomplete_week_dates"], ["2016-01-29", "2016-01-30"])
        self.assertFalse(scored.duplicated(["store", "item", "date"]).any())

    def test_leap_year_uses_only_complete_weeks(self):
        data = sales_fixture(start="2015-12-25", end="2016-12-31")
        _, summary = evaluate_baseline(data, start="2016-01-01", end="2016-12-31")
        self.assertEqual(summary["weeks_per_item"], 52)
        self.assertEqual(summary["overall"]["daily_forecasts"], 364)
        self.assertEqual(summary["last_scored_date"], "2016-12-29")
        self.assertEqual(summary["excluded_incomplete_week_dates"], ["2016-12-30", "2016-12-31"])

    def test_missing_actual_sales_fail_instead_of_shrinking_the_scores(self):
        data = sales_fixture().loc[lambda frame: ~frame["date"].eq("2016-01-20")]
        with self.assertRaisesRegex(ValueError, "Actual sales are missing"):
            evaluate_baseline(data, start="2016-01-15", end="2016-01-21")

    def test_incomplete_period_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "complete seven-day"):
            evaluate_baseline(sales_fixture(), start="2016-01-15", end="2016-01-20")


class CommandTests(unittest.TestCase):
    def test_prepare_preserves_source_when_output_paths_collide(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.csv"
            output = Path(directory) / "prepared.csv"
            audit = Path(directory) / "audit.json"
            sales_fixture(items=(1, 2, 3, 4, 5)).to_csv(source, index=False)
            original = source.read_bytes()
            for prepared_path, audit_path in [(source, audit), (output, output)]:
                with self.subTest(prepared_path=prepared_path, audit_path=audit_path):
                    process = subprocess.run([
                        sys.executable, "-m", "scripts.prepare_data", "--source", str(source),
                        "--output", str(prepared_path), "--audit", str(audit_path),
                    ], cwd=root, capture_output=True, text=True, timeout=30)
                    self.assertNotEqual(process.returncode, 0)
                    self.assertIn("different paths", process.stderr)
                    self.assertEqual(source.read_bytes(), original)
            self.assertFalse(output.exists())
            self.assertFalse(audit.exists())

    def test_prepare_evaluate_and_forecast_commands_together(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            source, prepared = folder / "source.csv", folder / "prepared.csv"
            audit, forecast = folder / "audit.json", folder / "forecast.csv"
            sales_fixture(start="2015-12-25", end="2016-12-31", items=(1, 2, 3, 4, 5)).to_csv(source, index=False)
            commands = [
                ["scripts.prepare_data", "--source", str(source), "--output", str(prepared), "--audit", str(audit)],
                ["scripts.evaluate_forecasters", "--input", str(prepared), "--output-dir", str(folder / "results")],
                ["scripts.forecast_baseline", "--input", str(prepared), "--output", str(forecast)],
            ]
            for command in commands:
                process = subprocess.run([sys.executable, "-m", *command], cwd=root,
                                         capture_output=True, text=True, timeout=30)
                self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertEqual(json.loads(audit.read_text())["selected_scope"]["rows"], 1865)
            self.assertEqual(json.loads((folder / "results" / "metrics.json").read_text())["overall"]["daily_forecasts"], 1820)
            output = pd.read_csv(forecast)
            self.assertEqual(len(output), 35)
            self.assertEqual(output["date"].min(), "2017-01-01")
            self.assertEqual(output["date"].max(), "2017-01-07")
            self.assertEqual(pd.read_csv(source).shape, (1865, 4))


if __name__ == "__main__":
    unittest.main()
