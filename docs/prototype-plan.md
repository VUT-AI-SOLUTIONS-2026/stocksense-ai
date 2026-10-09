# StockSense AI prototype plan

Plan updated 9 October 2026. Data preparation, the weekly benchmark, random forest comparison, stock calculation and dashboard are implemented. The first working milestone is complete; the LSTM experiment, text assistant, final test and group rehearsal remain pending. See [prototype results](prototype-results.md).

## Purpose and scope

Build a small Python application that helps a fictional retailer estimate sales and plan stock orders. Use store 1 and items 1 to 5 from the downloaded Store Item Demand Forecasting dataset. Predict seven daily sales quantities per item. Keep the anonymous item IDs instead of inventing product names.

The application will run locally on a laptop. Stock and supplier information will be labelled demonstration inputs. The sales history is from 2013 to 2017, so the screen must identify this as a historical demonstration and show the forecast cut-off date.

## What the user sees

Use one Streamlit page with four clearly labelled areas:

1. **Sales history:** choose an item and view its recent daily sales.
2. **Seven-day forecast:** show dated estimates in a chart and a small table, with the total for the week.
3. **Stock planning:** enter stock available, units already ordered, supplier lead time, review interval and buffer stock. Show the suggested order and its calculation.
4. **Ask StockSense:** ask a short question about a forecast, order suggestion, sales history, model performance or help.

Use a plain background, readable text and restrained colour. Keep the interface focused on these tasks. A login system, database, separate web frontend, cloud deployment and supplier integration are outside the first build.

## Build order

| Stage | Work | Evidence that it is complete |
| --- | --- | --- |
| 1. Prepare the data | Validate the source columns, dates and quantities. Select the five items, sort their histories and reproduce the data audit. | The subset contains 9,130 daily rows, with complete histories and no duplicate keys. |
| 2. Establish the forecast benchmark | Implement a weekly seasonal naive forecast: use the last week's sales on the corresponding weekdays. | Seven correctly dated predictions per item and recorded validation errors. |
| 3. Train and compare models | Add random forest regression and a small LSTM experiment. Compare them with the benchmark on the same dates. | Saved model settings, MAE, RMSE, weekly total error and training time. |
| 4. Calculate stock orders | Turn the forecast and demonstration stock inputs into a suggested order. Check delivery assumptions and invalid inputs. | At least 10 meaningful calculation cases, including sufficient stock and a possible shortage before delivery. |
| 5. Build the dashboard | Connect history, forecast and stock calculation to one page. Load saved models rather than train when the page opens. | A working demonstration for all five items, with clear dates and explanations. |
| 6. Add the text assistant | Train a small intent classifier and retrieve the dashboard's actual results. | A held-out question test and responses that match the displayed quantities. |
| 7. Rehearse and record evidence | Run on another member's laptop, review the interface and collect screenshots and test outcomes. | Reproducible setup instructions, measured response time, review results and a backup demonstration recording. |

Stage 3 begins with random forest. The dashboard and order calculation can proceed once that comparison is working; the LSTM experiment can be completed before the final evaluation. The first working milestone is sales history, a seven-day forecast and an order suggestion. The assistant follows that milestone.

## Forecasting and evaluation decisions

- Use 2013 to 2015 for training, 2016 for validation and 2017 for final testing. Keep the test year out of feature and model selection.
- Each learned forecast uses the preceding 28 days of sales. Include recent averages and calendar features for random forest. Use one small model per item, with seven outputs.
- Start random forest with the settings proposed in the report. Limit tuning to a few validation comparisons.
- Keep the deep learning experiment small: one 16-unit LSTM and a seven-output layer per item, at most 50 epochs and validation-based early stopping. Fit scalers on training data only.
- Reject training windows whose seven target dates cross the training boundary. Later validation and test forecasts may use history observed before their own cut-off.
- Choose the dashboard method using validation results. If a learned model does not improve on the benchmark, retain the benchmark and report the comparison honestly.
- Fix the choices, refit through 2016 and score seven-day forecast windows through 2017, advancing seven days at a time. Freeze model parameters during that evaluation. Exclude the final incomplete week consistently.
- Report MAE and RMSE by item and overall, plus error in the seven-day total. Record exact scored dates and sample counts. Apply the same non-negative prediction rule during evaluation and display.
- Kaggle's 2018 test file has no actual sales and cannot provide local accuracy scores. A demonstration forecasting beyond 31 December 2017 must not claim measured accuracy for those future dates.

