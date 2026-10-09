# StockSense AI

A Business Analysis 3.2 project on retail sales forecasting and stock replenishment using Python.

The first coding milestone prepares data for store 1, items 1 to 5, and evaluates a weekly forecasting benchmark. The retailer is fictional; the dataset uses anonymous item IDs and historical sales from 2013 to 2017.

## Run the first milestone

Use Python 3.12. Open PowerShell in this repository, then create the environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Download the [Store Item Demand Forecasting dataset](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data), extract the archive and put `train.csv` in `data/raw/`. Use the training file because it contains actual sales. The separate Kaggle `test.csv` has no sales values.

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_data
.\.venv\Scripts\python.exe -m scripts.evaluate_forecasters
.\.venv\Scripts\python.exe -m scripts.forecast_baseline --item 1
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

If the training CSV is elsewhere, pass its path to `scripts.prepare_data --source "C:\path\to\train.csv"`.

Preparation checks required columns, missing values, whole non-negative sales, positive IDs, unique daily keys and complete daily histories. It writes the 9,130-row selected dataset to `data/prepared/` and an audit to `artifacts/data_audit.json`. Invalid files fail with an explanation; missing days are not silently replaced by zeros.

The benchmark repeats the last observed week's sales on matching weekdays. Evaluation defaults to **2016 validation**, using 52 complete seven-day forecasts per item. Results are saved to `artifacts/baseline/validation/`. Use `--period test` only when the final model choices have been fixed for the 2017 comparison.

The demonstration command predicts seven days after the latest available date. With this dataset, its default forecast covers 1-7 January 2018. These are historical benchmark estimates with unverified future outcomes, not live shop forecasts. Use `--cutoff YYYY-MM-DD` to choose an earlier history cut-off; omit `--item` to forecast all five items.

Raw data, prepared CSVs and generated outputs stay local and are ignored by Git. Each machine needs the CSV and its own environment. On this PC, the environment shares the bundled runtime's pinned NumPy and pandas versions; the installation command above creates an independent environment on another laptop.

## Next milestone

Compare random forest forecasts against the same validation weeks, then add the stock order calculation and dashboard. Keep the 2017 test scores separate from model selection.

## Documents

- [Report draft](docs/report.md)
- [Team](docs/team.md)
- [Submission checklist](docs/submission-checklist.md)
- [Prototype build plan](docs/prototype-plan.md)
- [Baseline validation results](docs/baseline-results.md)

## Working together

Track tasks on GitHub Projects. Give each task an owner, work on a branch and have another member review changes before merging.

Reference sources and keep passwords, private business data and customer records out of the repository.

## Dates

- Submission: 2 November 2026 at 23:59 on Blackboard.
- Presentations: 9–13 November 2026 on campus.
