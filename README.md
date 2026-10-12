# StockSense AI

A Python application for retail sales forecasting and stock planning, built for the VUT Business Analysis 3.2 project.

## Features

- Seven-day sales forecasts for five items.
- Sales history charts and a stock-order calculator.
- A text assistant for forecasts, stock questions and model results.

The fictional retailer is Sunrise Mini Market. The prototype uses historical Kaggle data from anonymous Store 1; Product 1–5 in the app correspond to dataset Item 1–5, whose actual names are unknown.

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

To reproduce the LSTM comparison and final evaluation on a fresh setup, run these after the initial forecasting training:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-deep-learning.txt
.\.venv\Scripts\python.exe -m scripts.compare_lstm --stage validation
.\.venv\Scripts\python.exe -m scripts.compare_lstm --stage final
```

Validation freezes model choices before final testing. Skip completed stages; do not delete `selection-lock.json` or `final-test.json` to repeat training. The selected random forest dashboard needs only the core requirements once its saved model and comparison exist. See the [report](docs/report.md) for the experiment settings and recorded findings.

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Submission review files

- [Report PDF](docs/StockSense_AI_Report_Review.pdf)
- [Editable report source](docs/report.md)
- [Digital poster PDF](docs/StockSense_AI_Poster.pdf)
- [Presentation PDF](docs/StockSense_AI_Presentation_Review.pdf)
- [Editable presentation](docs/StockSense_AI_Presentation_Review.pptx)

The images in `docs/assets/` support the report and presentation. These are review drafts for the group. The report declaration still needs every member's signature, the Grammarly results must be attached, and the group must check the final PDFs before the single Blackboard submission. The poster and slides need a group content review and a timed rehearsal.

## Team contributions

Morris Sambo is the primary author (`240699874@edu.vut.ac.za`). The team confirmed shared contributions; include the nine contributing teammates using the exact `Co-authored-by` trailers in `.gitmessage`. Nkambule's corrected email is `akim.nkambule@icloud.com`. Do not randomly rotate authors or treat task assignments as completed work. Each member's email must be linked to their GitHub account for profile attribution.

Use repository-local Git settings:

```powershell
git config --local user.name "Morris Sambo"
git config --local user.email "240699874@edu.vut.ac.za"
git config --local commit.template .gitmessage
```

When using `git commit -m` or `git commit -F`, append the trailers explicitly; these commands do not load the template. Use plain descriptive branch names without a `codex/` prefix. Track existing assignments in GitHub issues #23–31 and #41. Member details are in the report. Historical team and evaluation notes remain recoverable in Git at commit `8be24ad`.

