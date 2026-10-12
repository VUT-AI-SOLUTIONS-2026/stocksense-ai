"""Recognise five topics and answer planning questions from dashboard data."""
from dataclasses import dataclass
import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from stocksense.forecasting import METHOD_LABELS

HELP = ("Choose a product, view its seven-day forecast, then calculate a stock order. "
        "I can compare products, show daily forecasts, find the busiest forecast day, "
        "explain an order and summarise recent sales or model results. "
        "After an answer, try 'and Product 2?' or 'explain that'.")
SUGGESTED_QUESTIONS = (
    "Show the sales forecast",
    "How much should I order?",
    "Show recent sales history",
    "Show model performance",
    "Compare forecast sales for all five products",
    "Explain my suggested order",
)


ITEM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
ITEM_TOKEN = r"(?:\d+|one|two|three|four|five)"
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
DEFINITIONS = {
    "buffer stock": "Buffer stock is extra stock you add above forecast demand to allow for uncertainty. This demo uses the number you enter.",
    "lead time": "Supplier lead time is the number of forecast days before the delivery arrives. A two-day lead means it arrives after the first two forecast days.",
    "review interval": "The review interval is the number of days between stock reviews. Lead time plus review interval sets the coverage period, up to seven days here.",
    "outstanding units": "Outstanding units are units already ordered and expected to arrive. The calculator counts them in inventory position, but not as stock available before delivery.",
    "inventory position": "Inventory position is stock available plus outstanding units. The calculator subtracts it from target stock to suggest a new order.",
    "coverage": "Coverage is supplier lead time plus review interval. The target covers forecast demand during those days, plus your buffer stock.",
    "mae": "MAE is mean absolute error: the average size of a forecast mistake in units, regardless of direction. Lower is better. It is not an accuracy percentage.",
    "rmse": "RMSE is root mean squared error. It gives larger forecast mistakes more weight than MAE. Lower is better, and the score uses units sold.",
    "random forest": "Random forest combines predictions from decision trees. In this project it uses past sales and calendar features, and won the daily validation comparison.",
    "lstm": "The small LSTM learns sales sequences from 28 past days and predicts seven days. It had the lowest overall weekly-total error on the final test.",
}


@dataclass
class ConversationContext:
    """Only remember the last successful data question and its product IDs."""
    items: tuple = ()
    intent: str | None = None

    def remember(self, items, intent):
        self.items = tuple(items)
        self.intent = intent


def requested_items(text):
    """Read explicit item references without treating stock quantities as IDs."""
    pattern = (rf"\b(?:items?|products?)\s*(?:number\s*|#\s*)?"
               rf"({ITEM_TOKEN}(?:\s*(?:,|and|&)\s*(?:(?:items?|products?)\s*)?"
               rf"(?:#\s*)?{ITEM_TOKEN})*)\b")
    groups = re.findall(pattern, text.lower())
    references = [value for group in groups for value in re.findall(ITEM_TOKEN, group)]
    return {ITEM_WORDS[value] if value in ITEM_WORDS else int(value) for value in references}


def question_intent(text, model):
    """Handle common stock phrases and retain the trained classifier."""
    cleaned = text.lower()
    if re.search(r"\b(?:weather|football|poem|recipe|president|password|flight|planet)\b", cleaned):
        return "unsupported"
    if re.search(r"\b(?:run out|running out|stockout|stock out|enough stock|restock|replenish|reorder|stock orders?|suggested order|recommended order)\b", cleaned):
        return "reorder"
    if re.search(r"\b(?:model results|model performance|model comparison|mae|rmse|validation|final test)\b", cleaned):
        return "performance"
    if re.search(r"\b(?:history|historical|observed|previous|past|recent|actually sold|last week|last month|last \d+ days)\b", cleaned) and re.search(r"\b(?:sales|sold|demand|units)\b", cleaned):
        return "history"
    if (is_comparison(text) or re.search(r"\b(?:daily breakdown|each day|busiest day|quietest day|forecast day)\b", cleaned)):
        return "forecast"
    intent = model.classify(text)
    if intent != "unsupported":
        return intent
    if re.search(r"\b(?:sales forecast|forecast sales|predicted sales|sales prediction)\b", cleaned) or (requested_items(text) and re.search(r"\bforecast\b", cleaned)):
        return "forecast"
    if re.search(r"\b(?:sales history|recent sales|past sales)\b", cleaned):
        return "history"
    return "unsupported"


