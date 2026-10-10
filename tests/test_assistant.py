import json
from pathlib import Path
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from stocksense.assistant import answer_question, train_intents
from stocksense.inventory import plan_stock

ROOT = Path(__file__).resolve().parents[1]


class AssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        corpus = json.loads((ROOT / "resources/assistant_questions.json").read_text())
        cls.model = train_intents(corpus["train"])
        cls.model.threshold = 0.35

    def setUp(self):
        self.context = dict(model=self.model, item=1,
                            forecast=pd.DataFrame({"date": pd.date_range("2018-01-01", periods=7), "prediction": range(1, 8)}),
                            recent=pd.DataFrame({"date": pd.date_range("2017-12-22", periods=10), "sales": [10]*10}))

    def answer(self, text, **extra):
        return answer_question(text, **{**self.context, **extra})

    def test_forecast_uses_passed_values_and_dates(self):
        response = self.answer("Show the sales forecast")
        self.assertIn("28.0 units", response)
        self.assertIn("01 January 2018", response)
        self.assertIn("07 January 2018", response)
        changed = self.context["forecast"].assign(prediction=10)
        self.assertIn("70.0 units", self.answer("Show the sales forecast", forecast=changed))

    def test_history_uses_observed_rows(self):
        response = self.answer("Show recent sales history")
        self.assertIn("100 units over 10 days", response)
        self.assertIn("10.0 units per day", response)

    def test_reorder_needs_inputs_and_matches_calculator(self):
        self.assertIn("Calculate suggested order", self.answer("How much should I order"))
        plan = plan_stock([10]*7, stock=5, outstanding=0, lead_days=2, review_days=3, buffer=0)
        response = self.answer("How much should I order", stock_plan=plan)
        self.assertIn("suggested order 45 units", response)
        self.assertIn("shortage before delivery: 15.0 units", response)

    def test_performance_identifies_validation_and_uses_saved_metrics(self):
        comparison = {"selected_method": "random_forest", "methods": {"random_forest": {"overall": {
            "mae_units": 4.911, "rmse_units": 6.596, "weekly_total_mae_units": 19.797}}}}
        response = self.answer("Show model performance", comparison=comparison)
        for value in ("4.911", "6.596", "19.797", "2016 validation", "all five items"):
            self.assertIn(value, response)
        self.assertIn("No model comparison", self.answer("Show model performance"))

    def test_final_metrics_are_distinct_from_validation(self):
        comparison = {"selected_method": "lstm", "methods": {"lstm": {"overall": {
            "mae_units": 4, "rmse_units": 5, "weekly_total_mae_units": 10}}},
            "final_test": {"methods": {"lstm": {"overall": {
                "mae_units": 6, "rmse_units": 7, "weekly_total_mae_units": 20}}}}}
        response = self.answer("Show model performance", comparison=comparison)
        for value in ("Small LSTM", "2016 validation", "2017 final test", "daily MAE 6.000", "20.000"):
            self.assertIn(value, response)
        self.assertNotIn("pending", response)

    def test_other_items_do_not_use_current_stock_or_forecast(self):
        for query in ("Forecast for item 2", "Forecast for item 1 and item 2"):
            self.assertIn("Item selector", self.answer(query))
        self.assertIn("IDs 1 to 5", self.answer("Forecast for item 9"))

    def test_help_and_unsupported_questions(self):
        self.assertIn("Choose an item", self.answer("How do I get started"))
        for query in ("", "zxqv123", "Who is the president", "x"*501):
            with self.subTest(query=query):
                self.assertIn("could not match", self.answer(query))


class AssistantDashboardTests(unittest.TestCase):
    def setUp(self):
        required = [ROOT / "data/prepared/store_1_items_1_to_5.csv", ROOT / "artifacts/assistant/intent_model.joblib"]
        if not all(path.exists() for path in required):
            self.skipTest("Prepare the dataset and train the assistant for dashboard integration tests.")
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    def ask(self, question):
        self.app.text_input(key="question").set_value(question)
        self.app.button[1].click().run()
        self.assertEqual(len(self.app.exception), 0)
        return self.app.info[-1].value

    def test_stock_survives_question_and_item_change_clears_it(self):
        self.assertIn("Calculate suggested order", self.ask("How much should I order"))
        self.app.button[0].click().run()
        order = self.app.metric[1].value
        self.assertIn(f"suggested order {order}", self.ask("How much should I order"))
        self.assertEqual(self.app.metric[1].value, order)
        self.app.selectbox[0].set_value(2).run()
        self.assertIn("Calculate suggested order", self.ask("How much should I order"))

    def test_forecast_answer_matches_display_and_invalid_order_clears_old_result(self):
        total = self.app.metric[0].value
        self.assertIn(total, self.ask("Show the sales forecast"))
        self.app.button[0].click().run()
        self.app.number_input(key="lead").set_value(6)
        self.app.number_input(key="review").set_value(3)
        self.app.button[0].click().run()
        self.assertIn("Calculate suggested order", self.ask("How much should I order"))

    def test_recorded_final_comparison_and_answer(self):
        comparison_path = ROOT / "artifacts/forecasters/comparison.json"
        if not comparison_path.exists():
            self.skipTest("Run the forecast comparison first.")
        comparison = json.loads(comparison_path.read_text())
        if not comparison.get("final_test"):
            self.skipTest("Complete the frozen final evaluation first.")
        self.assertEqual([e.label for e in self.app.expander],
                         ["Validation comparison (2016)", "Final evaluation (2017)"])
        for table in self.app.dataframe[1:]:
            self.assertEqual(len(table.value), 3)
        response = self.ask("Show model performance")
        selected = comparison["selected_method"]
        mae = comparison["final_test"]["methods"][selected]["overall"]["mae_units"]
        self.assertIn(f"daily MAE {mae:.3f}", response)
        self.assertIn("2017 final test", response)


if __name__ == "__main__":
    unittest.main()
