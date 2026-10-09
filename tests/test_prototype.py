from pathlib import Path
import tempfile
import unittest

import joblib
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from stocksense.evaluation import evaluate_baseline, evaluate_forecaster
from stocksense.inventory import plan_stock
from stocksense.random_forest import features, fit_random_forest, training_windows
from tests.test_baseline import sales_fixture


class RandomForestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = sales_fixture(start="2015-10-01", end="2016-02-28")
        cls.model = fit_random_forest(cls.data)

    def test_training_targets_never_cross_boundary(self):
        x, y, cutoffs = training_windows(self.data, "2015-12-31")
        self.assertEqual(len(x), 58)
        self.assertEqual(y.shape, (58, 7))
        self.assertEqual(cutoffs.max(), pd.Timestamp("2015-12-24"))
        self.assertEqual(cutoffs.min(), pd.Timestamp("2015-10-28"))
        self.assertEqual(y[-1].tolist(), [86, 87, 88, 89, 90, 91, 92])
        tampered = self.data.copy()
        tampered.loc[tampered["date"].gt("2015-12-31"), "sales"] = 999999
        changed_x, changed_y, changed_dates = training_windows(tampered, "2015-12-31")
        np.testing.assert_array_equal(x, changed_x)
        np.testing.assert_array_equal(y, changed_y)
        self.assertTrue(cutoffs.equals(changed_dates))

    def test_features_use_past_lags_and_known_calendar(self):
        x = features(np.arange(1, 29), pd.Timestamp("2015-12-31"))
        np.testing.assert_array_equal(x[:28], np.arange(28, 0, -1))
        self.assertAlmostEqual(x[28], 25)
        self.assertEqual(len(x), 59)

    def test_future_changes_cannot_change_prediction(self):
        original = self.model.forecast(self.data, item=1, cutoff="2016-01-14")
        changed = self.data.copy()
        changed.loc[changed["date"].gt("2016-01-14"), "sales"] = 1000000
        pd.testing.assert_frame_equal(original, self.model.forecast(changed, item=1, cutoff="2016-01-14"))
        self.assertEqual(len(original), 7)
        self.assertEqual(original["date"].min(), pd.Timestamp("2016-01-15"))
        self.assertTrue(original["prediction"].ge(0).all())

    def test_saved_model_reproduces_forecast(self):
        expected = self.model.forecast(self.data, item=1, cutoff="2016-01-14")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "forest.joblib"
            joblib.dump(self.model, path)
            loaded = joblib.load(path)
            pd.testing.assert_frame_equal(expected, loaded.forecast(self.data, item=1, cutoff="2016-01-14"))

    def test_invalid_history_and_pretraining_cutoff_fail(self):
        with self.assertRaisesRegex(ValueError, "training boundary"):
            self.model.forecast(self.data, item=1, cutoff="2015-12-30")
        missing = self.data.loc[~self.data["date"].eq("2016-01-10")]
        with self.assertRaisesRegex(ValueError, "28-day history"):
            self.model.forecast(missing, item=1, cutoff="2016-01-14")
        with self.assertRaisesRegex(ValueError, "No trained model"):
            self.model.forecast(self.data, item=2, cutoff="2016-01-14")

    def test_comparison_uses_identical_dates_and_samples(self):
        baseline, _ = evaluate_baseline(self.data, start="2016-01-01", end="2016-02-28")
        rf, summary = evaluate_forecaster(self.data, start="2016-01-01", end="2016-02-28",
                                          forecaster=self.model.forecast, method="random_forest")
        pd.testing.assert_frame_equal(baseline[["store", "item", "date"]], rf[["store", "item", "date"]])
        self.assertEqual(summary["weeks_per_item"], 8)
        self.assertEqual(summary["overall"]["daily_forecasts"], 56)