def is_comparison(text):
    """A comparison needs both comparison language and a product subject."""
    cleaned = text.lower()
    products = re.search(r"\b(?:items?|products?)\b", cleaned)
    comparison = re.search(r"\b(?:compare|comparison|rank|highest|lowest|most|least|best selling|more|less)\b", cleaned)
    return bool(products and (comparison or re.search(r"\ball\b", cleaned)))


def follow_up(text):
    cleaned = text.lower().strip().rstrip("?.! ")
    if re.fullmatch(r"(?:why(?: \d+(?:\.\d+)? units)?|explain that|explain it|how was that calculated|how did you calculate that)", cleaned):
        return True
    return bool(requested_items(text) and re.fullmatch(
        r"(?:and|what about|how about|same for|do the same for)\s+(?:for\s+)?(?:item|product).*", cleaned))


def definitions(text):
    cleaned = text.lower()
    if not (re.search(r"\b(?:explain|define|meaning|mean)\b", cleaned) or
            re.match(r"\s*what (?:is|are) (?:the |a )?(?:buffer stock|lead time|supplier lead time|review interval|outstanding units|inventory position|coverage|mae|rmse|random forest|lstm)\b", cleaned)):
        return None
    found = [value for term, value in DEFINITIONS.items()
             if re.search(r"\b" + re.escape(term) + r"\b", text.lower())]
    return "\n\n".join(found) if found else None


def history_window(text, recent):
    match = re.search(r"\b(?:last|past|recent)\s+(\d+|seven|fourteen)\s+days\b", text.lower())
    if match:
        word = match.group(1)
        days = {"seven": 7, "fourteen": 14}.get(word, int(word) if word.isdigit() else 0)
    elif "last week" in text.lower() or "past week" in text.lower():
        days = 7
    else:
        return recent
    if not 1 <= days <= len(recent):
        raise ValueError(f"I have {len(recent)} recent observed days here. Ask for 1 to {len(recent)} days.")
    cutoff = recent["date"].max() - pd.Timedelta(days=days)
    return recent.loc[recent["date"].gt(cutoff)]


def forecast_answer(text, item, forecast, other_item):
    cleaned = text.lower()
    start, end = forecast["date"].min(), forecast["date"].max()
    if re.search(r"\b(?:tomorrow|today|next month)\b", cleaned):
        return (f"This is a historical demonstration. Item {item}'s forecast covers {start:%d %B %Y} "
                f"to {end:%d %B %Y}, so I cannot give a live forecast for today or tomorrow. "
                "Ask for a weekday in that window or the first forecast day.")
    days = re.search(r"\b(?:next|coming|for)\s+(\d+)\s+days\b", cleaned)
    if days and int(days.group(1)) != 7:
        return "This prototype forecasts seven days only. Ask for the seven-day forecast or a day in that window."
    selected = forecast
    explicit_date = re.search(r"\b\d{4}-\d{2}-\d{2}\b", cleaned)
    day_number = re.search(r"\bday\s+(\d+)\b", cleaned)
    ordinal = re.search(r"\b(first|second|third|fourth|fifth|sixth|seventh|last)\s+(?:forecast\s+)?day\b", cleaned)
    weekday = next((day for day in WEEKDAYS if re.search(r"\b" + day + r"\b", cleaned)), None)
    if explicit_date:
        try:
            requested_date = pd.Timestamp(explicit_date.group())
        except ValueError:
            return "That date is not valid. Use a date in the forecast window, for example YYYY-MM-DD."
        selected = forecast.loc[forecast["date"].eq(requested_date)]
    elif day_number or ordinal:
        number = int(day_number.group(1)) if day_number else (
            ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "last").index(ordinal.group(1)) + 1)
        if ordinal and ordinal.group(1) == "last":
            number = len(forecast)
        if not 1 <= number <= len(forecast):
            return "Ask for forecast day 1 to 7."
        selected = forecast.sort_values("date").iloc[[number - 1]]
    elif weekday:
        selected = forecast.loc[forecast["date"].dt.day_name().str.lower().eq(weekday)]
    if selected.empty:
        return f"That day is outside Item {item}'s forecast window ({start:%d %B %Y} to {end:%d %B %Y})."
    period = f"from {start:%d %B %Y} to {end:%d %B %Y}"
    if len(selected) == 1:
        row = selected.iloc[0]
        response = f"Item {item}: forecast for {row['date']:%A, %d %B %Y} is **{row['prediction']:.1f} units**."
    elif re.search(r"\b(?:busiest|highest|peak|most|quietest|lowest|least)\b", cleaned) and re.search(r"\b(?:day|date)\b", cleaned):
        lowest = bool(re.search(r"\b(?:quietest|lowest|least)\b", cleaned))
        extreme = forecast["prediction"].min() if lowest else forecast["prediction"].max()
        dates = ", ".join(f"{value:%A, %d %B %Y}" for value in forecast.loc[forecast["prediction"].eq(extreme), "date"])
        response = f"Item {item}: {'lowest' if lowest else 'highest'} forecast is **{extreme:.1f} units** on {dates}."
    else:
        response = (f"Item {item}: forecast sales total {forecast['prediction'].sum():.1f} units {period}. "
                    f"That is {forecast['prediction'].mean():.1f} units per day on average.")
        if re.search(r"\b(?:daily|breakdown|each day|by day|dates|table)\b", cleaned):
            rows = "\n".join(f"| {row.date:%a, %d %b %Y} | {row.prediction:.1f} |" for row in forecast.sort_values("date").itertuples())
            response += "\n\n| Forecast date | Units |\n| --- | ---: |\n" + rows
        else:
            response += (f" Select Product {item} to see its daily estimates in the forecast table."
                         if other_item else " The daily estimates are in the forecast table.")
    return response + "\n\nThese dates have no measured outcomes in this dataset."