A failure to beat the baseline is a result to explain, not a reason to invent an improvement or repeatedly tune on the test year.

## Stock calculation

The coverage period is supplier lead time plus the review interval, limited to seven days. Target stock is the sum of forecast sales across that period plus the buffer. Inventory position is stock available plus outstanding units due within that period.

Suggested order = round upwards the greater of zero and target stock minus inventory position.

For the first version, assume the outstanding units arrive with the next scheduled delivery, after the entered lead time. State that assumption on screen. Compare forecast sales before that delivery with stock currently available to flag a possible shortage. An order placed today cannot fix a shortage that occurs before it arrives.

Reject negative inputs and unsupported coverage periods. Use decimals for forecast accuracy and round only the final suggested order upwards to whole units. This is a demonstration planning rule; it does not establish savings or actual reductions in stockouts.

## Text assistant

Support five request types: forecast, reorder, history, performance and help. Use TF-IDF with a small classifier and validate any item number separately. Use different phrasings in training, validation and test sets rather than splitting copies of the same sentence across sets.

For example, "Show the forecast for item 2" retrieves seven estimates and their total. "What should I order for item 3?" uses the entered stock information; missing inputs trigger a request to supply them. Unsupported questions show a clarification or the supported options.

Aim for at least 20 correct classifications out of 25 held-out in-scope questions, and separately record how unsupported questions are handled. Test whether the answer matches the same underlying result used by the dashboard. Do not connect a paid external language service for this prototype.

## Proposed code structure

Create these files as each stage needs them. Avoid empty modules and unnecessary scaffolding.

```text
app.py                     Streamlit page
stocksense/
    __init__.py
    data.py                Validation and history preparation
    forecasting.py         Forecast methods and saved-model loading
    inventory.py           Stock calculation
    assistant.py           Intent recognition and answer retrieval
scripts/
    train_forecasters.py   Baseline, random forest and LSTM comparison
    evaluate_forecasters.py
    train_assistant.py
tests/                     Data boundaries, calculations and output consistency
requirements.txt           Reproducible Python dependencies
data/                      Local CSV files, ignored by Git
artifacts/                 Local models and evaluation outputs, ignored by Git
docs/                      Report, evidence and setup instructions
```

Use pandas, NumPy, scikit-learn and Streamlit for the core application. Use Keras with its supported local backend for the LSTM experiment. Confirm installation on the demonstration laptop and record versions when implementation begins. Model training happens in scripts; the application loads the resulting files.

Keep raw data and generated model files out of Git commits. Provide the dataset source, preparation steps and a separate local demonstration bundle so another laptop can reproduce the run. Put reviewed result summaries and selected screenshots in the documentation.

## Group work

The [team page](team.md) links an assigned GitHub issue for each member, with expected evidence and a reviewer. Members should confirm or exchange tasks. Add the issues to GitHub Projects to track progress. One member integrates the parts and checks that the report uses the same scope, calculations and measured results. Everyone should be able to explain the demonstration.

## Proposed checkpoints

These dates are planning targets to confirm with the group:

- By 16 October: data preparation, benchmark, first random forest comparison and stock calculation working.
- By 23 October: dashboard, LSTM experiment and assistant connected.
- By 26 October: final evaluation, application checks and second-laptop rehearsal complete.
- By 29 October: report updated with measured results; poster and presentation prepared from the working prototype.
- By 1 November: group review, signatures, Grammarly evidence and final PDF inspection complete.
- Submit on Blackboard by 2 November 2026 at 23:59.

## Completion criteria

The demonstration must work for all five items, display seven dated estimates and show a correct order calculation from stated inputs. It must handle invalid quantities and unsupported questions clearly. The assistant must use the same results as the dashboard. Record measured forecast errors, classifier results and response time rather than assume the targets were achieved.

Collect at least three useful screenshots: sales and forecast, stock recommendation, and assistant response. Update the report's proposed wording to describe what was actually implemented, including limitations. Create the poster and slides from that final evidence.
