"""One small, univariate LSTM per item; optional Keras/PyTorch dependencies."""
from dataclasses import dataclass
from functools import lru_cache
import json
import os
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from stocksense.forecasting import calendar_date
from stocksense.random_forest import training_windows

SETTINGS = {"lookback": 28, "units": 16, "outputs": 7, "max_epochs": 50,
            "patience": 5, "batch_size": 32, "learning_rate": 0.001,
            "loss": "mse", "seed": 42, "backend": "torch", "shuffle": False}


@lru_cache(maxsize=1)
def keras_runtime():
    os.environ["KERAS_BACKEND"] = "torch"
    import torch
    import keras
    torch.set_num_threads(1)
    torch.use_deterministic_algorithms(True)
    return keras


def build_model(seed):
    keras = keras_runtime()
    keras.utils.set_random_seed(seed)
    model = keras.Sequential([keras.layers.Input((28, 1)), keras.layers.LSTM(16), keras.layers.Dense(7)])
    model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse", jit_compile=False)
    return model


def scaler_for(series, train_end):
    observed = series.loc[series["date"].le(calendar_date(train_end)), "sales"].to_numpy(dtype=float)
    if len(observed) == 0 or not np.isfinite(observed).all() or (observed < 0).any():
        raise ValueError("Scaler needs finite, non-negative training observations.")
    return float(observed.mean()), float(observed.std()) or 1.0


def sequence_windows(series, train_end):
    # The first 28 forest features are reversed lags; restore chronological order.
    x, y, cutoffs = training_windows(series, train_end)
    return x[:, :28][:, ::-1, None].astype("float32"), y.astype("float32"), cutoffs


def validation_windows(series, start="2016-01-01", end="2016-12-31"):
    start, end = calendar_date(start), calendar_date(end)
    if series["date"].duplicated().any():
        raise ValueError("Validation history contains duplicate dates.")
    indexed = series.set_index("date")["sales"]
    x, y = [], []
    for origin in pd.date_range(start, end, freq="7D"):
        if origin + pd.Timedelta(days=6) > end:
            break
        x.append(indexed.reindex(pd.date_range(origin - pd.Timedelta(days=28), periods=28)).to_numpy())
        y.append(indexed.reindex(pd.date_range(origin, periods=7)).to_numpy())
    x, y = np.asarray(x, dtype="float32"), np.asarray(y, dtype="float32")
    if not len(x) or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Complete observed validation weeks and 28-day histories are required.")
    return x[:, :, None], y


@dataclass
class LSTMForecast:
    models: dict
    scalers: dict
    train_end: pd.Timestamp
    details: dict

    def forecast(self, data, *, item, cutoff, store=1):
        cutoff = calendar_date(cutoff)
        if cutoff < self.train_end:
            raise ValueError("The forecast cut-off precedes this model's training boundary.")
        key = (store, item)
        if key not in self.models:
            raise ValueError("No LSTM is available for this store and item.")
        rows = data.loc[data["store"].eq(store) & data["item"].eq(item) & data["date"].le(cutoff)]
        if rows["date"].duplicated().any():
            raise ValueError("History contains duplicate daily records.")
        dates = pd.date_range(cutoff - pd.Timedelta(days=27), cutoff)
        values = rows.set_index("date")["sales"].reindex(dates).to_numpy(dtype="float32")
        if not np.isfinite(values).all() or (values < 0).any():
            raise ValueError("A complete 28-day history of non-negative sales is required.")
        mean, scale = self.scalers[key]
        x = ((values - mean) / scale).reshape(1, 28, 1)
        result = keras_runtime().ops.convert_to_numpy(self.models[key](x, training=False))[0]
        prediction = np.maximum(0, result.astype(float) * scale + mean)
        if not np.isfinite(prediction).all():
            raise ValueError("LSTM returned non-finite predictions.")
        return pd.DataFrame({"store": store, "item": item, "cutoff": cutoff,
                             "date": pd.date_range(cutoff + pd.Timedelta(days=1), periods=7),
                             "prediction": prediction})

    def save(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        rows = []
        for (store, item), model in self.models.items():
            filename = f"store_{store}_item_{item}.keras"
            model.save(directory / filename)
            rows.append({"store": store, "item": item, "filename": filename,
                         "mean": self.scalers[(store, item)][0], "scale": self.scalers[(store, item)][1],
                         "training": self.details[(store, item)]})
        metadata = {"train_end": str(self.train_end.date()), "settings": SETTINGS, "items": rows}
        (directory / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, directory):
        directory = Path(directory)
        metadata = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
        models, scalers, details = {}, {}, {}
        for row in metadata["items"]:
            key = (row["store"], row["item"])
            models[key] = keras_runtime().models.load_model(directory / row["filename"], compile=False)
            scalers[key] = (row["mean"], row["scale"])
            details[key] = row["training"]
        return cls(models, scalers, calendar_date(metadata["train_end"]), details)


def fit_lstm(data, *, train_end="2015-12-31", fixed_epochs=None, max_epochs=50):
    """Validation selects epochs; final refit uses those counts without test labels."""
    keras = keras_runtime()
    boundary = calendar_date(train_end)
    models, scalers, details = {}, {}, {}
    if fixed_epochs is None and boundary != calendar_date("2015-12-31"):
        raise ValueError("Validation training must finish in 2015; pass fixed epochs for refitting.")
    for (store, item), series in data.groupby(["store", "item"]):
        key = (int(store), int(item))
        mean, scale = scaler_for(series, boundary)
        x, y, _ = sequence_windows(series, boundary)
        model = build_model(SETTINGS["seed"] + int(item))
        callbacks, validation = [], None
        if fixed_epochs is None:
            vx, vy = validation_windows(series)
            validation = ((vx - mean) / scale, (vy - mean) / scale)
            callbacks = [keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True)]
            epochs = max_epochs
        else:
            epochs = int(fixed_epochs[key])
            if not 1 <= epochs <= SETTINGS["max_epochs"]:
                raise ValueError("Frozen epoch counts must be from 1 to 50.")
        print(f"Training LSTM item {item}, through {boundary.date()}, at most {epochs} epochs...", flush=True)
        started = perf_counter()
        history = model.fit((x - mean) / scale, (y - mean) / scale, validation_data=validation,
                            epochs=epochs, batch_size=32, shuffle=False, callbacks=callbacks, verbose=0)
        losses = history.history
        if not all(np.isfinite(values).all() for values in losses.values()):
            raise ValueError("LSTM training produced non-finite loss.")
        best = int(np.argmin(losses["val_loss"])) + 1 if validation is not None else epochs
        elapsed = perf_counter() - started
        details[key] = {"training_windows": len(x), "epochs_run": len(losses["loss"]), "selected_epochs": best,
                        "training_seconds": elapsed, "parameters": model.count_params(), "history": losses}
        models[key], scalers[key] = model, (mean, scale)
        print(f"Item {item}: {len(losses['loss'])} epochs, selected {best}, {elapsed:.2f}s", flush=True)
    if not models:
        raise ValueError("No series are available for LSTM training.")
    return LSTMForecast(models, scalers, boundary, details)