def compare_items(text, *, items, intent, context_for_item):
    rows = []
    periods = set()
    for item in items:
        context = context_for_item(item)
        values = context["forecast"] if intent == "forecast" else history_window(text, context["recent"])
        quantity = "prediction" if intent == "forecast" else "sales"
        periods.add((values["date"].min(), values["date"].max(), len(values)))
        rows.append((item, float(values[quantity].sum()), float(values[quantity].mean())))
    if len(periods) != 1:
        return "These products have different date ranges. Choose matching periods before comparing their totals."
    start, end, _ = next(iter(periods))
    if intent == "forecast":
        cleaned = text.lower()
        if re.search(r"\b(?:tomorrow|today|next month)\b", cleaned):
            return (f"This is a historical demonstration. Forecast comparisons cover {start:%d %B %Y} "
                    f"to {end:%d %B %Y}; live forecasts for today or tomorrow are not available.")
        days = re.search(r"\b(?:next|coming|for)\s+(\d+)\s+days\b", cleaned)
        if days and int(days.group(1)) != 7:
            return "This prototype compares seven-day forecasts only."
        if (any(re.search(r"\b" + day + r"\b", cleaned) for day in WEEKDAYS) or
                re.search(r"\b(?:day\s+\d+|\d{4}-\d{2}-\d{2}|(?:first|last) forecast day)\b", cleaned)):
            return "Product comparisons use the full seven-day window. Ask for the daily forecast of one product to see individual dates."
    label = "Forecast" if intent == "forecast" else "Observed"
    response = f"**{label} sales comparison**, {start:%d %B %Y} to {end:%d %B %Y}.\n\n"
    response += "| Product | Total units | Average per day |\n| --- | ---: | ---: |\n"
    response += "\n".join(f"| Product {item} | {total:.1f} | {average:.1f} |" for item, total, average in rows)
    maximum = max(total for _, total, _ in rows)
    highest = ", ".join(f"Product {item}" for item, total, _ in rows if total == maximum)
    response += f"\n\nHighest total: **{highest}**, {maximum:.1f} units."
    if intent == "forecast":
        response += " These are estimates, not order quantities. Each product needs its own stock inputs."
    return response


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


