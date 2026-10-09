"""Run with: python -m streamlit run app.py"""
import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from stocksense.data import ITEMS, load_sales, select_scope
from stocksense.forecasting import seasonal_naive_forecast
from stocksense.inventory import plan_stock
from stocksense.assistant import answer_question

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/prepared/store_1_items_1_to_5.csv"
MODEL = ROOT / "artifacts/forecasters/random_forest.joblib"
COMPARISON = ROOT / "artifacts/forecasters/comparison.json"
ASSISTANT = ROOT / "artifacts/assistant/intent_model.joblib"

st.set_page_config(page_title="StockSense AI", page_icon="📦", layout="centered")


@st.cache_data
def read_history(_path, modified):
    return select_scope(load_sales(_path))


@st.cache_resource
def read_model(path, modified):
    return joblib.load(path)


def main():
    st.title("StockSense AI")
    st.write("Sales forecasts and simple stock planning for a fictional retailer.")
    st.info("Historical demonstration · Store 1 · Sales data: 2013–2017. Stock and supplier values are demonstration inputs.")
    if not DATA.exists():
        st.warning("Prepare the dataset first: python -m scripts.prepare_data")
        return
    try:
        history = read_history(str(DATA), DATA.stat().st_mtime_ns)
        comparison = json.loads(COMPARISON.read_text(encoding="utf-8")) if COMPARISON.exists() else None
        method = comparison["selected_method"] if comparison else "weekly_seasonal_naive"
        if method == "random_forest" and not MODEL.exists():
            st.error("The saved forecast model is missing. Run python -m scripts.train_forecasters.")
            return
        item = st.selectbox("Item", ITEMS, format_func=lambda number: f"Item {number}")
        cutoff = history["date"].max()
        if method == "random_forest":
            model = read_model(str(MODEL), MODEL.stat().st_mtime_ns)
            forecast = model.forecast(history, item=item, cutoff=cutoff)
            label = "Random forest"
        else:
            forecast = seasonal_naive_forecast(history, item=item, cutoff=cutoff)
            label = "Repeat last week's sales"
    except (ValueError, OSError, KeyError) as error:
        st.error(f"Unable to load this demonstration: {error}")
        return
    st.caption(f"Last observed day: {cutoff:%d %B %Y} · Forecast method: {label}")
    st.subheader("Sales history and forecast")
    recent = history.loc[history["item"].eq(item) & history["date"].gt(cutoff - pd.Timedelta(days=28))]
    chart = recent.set_index("date")[["sales"]].rename(columns={"sales": "Observed sales"})
    chart = chart.join(forecast.set_index("date")[["prediction"]].rename(columns={"prediction": "Forecast"}), how="outer")
    st.line_chart(chart, color=["#64748b", "#0f766e"])
    st.metric("Forecast total for seven days", f"{forecast['prediction'].sum():.1f} units")
    table = forecast[["date", "prediction"]].copy()
    table["date"] = table["date"].dt.strftime("%a, %d %b %Y")
    st.dataframe(table.rename(columns={"date": "Date", "prediction": "Forecast units"}), hide_index=True,
                 column_config={"Forecast units": st.column_config.NumberColumn(format="%.1f")})
    st.caption("The January 2018 forecasts have no observed outcomes in this dataset. They are estimates, not measured future accuracy.")
    st.subheader("Stock planning")
    st.write("Outstanding units and an order placed today arrive after the lead-time days. A zero-day lead time means arrival before the first forecast day.")
    with st.form("stock_inputs"):
        left, right = st.columns(2)
        stock = left.number_input("Stock available (units)", min_value=0, value=50, step=1, key="stock")
        outstanding = right.number_input("Outstanding units", min_value=0, value=0, step=1, key="outstanding")
        lead = left.number_input("Supplier lead time (days)", min_value=0, max_value=6, value=2, step=1, key="lead")
        review = right.number_input("Review interval (days)", min_value=1, max_value=7, value=3, step=1, key="review")
        buffer = left.number_input("Buffer stock (units)", min_value=0, value=10, step=1, key="buffer")
        submitted = st.form_submit_button("Calculate suggested order")
    stock_context = (item, str(cutoff), tuple(forecast["prediction"]), stock, outstanding, lead, review, buffer)
    if st.session_state.get("stock_context") != stock_context:
        st.session_state.pop("stock_plan", None)
    if submitted:
        st.session_state.pop("stock_plan", None)
        try:
            result = plan_stock(forecast["prediction"], stock=stock, outstanding=outstanding,
                                lead_days=lead, review_days=review, buffer=buffer)
            st.session_state["stock_plan"] = result
            st.session_state["stock_context"] = stock_context
        except ValueError as error:
            st.error(str(error))
    result = st.session_state.get("stock_plan")
    if result is not None:
        st.metric("Suggested order", f"{result.suggested_order} units")
        st.write(f"Coverage: {result.coverage_days} days. Forecast demand: {result.forecast_demand:.2f} units. "
                 f"Target with buffer: {result.target_stock:.2f}. Inventory position: {result.inventory_position}.")
        st.caption("Order = round upwards max(0, target stock − stock available − outstanding units).")
        if result.shortage_before_delivery > 0:
            st.warning(f"Possible shortage before delivery: {result.shortage_before_delivery:.1f} units. "
                       "An order arriving after the lead time cannot cover this earlier shortage.")
        else:
            st.success("Current stock covers the forecast demand before the next delivery.")

    st.subheader("Ask StockSense")
    st.caption("Ask about forecasts, stock orders, recent sales, model performance or help. Answers use the selected item and the last submitted stock inputs.")
    if ASSISTANT.exists():
        intent_model = read_model(str(ASSISTANT), ASSISTANT.stat().st_mtime_ns)
        with st.form("ask_assistant"):
            question = st.text_input("Your question", placeholder="How much should I order?", max_chars=500, key="question")
            ask = st.form_submit_button("Ask")
        if ask:
            response = answer_question(question, model=intent_model, item=item, forecast=forecast,
                                       recent=recent, stock_plan=result, comparison=comparison)
            st.info(response)
    else:
        st.info("Set up the assistant first: python -m scripts.train_assistant")
    if comparison:
        with st.expander("Validation comparison (2016)"):
            rows = [{"Method": "Random forest" if key == "random_forest" else "Weekly benchmark",
                     "Daily MAE (units)": metrics["overall"]["mae_units"],
                     "Daily RMSE (units)": metrics["overall"]["rmse_units"],
                     "Weekly total MAE (units)": metrics["overall"]["weekly_total_mae_units"]}
                    for key, metrics in comparison["methods"].items()]
            st.dataframe(pd.DataFrame(rows), hide_index=True)
            st.write("MAE is the average absolute forecast error in units. Smaller is better.")
            st.caption("52 complete weeks per item. Training: 2013–2015; validation: 2016. "
                       "Demonstration model refitted through 2016. The LSTM comparison and final 2017 test are pending.")


main()
