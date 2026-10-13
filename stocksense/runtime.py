"""Load the saved forecasting setup used by the web and terminal interfaces."""
from dataclasses import dataclass
import json
from pathlib import Path

import joblib
import pandas as pd

from stocksense.data import ITEMS, load_sales, select_scope
from stocksense.forecasting import METHOD_LABELS, seasonal_naive_forecast

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/prepared/store_1_items_1_to_5.csv"
MODEL = ROOT / "artifacts/forecasters/random_forest.joblib"
COMPARISON = ROOT / "artifacts/forecasters/comparison.json"
ASSISTANT = ROOT / "artifacts/assistant/intent_model.joblib"
LSTM_DIRECTORY = ROOT / "artifacts/forecasters/lstm_final"


@dataclass
class ForecastService:
    history: pd.DataFrame
    comparison: dict | None = None
    method: str = "weekly_seasonal_naive"
    model: object = None

    @classmethod
    def load(cls, root=ROOT):
        root = Path(root)
        data = root / DATA.relative_to(ROOT)
        if not data.is_file():
            raise FileNotFoundError("Prepare the dataset first: python -m scripts.prepare_data")
        history = select_scope(load_sales(data))
        comparison_path = root / COMPARISON.relative_to(ROOT)
        comparison = (json.loads(comparison_path.read_text(encoding="utf-8"))
                      if comparison_path.is_file() else None)
        method = comparison["selected_method"] if comparison else "weekly_seasonal_naive"
        model = None
        if method == "random_forest":
            model_path = root / MODEL.relative_to(ROOT)
            if not model_path.is_file():
                raise FileNotFoundError("The saved forecast model is missing. Run python -m scripts.train_forecasters.")
            model = joblib.load(model_path)
        elif method == "lstm":
            directory = root / LSTM_DIRECTORY.relative_to(ROOT)
            if not (directory / "metadata.json").is_file():
                raise FileNotFoundError("The selected LSTM's final refit is still pending. Complete the final evaluation setup first.")
            from stocksense.lstm import LSTMForecast
            model = LSTMForecast.load(directory)
        elif method != "weekly_seasonal_naive":
            raise ValueError("Unknown forecast method in the saved comparison.")
        return cls(history, comparison, method, model)

    @property
    def cutoff(self):
        return self.history["date"].max()

    @property
    def label(self):
        return METHOD_LABELS[self.method]

    def forecast(self, item):
        if item not in ITEMS:
            raise ValueError("Choose a product number from 1 to 5.")
        if self.method == "weekly_seasonal_naive":
            return seasonal_naive_forecast(self.history, item=item, cutoff=self.cutoff)
        return self.model.forecast(self.history, item=item, cutoff=self.cutoff)

    def recent(self, item):
        return self.history.loc[self.history["item"].eq(item) &
                                self.history["date"].gt(self.cutoff - pd.Timedelta(days=28))]

    def context_for_item(self, item):
        return {"forecast": self.forecast(item), "recent": self.recent(item)}


def load_assistant(root=ROOT):
    path = Path(root) / ASSISTANT.relative_to(ROOT)
    if not path.is_file():
        raise FileNotFoundError("Set up the assistant first: python -m scripts.train_assistant")
    return joblib.load(path)
