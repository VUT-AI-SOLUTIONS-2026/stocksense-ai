import importlib.util
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from scripts.compare_lstm import choose_method
from stocksense.lstm import LSTMForecast, fit_lstm, scaler_for, sequence_windows, validation_windows
from tests.test_baseline import sales_fixture


class SequenceTests(unittest.TestCase):
    def test_training_and_scaler_ignore_future_sales(self):
        data = sales_fixture(start="2015-10-01", end="2016-12-31")
        changed = data.copy()
        changed.loc[changed.date.gt("2015-12-31"), "sales"] = 999999
        x, y, dates = sequence_windows(data, "2015-12-31")
        xx, yy, dd = sequence_windows(changed, "2015-12-31")
        np.testing.assert_array_equal(x, xx)
        np.testing.assert_array_equal(y, yy)
        self.assertTrue(dates.equals(dd))
        self.assertEqual(x.shape, (58, 28, 1))
        np.testing.assert_array_equal(x[0, :, 0], np.arange(1, 29))
        np.testing.assert_array_equal(y[0], np.arange(29, 36))
        self.assertEqual(scaler_for(data, "2015-12-31"), scaler_for(changed, "2015-12-31"))

    def test_validation_uses_complete_weeks_and_only_past_inputs(self):
        data = sales_fixture(start="2015-12-01", end="2016-12-31")
        x, y = validation_windows(data)
        self.assertEqual(x.shape, (52, 28, 1))
        self.assertEqual(y.shape, (52, 7))
        np.testing.assert_array_equal(x[0, :, 0], np.arange(4, 32))
        np.testing.assert_array_equal(y[0], np.arange(32, 39))
        self.assertEqual(y[-1, -1], data.loc[data.date.eq("2016-12-29"), "sales"].iloc[0])

    def test_selection_uses_daily_mae_and_retains_simpler_ties(self):
        methods = {name: {"overall": {"mae_units": mae, "weekly_total_mae_units": weekly}}
                   for name, mae, weekly in [("weekly_seasonal_naive", 6, 10), ("random_forest", 5, 20), ("lstm", 5, 9)]}
        self.assertEqual(choose_method(methods), "random_forest")


@unittest.skipUnless(importlib.util.find_spec("keras") and importlib.util.find_spec("torch"),
                     "Install requirements-deep-learning.txt for LSTM integration checks.")
class LSTMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = sales_fixture(start="2016-10-01", end="2017-02-28")
        cls.model = fit_lstm(cls.data, train_end="2016-12-31", fixed_epochs={(1, 1): 2})

    def test_fixed_epoch_refit_and_saved_forecast(self):
        details = self.model.details[(1, 1)]
        self.assertEqual(details["epochs_run"], 2)
        self.assertNotIn("val_loss", details["history"])
        self.assertEqual(details["parameters"], 1271)
        expected = self.model.forecast(self.data, item=1, cutoff="2017-01-14")
        self.assertEqual(len(expected), 7)
        self.assertTrue(expected.prediction.ge(0).all())
        self.assertEqual(expected.date.min(), pd.Timestamp("2017-01-15"))
        with tempfile.TemporaryDirectory() as directory:
            self.model.save(Path(directory))
            loaded = LSTMForecast.load(directory)
            pd.testing.assert_frame_equal(expected, loaded.forecast(self.data, item=1, cutoff="2017-01-14"))

    def test_forecast_ignores_future_sales_and_keeps_weights_fixed(self):
        weights = [w.copy() for w in self.model.models[(1, 1)].get_weights()]
        expected = self.model.forecast(self.data, item=1, cutoff="2017-01-14")
        changed = self.data.copy()
        changed.loc[changed.date.gt("2017-01-14"), "sales"] = 999999
        pd.testing.assert_frame_equal(expected, self.model.forecast(changed, item=1, cutoff="2017-01-14"))
        for before, after in zip(weights, self.model.models[(1, 1)].get_weights()):
            np.testing.assert_array_equal(before, after)

    def test_incomplete_history_and_early_cutoff_fail(self):
        with self.assertRaisesRegex(ValueError, "training boundary"):
            self.model.forecast(self.data, item=1, cutoff="2016-12-30")
        missing = self.data.loc[~self.data.date.eq("2017-01-10")]
        with self.assertRaisesRegex(ValueError, "28-day history"):
            self.model.forecast(missing, item=1, cutoff="2017-01-14")
