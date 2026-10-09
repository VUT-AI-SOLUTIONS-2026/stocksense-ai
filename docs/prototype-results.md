# First working prototype

Measured on 9 October 2026. Group review and a second-laptop rehearsal are pending.

The local Streamlit application supports store 1 and items 1–5. It shows 28 days of observed sales, seven dated forecast quantities, their total and a stock-order calculator. Inputs and delivery assumptions are visible. The retailer is fictional; stock and supplier values are demonstration inputs.

## Forecast comparison

Both methods were scored on the same 1,820 daily quantities: 52 complete weeks per item, from 1 January to 29 December 2016. The incomplete final week, 30–31 December, was excluded for both. Forecasts use only sales observed by each forecast cut-off. The weights stay fixed throughout validation; observed history advances weekly.

| Method | Daily MAE (units) | Daily RMSE (units) | Weekly-total MAE (units) |
| --- | ---: | ---: | ---: |
| Repeat the last week's sales | 6.320 | 8.217 | 18.758 |
| Random forest | 4.911 | 6.596 | 19.797 |

| Item | Benchmark daily MAE | Random forest daily MAE |
| --- | ---: | ---: |
| 1 | 5.277 | 3.849 |
| 2 | 9.082 | 7.454 |
| 3 | 7.228 | 5.500 |
| 4 | 5.173 | 3.960 |
| 5 | 4.841 | 3.790 |

The random forest improves average daily error on all five items. Its overall weekly-total error is worse. Selecting it by daily MAE does not establish that it makes better stock orders. The dashboard retains the weekly-total result, and no stockout reduction or cost saving is claimed.

The random forest is the provisional demonstration method because it has lower overall daily validation MAE. The small LSTM comparison remains pending. The 2017 final test has not been scored or used to choose features or settings.

## Training and saved model

Each item has one seven-output random forest: 100 trees, maximum depth 10, minimum leaf size 3, seed 42 and one worker. There was one settings comparison, with no validation tuning search. These settings use the documented [RandomForestRegressor API](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html).

Features contain 28 sales lags, 7/14/28-day means and sine/cosine encodings of the seven target weekdays and annual positions. Calendar features are known before forecasting. A daily training window is retained only when all seven targets finish by 31 December 2015. Each item supplies 1,061 training windows. Training inputs and targets contain no 2016 or 2017 sales.

The validation models are trained on 2013–2015. A separate saved model is refitted through 31 December 2016 for demonstration after that boundary. The dashboard loads this model; it does not train on page opening. Its last 28 observed sales days are in December 2017, and its forecasts cover 1–7 January 2018. The provided dataset contains no outcomes for those seven days.

Training the five validation models took 6.077 seconds; refitting the five demonstration models took 7.635 seconds on this PC. These times exclude loading the CSV and scoring predictions and do not measure dashboard response time. Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, scikit-learn 1.9.1, Streamlit 1.65.0 and joblib 1.6.0 were used. Timing varies by machine.

Run `python -m scripts.train_forecasters` to regenerate the model and comparison. Generated files are ignored by Git; another laptop needs to run preparation and training. Read `artifacts/forecasters/comparison.json` for exact per-item errors, settings and scored dates.

## Stock calculation

Coverage is supplier lead time plus review interval, at most seven days. Forecast demand is the sum of the corresponding daily quantities. Target stock adds the buffer; inventory position adds current stock and outstanding units. Suggested order is the positive difference rounded upwards to whole units.

Outstanding units and a new order are assumed to arrive after the lead-time forecast days. A lead time of two days means arrival before day three; a lead time of zero means arrival before day one. The calculator separately compares current stock with forecast demand before that arrival. Outstanding units cannot hide a shortage that happens before delivery.

For seven daily forecasts of 10 units, stock of 20, no outstanding units, lead time two days, review interval three days and buffer five: coverage is five days, target is 55 units, and the order is 35 units. Current stock covers the first two forecast days exactly.

## Checks

All 29 automated tests passed. The stock tests include 12 independently specified calculation cases, including sufficient stock, outstanding orders, fractional forecasts, zero demand, instant delivery and shortages before delivery. Other checks cover invalid inputs, chronological training boundaries, unchanged predictions when future sales change, saved-model reproduction, equal comparison dates and dashboard interactions for all five items.

Dashboard checks use [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest). A separate Chrome preview was opened at desktop and mobile widths for layout inspection. The text assistant has since been added, bringing the suite to 37 passing tests; see [assistant results](assistant-results.md). The LSTM experiment, frozen final evaluation, response-time measurement and group rehearsal are still required before final submission.