def answer_question(text, *, model, item, forecast, recent, stock_plan=None, comparison=None,
                    context_for_item=None, conversation=None):
    """Never estimate new numbers: answers use the current dashboard objects."""
    if not isinstance(text, str) or not text.strip() or len(text) > 500:
        return "I could not match that question. Try: " + "; ".join(SUGGESTED_QUESTIONS) + "."
    if re.fullmatch(r"(?:hi|hello|hey|good morning|good afternoon|good evening)[\s!.?]*", text.strip(), re.IGNORECASE):
        return ("Hi! Welcome to StockSense AI. " + HELP + " Try: "
                + "; ".join(SUGGESTED_QUESTIONS) + ".")
    definition = definitions(text)
    if definition:
        return definition
    if re.search(r"\b(?:price|prices|revenue|profit|profits|cost savings)\b", text.lower()):
        return "This dataset records sales in units. It has no product prices or costs, so I cannot calculate revenue, profit or real savings. I can compare unit sales instead."
    conversation = conversation if conversation is not None else ConversationContext()
    requested = requested_items(text)
    if requested:
        if not requested.issubset({1, 2, 3, 4, 5}):
            return "This demonstration supports item IDs 1 to 5. Choose one of those items."
    if follow_up(text):
        if conversation.intent is None:
            return "Start with a question about forecasts, stock orders, recent sales or model results. Then I can follow 'and Product 2?' or 'explain that'."
        intent = conversation.intent
    else:
        intent = question_intent(text, model)
    if intent == "unsupported":
        return "I could not match that question confidently. Are you asking about sales forecasts, stock orders, recent sales or model results? Try: " + "; ".join(SUGGESTED_QUESTIONS) + "."
    if intent == "help":
        return HELP
    if is_comparison(text):
        if intent not in {"forecast", "history"}:
            return "I can compare forecast or recent unit sales across products. For stock orders, calculate each product's own stock plan."
        items = sorted(requested) if requested else list(range(1, 6))
        if len(items) < 2:
            return "Name at least two products to compare, for example: Compare forecast sales for products 1 and 2."
        if context_for_item is None:
            return "Use the Product selector to view each product, or enable the product comparison in the dashboard."
        try:
            response = compare_items(text, items=items, intent=intent, context_for_item=context_for_item)
        except ValueError as error:
            return str(error)
        if response.startswith("**"):
            conversation.remember(items, intent)
        return response
    if len(requested) > 1:
        return "Please ask about one item at a time, for example: Show the forecast for item 2. You can also use the Product selector, or ask to compare their sales."
    if not requested and len(conversation.items) > 1 and intent in {"forecast", "history", "reorder"}:
        return "Which product do you mean? The last answer compared several products. Try: Show the daily forecast for Product 2."
    requested_item = next(iter(requested)) if requested else (
        conversation.items[0] if len(conversation.items) == 1 else item)
    other_item = requested_item != item
    if other_item:
        if context_for_item is None:
            return "Choose the requested product in the Product selector, then ask again."
        context = context_for_item(requested_item)
        item, forecast, recent = requested_item, context["forecast"], context["recent"]
        stock_plan = context.get("stock_plan")
    conversation.remember([item], intent)
    if intent == "forecast":
        if follow_up(text) and re.search(r"\b(?:why|explain|calculated|calculate)\b", text.lower()):
            return (f"Item {item}: the saved forecast method uses past sales to estimate the next seven daily quantities. "
                    f"Adding them gives {forecast['prediction'].sum():.1f} units. "
                    "The estimate does not explain why customers will buy, and these future dates have no measured outcomes in the dataset.")
        return forecast_answer(text, item, forecast, other_item)
    if intent == "history":
        try:
            recent = history_window(text, recent)
        except ValueError as error:
            return str(error)
        return (f"Item {item}: observed sales total {recent['sales'].sum():.0f} units over {len(recent)} days, "
                f"from {recent['date'].min():%d %B %Y} to {recent['date'].max():%d %B %Y}. "
                f"That is {recent['sales'].mean():.1f} units per day on average.")
    if intent == "reorder":
        if stock_plan is None:
            return (f"For item {item}, I need stock available, outstanding units, supplier lead time, review interval and buffer stock. "
                    f"Select Product {item}, enter those values in Stock planning, then click Calculate suggested order. "
                    "I won't assume that the displayed defaults are your stock details.")
        response = (f"Item {item}: suggested order {stock_plan.suggested_order} units for {stock_plan.coverage_days} days of coverage. "
                    f"Target stock is {stock_plan.target_stock:.2f} units and inventory position is {stock_plan.inventory_position} units.")
        if re.search(r"\b(?:why|explain|calculated|calculate|formula)\b", text.lower()):
            buffer = stock_plan.target_stock - stock_plan.forecast_demand
            response += (f"\n\nTarget = {stock_plan.forecast_demand:.2f} forecast units + {buffer:.2f} buffer units = {stock_plan.target_stock:.2f}. "
                         f"Order = round up max(0, {stock_plan.target_stock:.2f} minus {stock_plan.inventory_position}) "
                         f"= **{stock_plan.suggested_order} units**. Outstanding units already count in inventory position.")
        if stock_plan.shortage_before_delivery > 0:
            response += (f" Possible shortage before delivery: {stock_plan.shortage_before_delivery:.1f} units. "
                         "An order arriving after the lead time cannot cover that earlier shortage.")
        else:
            response += " Current stock covers forecast sales before delivery under these inputs; actual sales may differ."
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
