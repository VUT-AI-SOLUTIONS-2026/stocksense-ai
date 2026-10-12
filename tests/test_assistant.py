import json
from pathlib import Path
import unittest

import pandas as pd
from streamlit.testing.v1 import AppTest

from stocksense.assistant import ConversationContext, answer_question, requested_items, train_intents
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
            self.assertIn("Product selector", self.answer(query))
        self.assertIn("IDs 1 to 5", self.answer("Forecast for item 9"))

    def test_help_and_unsupported_questions(self):
        self.assertIn("Choose a product", self.answer("How do I get started"))
        for query in ("", "zxqv123", "Who is the president", "x"*501):
            with self.subTest(query=query):
                self.assertIn("could not match", self.answer(query))

    def test_named_item_uses_its_own_values_and_never_another_stock_plan(self):
        second = {"forecast": self.context["forecast"].assign(prediction=20),
                  "recent": self.context["recent"].assign(sales=30)}
        resolver = lambda item: second
        for query in ("Forecast for item 2", "Forecast for product two", "Forecast for item #2"):
            response = self.answer(query, context_for_item=resolver)
            self.assertIn("Item 2", response)
            self.assertIn("140.0 units", response)
        self.assertIn("300 units", self.answer("Show recent sales for item 2", context_for_item=resolver))
        plan = plan_stock([10]*7, stock=5, outstanding=0, lead_days=2, review_days=3, buffer=0)
        response = self.answer("Will I run out of item 2?", context_for_item=resolver, stock_plan=plan)
        self.assertIn("For item 2, I need stock available", response)
        self.assertNotIn("suggested order 45", response)

    def test_natural_stock_questions_and_clarification(self):
        for query in ("Will I run out of item 1?", "Do I have enough stock?", "Should I restock?"):
            self.assertIn("supplier lead time, review interval and buffer stock", self.answer(query))
        response = self.answer("zxqv123")
        self.assertIn("Are you asking about", response)
        self.assertIn("Show recent sales history", response)

    def test_run_out_answer_matches_delivery_shortage(self):
        plan = plan_stock([10]*7, stock=50, outstanding=0, lead_days=2, review_days=3, buffer=0)
        self.assertIn("covers forecast sales before delivery", self.answer("Will I run out?", stock_plan=plan))
        plan = plan_stock([10]*7, stock=0, outstanding=50, lead_days=2, review_days=3, buffer=0)
        self.assertIn("shortage before delivery: 20.0 units", self.answer("Will I run out?", stock_plan=plan))

    def test_greeting_is_local_and_does_not_swallow_a_stock_question(self):
        class NoClassifier:
            def classify(self, text):
                raise AssertionError("Greetings must not require classification")
        for query in ("hi", " Hello! ", "HEY", "Good morning."):
            response = self.answer(query, model=NoClassifier())
            self.assertIn("Welcome to StockSense AI", response)
            self.assertIn("Show the sales forecast", response)
            self.assertIn("How much should I order?", response)
        self.assertIn("28.0 units", self.answer("Hi, show the sales forecast"))

    def test_product_lists_do_not_treat_stock_quantities_as_item_ids(self):
        self.assertEqual(requested_items("Compare products one and two"), {1, 2})
        self.assertEqual(requested_items("Compare items 1, 3 and 5"), {1, 3, 5})
        self.assertEqual(requested_items("Product 2 has 50 available and 10 outstanding"), {2})
        self.assertIn("IDs 1 to 5", self.answer("Compare products 1 and 9"))

    def test_comparison_uses_each_products_values_and_reports_ties(self):
        contexts = {1: self.context, 2: {**self.context, "forecast": self.context["forecast"].assign(prediction=10)}}
        response = self.answer("Compare forecast sales for products 1 and 2", context_for_item=contexts.__getitem__)
        self.assertIn("| Product 1 | 28.0 | 4.0 |", response)
        self.assertIn("| Product 2 | 70.0 | 10.0 |", response)
        self.assertIn("Highest total: **Product 2**", response)
        self.assertIn("not order quantities", response)
        response = self.answer("Compare all products", context_for_item=lambda _: self.context)
        self.assertIn("Highest total: **Product 1, Product 2, Product 3, Product 4, Product 5**", response)
        self.assertIn("live forecasts", self.answer("Compare products 1 and 2 tomorrow", context_for_item=contexts.__getitem__))
        self.assertIn("full seven-day window", self.answer("Compare products 1 and 2 on Monday", context_for_item=contexts.__getitem__))
        conversation = ConversationContext()
        self.answer("Compare all products", context_for_item=lambda _: self.context, conversation=conversation)
        self.assertIn("Which product do you mean", self.answer("Show the daily breakdown", conversation=conversation))

    def test_comparison_refuses_mismatched_dates_and_shared_stock_orders(self):
        def different_dates(item):
            forecast = self.context["forecast"].copy()
            if item == 2:
                forecast["date"] += pd.Timedelta(days=7)
            return {**self.context, "forecast": forecast}
        response = self.answer("Compare products 1 and 2", context_for_item=different_dates)
        self.assertIn("different date ranges", response)
        response = self.answer("Compare stock orders for products 1 and 2", context_for_item=different_dates)
        self.assertIn("each product's own stock plan", response)

    def test_followups_remember_named_product_and_keep_unknown_questions_separate(self):
        conversation = ConversationContext()
        resolver = lambda item: {**self.context, "forecast": self.context["forecast"].assign(prediction=item * 10)}
        extra = dict(conversation=conversation, context_for_item=resolver)
        self.assertIn("140.0 units", self.answer("Forecast for Product 2", **extra))
        self.assertIn("could not match", self.answer("Who is the president?", **extra))
        self.answer("Hi!", **extra)
        self.assertIn("210.0 units", self.answer("And Product 3?", **extra))
        response = self.answer("Show the daily breakdown", **extra)
        self.assertIn("Item 3", response)
        self.assertIn("| Mon, 01 Jan 2018 | 30.0 |", response)
        self.assertIn("Start with a question", self.answer("And Product 2?"))

    def test_followup_to_other_product_requires_its_own_stock_inputs(self):
        conversation = ConversationContext()
        resolver = lambda _: {**self.context, "forecast": self.context["forecast"].assign(prediction=20)}
        extra = dict(conversation=conversation, context_for_item=resolver,
                     stock_plan=plan_stock([10] * 7, stock=5, outstanding=0, lead_days=2, review_days=3, buffer=0))
        self.answer("Forecast for Product 2", **extra)
        response = self.answer("How much should I order?", **extra)
        self.assertIn("For item 2, I need stock available", response)
        self.assertNotIn("suggested order 45", response)

    def test_daily_forecasts_peak_and_date_queries_use_existing_rows(self):
        daily = self.answer("Show the daily forecast")
        self.assertIn("| Forecast date | Units |", daily)
        self.assertIn("| Sun, 07 Jan 2018 | 7.0 |", daily)
        for query, value in (("Forecast for Monday", "1.0 units"),
                             ("Forecast for day 3", "3.0 units"),
                             ("Forecast for 2018-01-06", "6.0 units")):
            self.assertIn(value, self.answer(query))
        response = self.answer("Which is the busiest forecast day?")
        self.assertIn("highest forecast is **7.0 units**", response)
        self.assertIn("Sunday, 07 January 2018", response)
        self.assertIn("lowest forecast is **1.0 units**", self.answer("Which is the quietest day?"))
        self.assertIn("day 1 to 7", self.answer("Forecast for day 8"))
        self.assertIn("outside", self.answer("Forecast for 2018-02-01"))
        self.assertIn("cannot give a live forecast", self.answer("Forecast for tomorrow"))

    def test_recent_history_window_and_comparison_use_observed_sales(self):
        self.assertIn("70 units over 7 days", self.answer("Show sales from the last 7 days"))
        self.assertIn("I have 10 recent observed days", self.answer("Show sales from the last 30 days"))
        resolver = lambda item: {**self.context, "recent": self.context["recent"].assign(sales=item * 10)}
        response = self.answer("Compare past sales for products 1 and 2 over the last 7 days", context_for_item=resolver)
        self.assertIn("Observed sales comparison", response)
        self.assertIn("| Product 1 | 70.0 | 10.0 |", response)
        self.assertIn("| Product 2 | 140.0 | 20.0 |", response)

    def test_explanation_uses_submitted_order_and_defines_terms(self):
        plan = plan_stock([10] * 7, stock=5, outstanding=0, lead_days=2, review_days=3, buffer=5)
        conversation = ConversationContext()
        self.answer("How much should I order?", stock_plan=plan, conversation=conversation)
        response = self.answer("Why?", stock_plan=plan, conversation=conversation)
        self.assertIn("50.00 forecast units + 5.00 buffer units = 55.00", response)
        self.assertIn("= **50 units**", response)
        self.assertIn("shortage before delivery: 15.0 units", response)
        self.assertIn("extra stock", self.answer("What is buffer stock?"))
        self.assertIn("accuracy percentage", self.answer("What does MAE mean?"))
        self.assertIn("larger forecast mistakes", self.answer("Explain RMSE"))
        self.assertIn("no product prices or costs", self.answer("Which product makes the most profit?"))


