# StockSense AI

A Python application for retail sales forecasting and stock planning, built for the VUT Business Analysis 3.2 project.

## Features

- Seven-day sales forecasts for five items.
- Sales history charts and a stock-order calculator.
- A text assistant for forecasts, stock questions and model results.

The prototype uses historical Kaggle data for one anonymous store and a fictional retail case.

## Getting started

Use Python 3.12. Download the [Store Item Demand Forecasting dataset](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data) and place `train.csv` in `data/raw/`.

Run these commands in PowerShell from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.prepare_data
.\.venv\Scripts\python.exe -m scripts.train_forecasters
.\.venv\Scripts\python.exe -m scripts.train_assistant
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open [localhost:8501](http://localhost:8501). If setup is already complete, run only the Streamlit command. Data, environments and trained models stay local. Preserve completed evaluation files.

For the LSTM comparison and final evaluation, follow the [setup and experiment notes](docs/handover.md).

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Project documents

- [Report, poster and presentation](docs/submission/README.md)
- [Model results](docs/final-model-results.md)
- [Team and contributions](docs/team.md)
- [Submission checklist](docs/submission-checklist.md)

