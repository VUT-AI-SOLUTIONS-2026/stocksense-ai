"""Run with: python -m streamlit run app.py"""
import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

from stocksense.data import ITEMS, load_sales, select_scope
from stocksense.forecasting import METHOD_LABELS, seasonal_naive_forecast
from stocksense.inventory import plan_stock
from stocksense.assistant import SUGGESTED_QUESTIONS, answer_question
from stocksense.ui import HERO, STYLES

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/prepared/store_1_items_1_to_5.csv"
MODEL = ROOT / "artifacts/forecasters/random_forest.joblib"
COMPARISON = ROOT / "artifacts/forecasters/comparison.json"
ASSISTANT = ROOT / "artifacts/assistant/intent_model.joblib"
LSTM_DIRECTORY = ROOT / "artifacts/forecasters/lstm_final"

st.set_page_config(page_title="StockSense AI", page_icon="📦", layout="wide")


@st.cache_data
def read_history(_path, modified):
    return select_scope(load_sales(_path))


@st.cache_resource
def read_model(path, modified):
    return joblib.load(path)


@st.cache_resource
def read_lstm(path, modified):
    from stocksense.lstm import LSTMForecast
    return LSTMForecast.load(path)


def metric_rows(methods):
    return [{"Method": METHOD_LABELS[key],
             "Daily MAE (units)": metrics["overall"]["mae_units"],
             "Daily RMSE (units)": metrics["overall"]["rmse_units"],
             "Weekly total MAE (units)": metrics["overall"]["weekly_total_mae_units"]}
            for key, metrics in methods.items()]


