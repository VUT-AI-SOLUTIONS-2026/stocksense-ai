import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from stocksense.assistant import train_intents
from stocksense.runtime import ASSISTANT, DATA, ROOT, ForecastService, load_assistant
from stocksense.terminal import TerminalSession, main, plain_text


def terminal_sales():
    return pd.DataFrame([
        {"date": day, "store": 1, "item": item, "sales": 10 * item}
        for item in range(1, 6)
        for day in pd.date_range("2017-12-04", "2017-12-31")
    ])


class ForecastServiceTests(unittest.TestCase):
    def write_history(self, root):
        path = root / "data/prepared/store_1_items_1_to_5.csv"
        path.parent.mkdir(parents=True)
        terminal_sales().to_csv(path, index=False, date_format="%Y-%m-%d")

    def test_loader_uses_benchmark_when_no_comparison_exists(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_history(root)
            service = ForecastService.load(root)
        forecast = service.forecast(2)
        self.assertEqual(service.method, "weekly_seasonal_naive")
        self.assertEqual(forecast["date"].min(), pd.Timestamp("2018-01-01"))
        self.assertEqual(forecast["prediction"].tolist(), [20] * 7)
        self.assertEqual(len(service.recent(2)), 28)

    def test_missing_setup_explains_how_to_prepare_it(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(FileNotFoundError, "scripts.prepare_data"):
                ForecastService.load(directory)
            with self.assertRaisesRegex(FileNotFoundError, "scripts.train_assistant"):
                load_assistant(directory)

    def test_selected_missing_model_never_silently_changes_method(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_history(root)
            comparison = root / "artifacts/forecasters/comparison.json"
            comparison.parent.mkdir(parents=True)
            for method, exception, message in (
                ("random_forest", FileNotFoundError, "saved forecast model is missing"),
                ("lstm", FileNotFoundError, "final refit is still pending"),
                ("unrecognised", ValueError, "Unknown forecast method"),
            ):
                with self.subTest(method=method):
                    comparison.write_text(json.dumps({"selected_method": method}), encoding="utf-8")
                    with self.assertRaisesRegex(exception, message):
                        ForecastService.load(root)


class TerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus = json.loads((ROOT / "resources/assistant_questions.json").read_text(encoding="utf-8"))
        cls.model = train_intents(corpus["train"])
        cls.model.threshold = 0.35

    def setUp(self):
        self.service = ForecastService(terminal_sales())
        self.session = TerminalSession(self.service, self.model)
        self.inputs = dict(stock=5, outstanding=0, lead_days=2, review_days=3, buffer=5)

    def test_named_products_and_daily_followups_use_same_forecast_values(self):
        self.assertIn("140.0 units", self.session.answer("Forecast for Product 2"))
        self.assertIn("210.0 units", self.session.answer("And Product 3?"))
        daily = self.session.answer("Show the daily breakdown")
        self.assertIn("Item 3", daily)
        self.assertIn("| Mon, 01 Jan 2018 | 30.0 |", daily)
        self.assertIn("focus Product 3", self.session.prompt())
        self.assertEqual(self.session.item, 1)

    def test_all_product_comparison_and_history_use_observed_data(self):
        response = self.session.answer("Compare forecast sales for all five products")
        for item, total in ((1, 70), (2, 140), (3, 210), (4, 280), (5, 350)):
            self.assertIn(f"| Product {item} | {total:.1f} |", response)
        self.assertIn("Highest total: **Product 5**", response)
        self.assertIn("Which product", self.session.answer("Show the daily breakdown"))
        self.session.select_product(2)
        self.assertIn("140 units over 7 days", self.session.answer("Show sales from the last 7 days"))

    def test_stock_instructions_refer_to_terminal_commands(self):
        response = self.session.answer("How much should I order?")
        self.assertIn("/product 1", response)
        self.assertIn("/stock", response)
        self.assertNotIn("click", response)
        self.assertNotIn("Product selector", response)
        forecast = self.session.answer("Forecast for Product 2")
        self.assertIn("show the daily breakdown", forecast)
        self.assertNotIn("forecast table", forecast)

    def test_stock_order_matches_rule_and_followup_explains_it(self):
        self.assertEqual(self.session.calculate_stock(**self.inputs).suggested_order, 50)
        response = self.session.answer("Why?")
        self.assertIn("suggested order 50 units", response)
        self.assertIn("shortage before delivery: 15.0 units", response)
        self.assertIn("50.00 forecast units + 5.00 buffer units = 55.00", response)

    def test_stock_submission_focuses_selected_product(self):
        self.session.answer("Forecast for Product 2")
        self.session.calculate_stock(**self.inputs)
        self.assertIn("Item 1: suggested order 50 units", self.session.answer("Why?"))

    def test_product_switch_clears_old_stock_and_followup_context(self):
        self.session.calculate_stock(**self.inputs)
        self.session.select_product(2)
        self.assertIsNone(self.session.stock_plan)
        self.assertEqual(self.session.conversation.items, ())
        self.assertIn("/product 2", self.session.answer("How much should I order?"))
        self.assertNotIn("suggested order 50", self.session.answer("How much should I order?"))

    def test_other_product_does_not_reuse_selected_products_stock_plan(self):
        self.session.calculate_stock(**self.inputs)
        self.session.answer("Forecast for Product 2")
        response = self.session.answer("How much should I order?")
        self.assertIn("/product 2", response)
        self.assertNotIn("suggested order 50", response)

    def test_clear_keeps_stock_but_invalid_recalculation_removes_it(self):
        self.session.calculate_stock(**self.inputs)
        self.session.clear()
        self.assertEqual(self.session.conversation.items, ())
        self.assertIn("suggested order 50", self.session.answer("How much should I order?"))
        with self.assertRaises(ValueError):
            self.session.calculate_stock(**{**self.inputs, "lead_days": 6})
        self.assertIsNone(self.session.stock_plan)

    def test_invalid_product_keeps_existing_selection_and_stock(self):
        self.session.calculate_stock(**self.inputs)
        for invalid in (0, 6, True):
            with self.subTest(product=invalid), self.assertRaises(ValueError):
                self.session.select_product(invalid)
            self.assertEqual(self.session.item, 1)
            self.assertEqual(self.session.stock_plan.suggested_order, 50)

    def run_script(self, script, args=None):
        output = io.StringIO()
        with patch("stocksense.terminal.ForecastService.load", return_value=self.service), \
             patch("stocksense.terminal.load_assistant", return_value=self.model), \
             patch("sys.stdin", io.StringIO(script)), patch("sys.stdout", output):
            code = main(args or [])
        self.assertEqual(code, 0)
        return output.getvalue()

    def test_chat_commands_retry_bad_inputs_and_cancel_without_losing_plan(self):
        output = self.run_script("/stock\n-1\n5\n0\n2\n6\n3\n5\n/stock\n/cancel\nWhy?\n/product 6\n/status\n/clear\n/unknown\n/quit\n")
        self.assertIn("Enter a whole number at least 0", output)
        self.assertIn("Enter a whole number from 1 to 5", output)
        self.assertIn("suggested order 50 units", output)
        self.assertIn("Stock entry cancelled", output)
        self.assertIn("Stock plan: calculated", output)
        self.assertIn("Choose a product number from 1 to 5", output)
        self.assertIn("Unknown command", output)
        self.assertIn("Goodbye from StockSense", output)

    def test_eof_and_one_question_exit_cleanly(self):
        self.assertIn("Goodbye from StockSense", self.run_script(""))
        answer = self.run_script("", ["--product", "2", "--question", "Show the sales forecast"])
        self.assertIn("140.0 units", answer)
        self.assertNotIn("You [", answer)

    def test_tables_are_readable_without_markdown_delimiters(self):
        result = plain_text(self.session.answer("Show the daily forecast"))
        self.assertIn("Forecast date", result)
        self.assertIn("Mon, 01 Jan 2018", result)
        self.assertNotIn("|", result)
        self.assertNotIn("**", result)


class TerminalIntegrationTests(unittest.TestCase):
    def test_module_runs_outside_project_folder_and_matches_saved_forecast(self):
        if not all(path.is_file() for path in (DATA, ASSISTANT)):
            self.skipTest("Prepare the dataset and train the assistant for integration tests.")
        service = ForecastService.load()
        expected = f"{service.forecast(2)['prediction'].sum():.1f} units"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, "-m", "stocksense.terminal", "--product", "2",
                                     "--question", "Show the sales forecast"],
                                    cwd=directory,
                                    env={**os.environ, "PYTHONPATH": str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")},
                                    capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(expected, result.stdout)
        self.assertNotIn("streamlit", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
