# StockSense AI

A Business Analysis 3.2 project on retail sales forecasting and stock replenishment using Python.

The prototype shows sales history, a seven-day forecast and a stock-order calculation for store 1, items 1 to 5. The retailer is fictional; the dataset uses anonymous item IDs and historical sales from 2013 to 2017.

## Run the prototype

Use Python 3.12. Open PowerShell in this repository, then create the environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the [Store Item Demand Forecasting dataset](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data), extract the archive and put `train.csv` in `data/raw/`. Use the training file because it contains actual sales. The separate Kaggle `test.csv` has no sales values.

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_data
.\.venv\Scripts\python.exe -m scripts.evaluate_forecasters
.\.venv\Scripts\python.exe -m scripts.train_forecasters
.\.venv\Scripts\python.exe -m scripts.train_assistant
.\.venv\Scripts\python.exe -m scripts.forecast_baseline --item 1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If the training CSV is elsewhere, pass its path to `scripts.prepare_data --source "C:\path\to\train.csv"`.

Preparation checks required columns, missing values, whole non-negative sales, positive IDs, unique daily keys and complete daily histories. It writes the 9,130-row selected dataset to `data/prepared/` and an audit to `artifacts/data_audit.json`. Invalid files fail with an explanation; missing days are not silently replaced by zeros.

The benchmark repeats the last observed week's sales on matching weekdays. Evaluation defaults to **2016 validation**, using 52 complete seven-day forecasts per item. Results are saved to `artifacts/baseline/validation/`. Use `--period test` only when the final model choices have been fixed for the 2017 comparison.

The initial training command compares five random forests against the benchmark on those same 2016 weeks. It uses 2013–2015 targets, with 28 preceding sales days, recent averages and known calendar features. It creates a provisional comparison and a forest refitted through 2016.

To reproduce the completed deep-learning experiment and final evaluation, install the extra dependencies and run these stages in order:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-deep-learning.txt
.\.venv\Scripts\python.exe -m scripts.compare_lstm --stage validation
.\.venv\Scripts\python.exe -m scripts.compare_lstm --stage final
```

Validation adds one small LSTM per item and freezes the method and epoch counts using 2016 results. The final stage refits through 2016, then evaluates 2017 with fixed weights. Results go to `artifacts/forecasters/comparison.json` and `final-test.json`; `selection-lock.json` records the choices and dataset checksum. The scripts protect completed results against accidental retraining. On an already prepared machine, launch Streamlit directly instead of repeating training.

Random forest remains selected by daily validation MAE. Keras and PyTorch are needed to reproduce the LSTM experiment, but the selected random forest dashboard runs with the core requirements alone. See [final model results](docs/final-model-results.md) for the recorded comparison and limitations.

Open the local address printed by Streamlit, usually `http://localhost:8501`. Choose an item, inspect its history and forecast, enter demonstration stock values and calculate an order. Lead time plus review interval must fit within seven days. The calculation flags possible shortages before delivery and rounds only the final order upwards. A zero-day lead time means delivery before the first forecast day.

The dashboard forecasts 1–7 January 2018, after the last observed date. Those forecasts have unverified outcomes. Separate tables report **2016 validation** and **2017 final testing**; neither measures January 2018 accuracy or benefits for a real retailer. The comparison includes daily and weekly-total errors.

The separate baseline command also produces seven-day forecasts. Use `--cutoff YYYY-MM-DD` for an earlier cut-off; omit `--item` to forecast all five items. It remains available for checking the benchmark independently.

Raw data, prepared CSVs and generated outputs stay local and are ignored by Git. Each machine needs the CSV and its own environment. On this PC, the environment shares the bundled runtime's pinned NumPy and pandas versions; the installation command above creates an independent environment on another laptop.

## Next milestone

The [personal-PC technical rehearsal](docs/personal-pc-rehearsal.md) is complete with 45 tests passed and no skips. Continue group content review, human usability checks, signatures, Grammarly evidence and a timed presentation rehearsal. Current materials are in [submission](docs/submission/README.md). The LSTM comparison and frozen final evaluation are preserved.

## Ask StockSense

The dashboard includes a small text assistant for forecasts, replenishment, recent sales, model performance and help. It recognises the question type and retrieves the selected item's displayed results. Calculate a stock order before asking about replenishment. To ask about another item, change the Item selector first.

Try "Show the sales forecast", "How much should I order?", "Show recent sales history", "Show model performance" or "How do I get started?". Questions below the confidence threshold show supported options. Stock results persist when asking questions and are cleared when the item changes or an invalid stock calculation is submitted.

Training uses the question sets in `resources/assistant_questions.json`. The saved classifier and detailed evaluation stay in `artifacts/assistant/`. On a fresh curated check it recognised 24 of 25 supported questions and rejected 8 of 8 unrelated questions. This is a small language test; group testing with new phrasings is still needed. See [assistant results](docs/assistant-results.md).

## Documents

- [Project handover and continuation context](docs/handover.md)
- [Earlier full report source and designed drafts](docs/drafts/README.md)
- [Report draft](docs/report.md)
- [Team](docs/team.md)
- [Submission checklist](docs/submission-checklist.md)
- [Prototype build plan](docs/prototype-plan.md)
- [Baseline validation results](docs/baseline-results.md)
- [Prototype and random forest results](docs/prototype-results.md)
- [Text assistant results](docs/assistant-results.md)
- [Final forecasting comparison](docs/final-model-results.md)

## Working together

Track tasks on GitHub Projects. Give each task an owner, work on a branch and have another member review changes before merging.

The [team page](docs/team.md) links assigned GitHub issues for all ten members, reviewers and the contribution record. Credit actual contributions using the member's confirmed GitHub-linked commit email. Group review remains pending.

Reference sources and keep passwords, private business data and customer records out of the repository.

## Dates

- Submission: 2 November 2026 at 23:59 on Blackboard.
- Presentations: 9–13 November 2026 on campus.