def main():
    st.markdown(STYLES, unsafe_allow_html=True)
    st.markdown(HERO, unsafe_allow_html=True)
    st.caption("Fictional retailer · Sales data: 2013–2017. Stock and supplier values are demonstration inputs.")
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
        selector, context = st.columns([1, 3])
        item = selector.selectbox("Item", ITEMS, format_func=lambda number: f"Item {number}")
        context.caption("Choose an item to update its forecast, stock plan and assistant answers.")
        cutoff = history["date"].max()
        if method == "random_forest":
            model = read_model(str(MODEL), MODEL.stat().st_mtime_ns)
            forecast = model.forecast(history, item=item, cutoff=cutoff)
            label = "Random forest"
        elif method == "lstm":
            metadata = LSTM_DIRECTORY / "metadata.json"
            if not metadata.exists():
                st.info("The selected LSTM's final refit is still pending. Complete the final evaluation setup first.")
                return
            model = read_lstm(str(LSTM_DIRECTORY), metadata.stat().st_mtime_ns)
            forecast = model.forecast(history, item=item, cutoff=cutoff)
            label = METHOD_LABELS[method]
        elif method == "weekly_seasonal_naive":
            forecast = seasonal_naive_forecast(history, item=item, cutoff=cutoff)
            label = "Repeat last week's sales"
        else:
            raise ValueError("Unknown forecast method in the saved comparison.")
    except (ValueError, OSError, KeyError, ImportError) as error:
        st.error(f"Unable to load this demonstration: {error}")
        return
    st.caption(f"Last observed day: {cutoff:%d %B %Y} · Forecast method: {label}")
    recent = history.loc[history["item"].eq(item) & history["date"].gt(cutoff - pd.Timedelta(days=28))]
    st.markdown(f"""
    <section class="ss-kpis" aria-label="Selected item summary">
      <div class="ss-kpi"><div class="ss-kpi-label">RECENT SALES</div>
        <div class="ss-kpi-value">{recent['sales'].sum():,.0f} units</div>
        <div class="ss-kpi-note">Item {item} · Last {len(recent)} observed days</div></div>
      <div class="ss-kpi"><div class="ss-kpi-label">DAILY AVERAGE</div>
        <div class="ss-kpi-value">{recent['sales'].mean():.1f} units</div>
        <div class="ss-kpi-note">Based on observed sales</div></div>
      <div class="ss-kpi"><div class="ss-kpi-label">PLANNING WINDOW</div>
        <div class="ss-kpi-value">7 days</div>
        <div class="ss-kpi-note">{forecast['date'].min():%d %b}–{forecast['date'].max():%d %b %Y}</div></div>
    </section>
    """, unsafe_allow_html=True)
    chart = recent.set_index("date")[["sales"]].rename(columns={"sales": "Observed sales"})
    chart = chart.join(forecast.set_index("date")[["prediction"]].rename(columns={"prediction": "Forecast"}), how="outer")
    with st.container(border=True, key="forecast_card"):
        st.subheader("Sales history and forecast")
        plot, summary = st.columns([1.8, 1], gap="large")
        with plot:
            st.caption("Last 28 observed days and the next seven estimates")
            st.line_chart(chart, color=["#78909c", "#0f766e"], height=350)
        with summary:
            st.metric("Forecast total for seven days", f"{forecast['prediction'].sum():.1f} units")
            table = forecast[["date", "prediction"]].copy()
            table["date"] = table["date"].dt.strftime("%a, %d %b %Y")
            st.dataframe(table.rename(columns={"date": "Date", "prediction": "Forecast units"}), hide_index=True,
                         column_config={"Forecast units": st.column_config.NumberColumn(format="%.1f")},
                         width="stretch")
        st.caption("The January 2018 forecasts have no observed outcomes in this dataset. They are estimates, not measured future accuracy.")
    planner, assistant = st.columns([1.15, 1], gap="large")
    with planner, st.container(border=True, key="planner_card"):
        st.subheader("Stock planning")
        st.caption("Enter your stock and delivery details to calculate an order. Delivery occurs after the lead-time days; zero means before forecast day one.")
        with st.form("stock_inputs"):
            left, right = st.columns(2)
            stock = left.number_input("Stock available (units)", min_value=0, value=50, step=1, key="stock")
            outstanding = right.number_input("Outstanding units", min_value=0, value=0, step=1, key="outstanding")
            lead = left.number_input("Supplier lead time (days)", min_value=0, max_value=6, value=2, step=1, key="lead")
            review = right.number_input("Review interval (days)", min_value=1, max_value=7, value=3, step=1, key="review")
            buffer = left.number_input("Buffer stock (units)", min_value=0, value=10, step=1, key="buffer")
            submitted = st.form_submit_button("Calculate suggested order", type="primary", width="stretch")
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

    with assistant, st.container(border=True, key="assistant_card"):
        st.subheader("Ask StockSense")
        st.caption("Your planning assistant. Ask about any item, or use a shortcut below. Stock answers use a calculated plan for that item.")
        if ASSISTANT.exists():
            intent_model = read_model(str(ASSISTANT), ASSISTANT.stat().st_mtime_ns)
            status, reset = st.columns([3, 1])
            status.caption(f"Answering for Item {item} unless you name another item")
            if reset.button("Clear", key="clear_chat", help="Clear this conversation", width="stretch"):
                st.session_state["chat_messages"] = []
            messages = st.session_state.setdefault("chat_messages", [])
            transcript = st.container(height=340, border=False)
            st.caption("Choose a question or type your own")
            question = None
            shortcuts = st.columns(2)
            for index, (label, prompt) in enumerate(zip(
                    ("Sales forecast", "Stock order", "Recent sales", "Model results"), SUGGESTED_QUESTIONS)):
                if shortcuts[index % 2].button(label, key=f"chat_suggestion_{index}", width="stretch"):
                    question = prompt
            typed_question = st.chat_input("Ask about sales or stock…", max_chars=500, key="question")
            question = typed_question or question
            if question:
                def context_for_item(requested_item):
                    requested_forecast = (seasonal_naive_forecast(history, item=requested_item, cutoff=cutoff)
                                          if method == "weekly_seasonal_naive"
                                          else model.forecast(history, item=requested_item, cutoff=cutoff))
                    requested_recent = history.loc[history["item"].eq(requested_item) & history["date"].gt(cutoff - pd.Timedelta(days=28))]
                    return {"forecast": requested_forecast, "recent": requested_recent}

                with st.spinner("Checking your question…"):
                    try:
                        response = answer_question(question, model=intent_model, item=item, forecast=forecast,
                                                   recent=recent, stock_plan=result, comparison=comparison,
                                                   context_for_item=context_for_item)
                    except (ValueError, OSError, KeyError, ImportError) as error:
                        response = f"I couldn't load those item results: {error}. Please check the forecast setup."
                messages.extend([{"role": "user", "text": question, "item": item},
                                 {"role": "assistant", "text": response, "item": item}])
                del messages[:-40]
            with transcript:
                if not messages:
                    with st.chat_message("assistant", avatar="📦"):
                        st.markdown("Hi! I'm StockSense. Ask me about **sales forecasts**, **stock orders**, **recent sales** or **model results**. You can name an item, such as **item 2**.")
                for message in messages:
                    with st.chat_message(message["role"], avatar="📦" if message["role"] == "assistant" else None):
                        st.markdown(message["text"])
                        if message["role"] == "assistant":
                            st.caption(f"Answered with Item {message['item']} selected · Previous answers keep their original inputs")
        else:
            st.info("Set up the assistant first: python -m scripts.train_assistant")
    if comparison:
        st.subheader("Historical model results")
        st.caption("Compare measured errors from validation and the frozen final test.")
        with st.expander("Validation comparison (2016)"):
            st.dataframe(pd.DataFrame(metric_rows(comparison["methods"])), hide_index=True)
            st.write("MAE is the average absolute forecast error in units. Smaller is better.")
            st.caption("52 complete weeks per item. Training: 2013–2015; validation: 2016. "
                       "The demonstration model is refitted through 2016. Model choice uses daily validation MAE.")
            if "lstm" not in comparison["methods"]:
                st.caption("The LSTM comparison remains pending.")
        if comparison.get("final_test"):
            with st.expander("Final evaluation (2017)"):
                st.dataframe(pd.DataFrame(metric_rows(comparison["final_test"]["methods"])), hide_index=True)
                st.caption("52 complete weeks per item: 1 January–30 December 2017. The incomplete final day is excluded. "
                           "Model choice and settings were fixed using 2016 validation before scoring this year. "
                           "Model weights stay fixed while observed history advances each week.")
        else:
            st.caption("Final 2017 evaluation is pending.")


main()
