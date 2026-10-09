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
.\.venv\Scripts\python.exe -m scripts.forecast_baseline --item 1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If the training CSV is elsewhere, pass its path to `scripts.prepare_data --source "C:\path\to\train.csv"`.

Preparation checks required columns, missing values, whole non-negative sales, positive IDs, unique daily keys and complete daily histories. It writes the 9,130-row selected dataset to `data/prepared/` and an audit to `artifacts/data_audit.json`. Invalid files fail with an explanation; missing days are not silently replaced by zeros.

The benchmark repeats the last observed week's sales on matching weekdays. Evaluation defaults to **2016 validation**, using 52 complete seven-day forecasts per item. Results are saved to `artifacts/baseline/validation/`. Use `--period test` only when the final model choices have been fixed for the 2017 comparison.

Training compares five random forests against the benchmark on those same 2016 weeks. It uses 2013–2015 targets, with 28 preceding sales days, recent averages and known calendar features. The comparison is saved to `artifacts/forecasters/comparison.json`. A separate forest is refitted through 2016 for the demonstration; no 2017 test scores are calculated. Selection uses daily MAE and remains provisional until the LSTM comparison.

Open the local address printed by Streamlit, usually `http://localhost:8501`. Choose an item, inspect its history and forecast, enter demonstration stock values and calculate an order. Lead time plus review interval must fit within seven days. The calculation flags possible shortages before delivery and rounds only the final order upwards. A zero-day lead time means delivery before the first forecast day.

The dashboard forecasts 1–7 January 2018, after the last observed date. Those forecasts have unverified outcomes. Its error table reports **2016 validation**, not accuracy for January 2018 or a real retailer. The random forest improves daily validation MAE but has slightly worse weekly-total MAE; the comparison shows both. See [prototype results](docs/prototype-results.md).

The separate baseline command also produces seven-day forecasts. Use `--cutoff YYYY-MM-DD` for an earlier cut-off; omit `--item` to forecast all five items. It remains available for checking the benchmark independently.

Raw data, prepared CSVs and generated outputs stay local and are ignored by Git. Each machine needs the CSV and its own environment. On this PC, the environment shares the bundled runtime's pinned NumPy and pandas versions; the installation command above creates an independent environment on another laptop.

## Next milestone

Add the small LSTM comparison and text assistant, then fix model choices before the final 2017 test. Complete a second-laptop rehearsal and collect the final report, poster and presentation evidence.

## Documents

- [Report draft](docs/report.md)
- [Team](docs/team.md)
- [Submission checklist](docs/submission-checklist.md)
- [Prototype build plan](docs/prototype-plan.md)
- [Baseline validation results](docs/baseline-results.md)
- [Prototype and random forest results](docs/prototype-results.md)

## Working together

Track tasks on GitHub Projects. Give each task an owner, work on a branch and have another member review changes before merging.

The [team page](docs/team.md) links assigned GitHub issues for all ten members, reviewers and the contribution record. Credit actual contributions using the member's confirmed GitHub-linked commit email. Group review remains pending.

Reference sources and keep passwords, private business data and customer records out of the repository.

## Dates

- Submission: 2 November 2026 at 23:59 on Blackboard.
- Presentations: 9–13 November 2026 on campus.
