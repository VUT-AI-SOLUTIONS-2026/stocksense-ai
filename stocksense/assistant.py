"""Recognise five question types and retrieve results from the dashboard."""
from dataclasses import dataclass
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from stocksense.forecasting import METHOD_LABELS

HELP = "Choose an item, view its seven-day forecast, then calculate a stock order. Ask about forecast sales, replenishment, recent sales or model performance."


def normalise(text):
    return re.sub(r"\b(?:item|product)\s*(?:number\s*)?\d+\b", "item", text.lower()).strip()


@dataclass
class IntentModel:
    pipeline: object
    threshold: float = 0.45

    def classify(self, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 500:
            return "unsupported"
        cleaned = normalise(text)
        vector = self.pipeline[0].transform([cleaned])
        if vector.nnz == 0:
            return "unsupported"
        probabilities = self.pipeline.predict_proba([cleaned])[0]
        if probabilities.max() < self.threshold:
            return "unsupported"
        return str(self.pipeline.classes_[int(np.argmax(probabilities))])


def train_intents(examples):
    texts = [normalise(row["text"]) for row in examples]
    labels = [row["intent"] for row in examples]
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english"),
                          LogisticRegression(C=5, random_state=42, max_iter=1000))
    model.fit(texts, labels)
    return IntentModel(model)


def answer_question(text, *, model, item, forecast, recent, stock_plan=None, comparison=None):
    """Never estimate new numbers: answers use the current dashboard objects."""
    references = re.findall(r"\b(?:item|product)\s*(?:number\s*)?(\d+)\b", text.lower())
    if references:
        requested = {int(value) for value in references}
        if not requested.issubset({1, 2, 3, 4, 5}):
            return "This demonstration supports item IDs 1 to 5. Choose one of those items."
        if requested != {item}:
            return "Choose the requested item in the Item selector, then ask again. I answer for one displayed item at a time."
    intent = model.classify(text)
    if intent == "unsupported":
        return "I could not match that question confidently. " + HELP
    if intent == "help":
        return HELP
    if intent == "forecast":
        start, end = forecast["date"].min(), forecast["date"].max()
        return (f"Item {item}: forecast sales total {forecast['prediction'].sum():.1f} units "
                f"from {start:%d %B %Y} to {end:%d %B %Y}. "
                "The daily estimates are in the forecast table. These dates have no measured outcomes in this dataset.")
    if intent == "history":
        return (f"Item {item}: observed sales total {recent['sales'].sum():.0f} units over {len(recent)} days, "
                f"from {recent['date'].min():%d %B %Y} to {recent['date'].max():%d %B %Y}. "
                f"That is {recent['sales'].mean():.1f} units per day on average.")
    if intent == "reorder":
        if stock_plan is None:
            return "Enter the stock and delivery inputs, then click Calculate suggested order before asking about replenishment."
        response = (f"Item {item}: suggested order {stock_plan.suggested_order} units for {stock_plan.coverage_days} days of coverage. "
                    f"Target stock is {stock_plan.target_stock:.2f} units and inventory position is {stock_plan.inventory_position} units.")
        if stock_plan.shortage_before_delivery > 0:
            response += (f" Possible shortage before delivery: {stock_plan.shortage_before_delivery:.1f} units. "
                         "An order arriving after the lead time cannot cover that earlier shortage.")
        return response
    if not comparison:
        return "No model comparison is available yet. Run the forecasting comparison first."
    method = comparison["selected_method"]
    metrics = comparison["methods"][method]["overall"]
    name = METHOD_LABELS[method]
    response = (f"{name}: average daily absolute error {metrics['mae_units']:.3f} units across all five items "
            f"on 2016 validation; daily RMSE {metrics['rmse_units']:.3f} and weekly-total MAE "
            f"{metrics['weekly_total_mae_units']:.3f} units. ")
    if comparison.get("final_test"):
        final = comparison["final_test"]["methods"][method]["overall"]
        response += (f"On the separate 2017 final test: daily MAE {final['mae_units']:.3f}, "
                     f"RMSE {final['rmse_units']:.3f} and weekly-total MAE {final['weekly_total_mae_units']:.3f} units. ")
    else:
        response += "The final 2017 test is pending. "
    return response + "These historical scores do not measure January 2018 forecast accuracy."
