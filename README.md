# StockSense AI

A Python application for retail sales forecasting and stock planning, built for the VUT Business Analysis 3.2 project.

## Features

- Seven-day sales forecasts for five items.
- Sales history charts and a stock-order calculator.
- A text assistant with product comparisons, daily forecasts, follow-up questions and stock-order explanations.
- Choose a web dashboard or a standalone terminal chat using the same saved models.

The fictional retailer is Sunrise Mini Market. The prototype uses historical Kaggle data from anonymous Store 1; Product 1–5 in the app correspond to dataset Item 1–5, whose actual names are unknown.

## Run the application

Open the project folder in VS Code and select **Terminal → New Terminal**. Use PowerShell. The terminal must be in the folder containing `app.py`, `README.md` and `requirements.txt`.

If setup is already complete, choose **one** of the launch commands below. For a new PC or your first run, complete [First-time setup](#first-time-setup) first.

### Web app

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the **Local URL** printed in the terminal, usually [http://localhost:8501](http://localhost:8501). If that port is busy, use the URL actually shown. Keep the terminal open while using the app. Press **Ctrl+C** in that terminal to stop the web server.

Choose a product to see its sales chart and seven-day forecast. Enter your stock and delivery details, then click **Calculate suggested order**. Type questions in **Ask StockSense** or use its question buttons.

### Terminal chat

```powershell
.\.venv\Scripts\python.exe -m stocksense.terminal
```

Wait for the `You [Product 1]>` prompt, then type a question and press **Enter**. The terminal runs independently of the web app and displays readable tables.

| Command | What it does |
| --- | --- |
| `/product 2` | Select Product 2. Changing products resets follow-up focus and clears the previous stock plan. |
| `/stock` | Enter stock available, outstanding units, lead time, review interval and buffer stock; calculate an order. |
| `/help` | Show all commands and example questions. |
| `/status` | Show the selected product, follow-up focus and stock-plan status. |
| `/clear` | Reset follow-up focus while keeping the current product's stock plan. |
| `/quit` | Close terminal chat. `exit` or Ctrl+C also works. |

During `/stock`, press **Enter** to accept a shown example value, or type `/cancel` to stop entering details. The example values are demonstration inputs. Select the intended product with `/product N` before calculating its stock order.

To get one answer and exit:

```powershell
.\.venv\Scripts\python.exe -m stocksense.terminal --product 2 --question "Show the daily forecast"
```

### Questions to try in either version

- "Compare forecast sales for all products"
- "Forecast for Product 2", followed by "Show the daily breakdown"
- "Which is the busiest forecast day?"
- "What is buffer stock?"
- "Explain my suggested order" after calculating a stock plan

Both versions use the same saved models and sales data. Each keeps its own stock inputs and conversation state for the current session. Follow-up questions remember the last product discussed; changing the selected product or clearing the chat resets that focus. Once the local setup is ready, terminal chat needs no browser, web server or internet connection.

## First-time setup

Install **Python 3.12** with the Python launcher if it is not already installed. Run the following in PowerShell from the project folder to create the local environment and install the core packages:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Then choose the appropriate setup route:

### Moving from a PC that is already set up

GitHub contains the code and documentation. The dataset and trained models stay local, so `git clone` or `git pull` does not download them. Copy these folders from the working PC into the same locations in your new project folder:

| Folder | What it contains |
| --- | --- |
| `data/prepared/` | The prepared sales data. |
| `artifacts/forecasters/` | Saved forecasting models and the recorded model comparisons. |
| `artifacts/assistant/` | The trained question classifier. |

Recreate `.venv` on the new PC using the installation commands above. With these folders in place, use either [launch command](#run-the-application). This route preserves the group's agreed model results.

### Starting without prepared data or trained models

Download and extract the [Store Item Demand Forecasting dataset](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data). Place the extracted `train.csv` inside `data/raw/`, creating those folders if needed. The CSV is an input file; it is not a command to enter in PowerShell.

Run these commands once:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_data
.\.venv\Scripts\python.exe -m scripts.train_forecasters
.\.venv\Scripts\python.exe -m scripts.train_assistant
```

Wait for each command to finish before running the next. This creates the prepared data, the initial weekly benchmark/random forest comparison and the trained assistant. You can then launch the web app or terminal chat. The complete LSTM comparison and final 2017 evaluation require the optional steps below.

<details>
<summary>Reproduce the full model comparison on a fresh setup</summary>

After the initial training above, run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-deep-learning.txt
.\.venv\Scripts\python.exe -m scripts.compare_lstm --stage validation
.\.venv\Scripts\python.exe -m scripts.compare_lstm --stage final
```

Validation freezes model choices before final testing. Skip completed stages; preserve `selection-lock.json` and `final-test.json`. Launching either interface loads saved models; it does not require another training run. The selected random forest needs only the core packages once its saved model and comparison exist. See the [report](docs/report.md) for the experiment settings and recorded findings.

</details>

### If a launch command fails

| Message or problem | What to do |
| --- | --- |
| `.venv\Scripts\python.exe` cannot be found | Open the correct project folder and complete the environment setup above. |
| `requirements.txt` or `app.py` cannot be found | Move the terminal into the folder containing those files. |
| "Prepare the dataset first" | Copy `data/prepared/` from the working PC, or complete data preparation above. |
| A saved model or assistant is missing | Copy the corresponding `artifacts/` folder from the working PC, or complete the initial training above on a fresh setup. |

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

For group meetings, use the [editable teaching deck](docs/StockSense_AI_Team_Meeting.pptx) or its [PDF copy](docs/StockSense_AI_Team_Meeting.pdf). It covers the app, terms and models, with presenter notes and practice questions in the PowerPoint.

The images in `docs/assets/` support the report and presentation. These are review drafts for the group. The report declaration still needs every member's signature, the Grammarly results must be attached, and the group must check the final PDFs before the single Blackboard submission. The poster and slides need a group content review and a timed rehearsal.

## Team contributions

Use the [StockSense AI Projects board](https://github.com/orgs/VUT-AI-SOLUTIONS-2026/projects/1) to track work. It is linked from the repository's **Projects** tab. Organisation members can view and edit it.

The board uses **Todo**, **In Progress** and **Done**. Existing completed issues #23–31 and #41 retain their owners in Done. Issues #50–55 cover the remaining group review, signatures, Grammarly results, usability testing, rehearsal and final submission checks. Move your card to In Progress when starting, record actual work with a commit or discussion link, and move it to Done after its completion criteria are checked.

A [dated board screenshot](docs/assets/project-board-2026-10-14.png) is included with the report's evidence. The board is private to the organisation; the screenshot allows external reviewers to see the recorded status.

Morris Sambo is the primary author (`240699874@edu.vut.ac.za`). The team confirmed shared contributions; include the nine contributing teammates using the exact `Co-authored-by` trailers in `.gitmessage`. Nkambule's corrected email is `akim.nkambule@icloud.com`. Do not randomly rotate authors or treat task assignments as completed work. Each member's email must be linked to their GitHub account for profile attribution.

Use repository-local Git settings:

```powershell
git config --local user.name "Morris Sambo"
git config --local user.email "240699874@edu.vut.ac.za"
git config --local commit.template .gitmessage
```

When using `git commit -m` or `git commit -F`, append the trailers explicitly; these commands do not load the template. Use plain descriptive branch names without a `codex/` prefix. Track existing assignments in GitHub issues #23–31 and #41. Member details are in the report. Historical team and evaluation notes remain recoverable in Git at commit `8be24ad`.