class InventoryTests(unittest.TestCase):
    def test_calculation_cases(self):
        # Independently specified input/output cases, including delivery timing.
        cases = [
            ("basic", [10]*7, 20, 0, 2, 3, 5, 35, 0),
            ("sufficient stock", [10]*7, 100, 0, 2, 3, 5, 0, 0),
            ("outstanding lowers order", [10]*7, 20, 15, 2, 3, 5, 20, 0),
            ("shortage before delivery", [10]*7, 5, 50, 2, 3, 0, 0, 15),
            ("instant delivery", [10]*7, 0, 0, 0, 3, 0, 30, 0),
            ("all seven days", [10]*7, 0, 0, 6, 1, 0, 70, 60),
            ("one day coverage", [10]*7, 3, 0, 0, 1, 0, 7, 0),
            ("zero demand", [0]*7, 0, 0, 2, 3, 0, 0, 0),
            ("buffer only", [0]*7, 0, 0, 2, 3, 4, 4, 0),
            ("round final order upwards", [1.25]*7, 0, 0, 0, 3, 0, 4, 0),
            ("exact delivery balance", [10]*7, 20, 0, 2, 3, 0, 30, 0),
            ("varying daily demand", [1, 2, 3, 4, 5, 6, 7], 2, 4, 2, 2, 2, 6, 1),
        ]
        for label, forecast, stock, outstanding, lead, review, buffer, expected, shortage in cases:
            with self.subTest(case=label):
                result = plan_stock(forecast, stock=stock, outstanding=outstanding,
                                    lead_days=lead, review_days=review, buffer=buffer)
                self.assertEqual(result.suggested_order, expected)
                self.assertEqual(result.shortage_before_delivery, shortage)

    def test_invalid_inputs_are_rejected(self):
        defaults = dict(stock=10, outstanding=0, lead_days=2, review_days=3, buffer=0)
        for field in defaults:
            for value in [-1, 1.5, True, np.inf]:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    plan_stock([10]*7, **{**defaults, field: value})
        for changed in [dict(review_days=0), dict(lead_days=6, review_days=2)]:
            with self.assertRaises(ValueError):
                plan_stock([10]*7, **{**defaults, **changed})

    def test_invalid_forecasts_are_rejected(self):
        for values in [[1]*6, [1]*8, [-1]*7, [np.nan]*7, [np.inf]*7]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                plan_stock(values, stock=0, outstanding=0, lead_days=1, review_days=1, buffer=0)


class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        if not (self.root / "data/prepared/store_1_items_1_to_5.csv").exists():
            self.skipTest("Prepare the local dataset before dashboard integration tests.")
        self.app = AppTest.from_file(str(self.root / "app.py"), default_timeout=30).run()
        self.assertEqual(len(self.app.exception), 0)

    def test_all_five_items_and_calculation(self):
        for item in range(1, 6):
            with self.subTest(item=item):
                self.app.selectbox[0].set_value(item).run()
                self.assertEqual(len(self.app.exception), 0)
                table = self.app.dataframe[0].value
                self.assertEqual(len(table), 7)
                self.assertIn("2018", table.iloc[0]["Date"])
        self.app.button[0].click().run()
        self.assertEqual(len(self.app.exception), 0)
        self.assertEqual(self.app.metric[1].label, "Suggested order")

    def test_invalid_coverage_and_delivery_shortage_messages(self):
        self.app.number_input(key="lead").set_value(6)
        self.app.number_input(key="review").set_value(3)
        self.app.button[0].click().run()
        self.assertTrue(any("must not exceed seven days" in error.value for error in self.app.error))
        self.app.number_input(key="stock").set_value(0)
        self.app.number_input(key="lead").set_value(2)
        self.app.number_input(key="review").set_value(3)
        self.app.button[0].click().run()
        self.assertTrue(any("Possible shortage before delivery" in warning.value for warning in self.app.warning))
        self.assertEqual(len(self.app.exception), 0)


if __name__ == "__main__":
    unittest.main()