class AssistantDashboardTests(unittest.TestCase):
    def setUp(self):
        required = [ROOT / "data/prepared/store_1_items_1_to_5.csv", ROOT / "artifacts/assistant/intent_model.joblib"]
        if not all(path.exists() for path in required):
            self.skipTest("Prepare the dataset and train the assistant for dashboard integration tests.")
        self.app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()

    def ask(self, question):
        self.app.chat_input(key="question").set_value(question).run()
        self.assertEqual(len(self.app.exception), 0)
        return self.app.chat_message[-1].markdown[0].value

    def test_stock_survives_question_and_item_change_clears_it(self):
        self.assertIn("Calculate suggested order", self.ask("How much should I order"))
        self.app.button[0].click().run()
        order = self.app.metric[1].value
        self.assertIn(f"suggested order {order}", self.ask("How much should I order"))
        self.assertEqual(self.app.metric[1].value, order)
        self.app.selectbox[0].set_value(2).run()
        self.assertIn("Calculate suggested order", self.ask("How much should I order"))

    def test_greeting_and_visible_examples_preserve_stock_order(self):
        self.assertEqual(self.app.button(key="chat_suggestion_0").label, "Sales forecast")
        self.app.button[0].click().run()
        order = self.app.metric[1].value
        self.assertIn("Welcome to StockSense AI", self.ask("Hi!"))
        self.assertEqual(self.app.metric[1].value, order)

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

    def test_named_item_answer_matches_its_dashboard_without_reusing_stock(self):
        self.app.button[0].click().run()
        response = self.ask("Show the sales forecast for item 2")
        self.assertEqual(self.app.selectbox[0].value, 1)
        self.assertIn("Item 2", response)
        self.assertIn("Select Product 2 to see its daily estimates", response)
        self.assertIn("For item 2, I need stock available", self.ask("Will I run out of item 2?"))
        self.app.selectbox[0].set_value(2).run()
        self.assertIn(self.app.metric[0].value, response)

    def test_conversation_shortcuts_and_clear_preserve_stock_plan(self):
        self.app.button[0].click().run()
        order = self.app.metric[1].value
        self.app.button(key="chat_suggestion_0").click().run()
        self.assertIn(self.app.metric[0].value, self.app.chat_message[-1].markdown[0].value)
        self.ask("Hi")
        self.assertEqual([message.name for message in self.app.chat_message], ["user", "assistant", "user", "assistant"])
        self.app.selectbox[0].set_value(2).run()
        self.assertIn("Product 1 was selected when asked", self.app.chat_message[1].caption[0].value)
        self.app.selectbox[0].set_value(1).run()
        self.app.button[0].click().run()
        self.app.button(key="clear_chat").click().run()
        self.assertEqual(len(self.app.chat_message), 1)
        self.assertIn("Hi! I'm StockSense", self.app.chat_message[0].markdown[0].value)
        self.assertEqual(self.app.metric[1].value, order)

    def test_daily_followups_use_named_item_and_selection_resets_memory(self):
        self.ask("Forecast for Product 2")
        response = self.ask("And Product 3?")
        self.assertIn("Item 3", response)
        daily = self.ask("Show the daily breakdown")
        self.assertIn("Item 3", daily)
        self.assertIn("| Forecast date | Units |", daily)
        self.app.selectbox[0].set_value(3).run()
        self.assertIn(self.app.metric[0].value, response)
        self.app.selectbox[0].set_value(4).run()
        self.assertIn("Item 4", self.ask("Show the sales forecast"))
        self.app.button(key="clear_chat").click().run()
        self.assertIn("Start with a question", self.ask("And Product 2?"))

    def test_comparison_shortcut_matches_selected_product_and_order_explanation(self):
        self.app.button(key="chat_suggestion_4").click().run()
        response = self.app.chat_message[-1].markdown[0].value
        selected_total = self.app.metric[0].value.replace(" units", "")
        self.assertIn(f"| Product 1 | {selected_total} |", response)
        for item in range(1, 6):
            self.assertIn(f"| Product {item} |", response)
        self.app.button[0].click().run()
        order = self.app.metric[1].value
        self.app.button(key="chat_suggestion_5").click().run()
        self.assertIn("Target =", self.app.chat_message[-1].markdown[0].value)
        self.assertIn(f"suggested order {order}", self.app.chat_message[-1].markdown[0].value)

    def test_stock_submission_focuses_selected_product_after_another_item_question(self):
        self.ask("Forecast for Product 2")
        self.app.button[0].click().run()
        response = self.ask("Why?")
        self.assertIn("Item 1: suggested order", response)
        self.assertIn(self.app.metric[1].value, response)
        self.assertIn("Target =", response)


if __name__ == "__main__":
    unittest.main()
