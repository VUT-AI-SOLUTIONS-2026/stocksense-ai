# First prototype milestone

Run on 9 October 2026. Data preparation and the weekly seasonal naive benchmark are implemented. The dashboard, learned models, stock calculation and text assistant are the next stages.

## Data preparation

The source is the group's downloaded Kaggle Store Item Demand Forecasting `train.csv`. The pipeline validated 913,000 source rows and prepared 9,130 records for store 1 and items 1 to 5. Every selected item has 1,826 daily records, covering 1 January 2013 to 31 December 2017.

Checks found no missing values, repeated daily keys, negative sales or incomplete histories. Whole-number sales and positive store/item IDs are required. Invalid input fails with an explanation; missing days are not filled with zero sales.

The original source file is preserved. Its SHA-256 is `038f25690a65149c94f86ddd3deceda20c037a5cfd754cafdfc539a72992f2ed`. Detailed source and subset summaries are saved locally in `artifacts/data_audit.json`.

## Validation method

The benchmark forecasts the next seven days using sales from the matching weekdays in the last observed week. For example, the first forecast is made at the end of 31 December 2015, using 25 to 31 December to predict 1 to 7 January 2016. At each later forecast cut-off, newly observed history is available; sales inside the forecast week are not used for those predictions.

The evaluation advances seven days at a time through 2016. It scores 52 complete weeks per item: 364 daily predictions each, or 1,820 daily predictions and 260 item-week totals overall. Scored dates run from 1 January to 29 December. The final incomplete week, 30 and 31 December, is excluded consistently. Future candidate models must use these same dates for a fair comparison.

The benchmark needs no model fitting. It uses seven history days; the planned learned models will use 28. The 2017 test-year evaluation has not been run. Model and feature choices will be made using 2016 before the final comparison.

## Measured results

| Item | Daily MAE (units) | Daily RMSE (units) | Weekly total MAE (units) |
| --- | ---: | ---: | ---: |
| 1 | 5.277 | 6.599 | 17.481 |
| 2 | 9.082 | 11.430 | 28.962 |
| 3 | 7.228 | 9.043 | 21.558 |
| 4 | 5.173 | 6.608 | 13.750 |
| 5 | 4.841 | 6.159 | 12.038 |
| Overall | 6.320 | 8.217 | 18.758 |

Daily MAE is the mean absolute difference between each predicted quantity and its actual sales. RMSE gives larger errors more weight. Weekly total MAE compares the sum of the seven predictions with the actual seven-day total for each item-week, then averages those absolute differences. The overall weekly figure averages 260 item-weeks; it is not an error for the combined stock of the whole store.

An overall daily MAE of 6.320 means each daily item forecast differed from actual sales by about 6.32 units on average over these scored validation dates. It is not an accuracy percentage and does not establish savings, fewer shortages or performance for a real retailer.

Evaluation took approximately 0.35 seconds on this PC, excluding CSV loading and validation. Timing will vary by machine and should not be treated as the future dashboard's response time.

## First demonstration forecasts

The command also generated 35 forecasts, covering 1 to 7 January 2018 for all five items, using history through 31 December 2017. These are historical demonstration estimates. Their outcomes cannot be verified from the supplied Kaggle files because `test.csv` has no actual sales values.

For item 1, the seven estimates are 13, 16, 14, 19, 15, 27 and 23 units, totalling 127 units. These are benchmark predictions, not random forest outputs.

## Verification and repeatability

All 18 automated tests passed. They cover preparation, invalid quantities and dates, missing history, matching weekdays, future-sales isolation, known daily/weekly errors, leap-year boundaries, protection of the original input file and the three commands run together. The real data preparation, validation evaluation and forecast commands also completed successfully.

The tested environment is Python 3.12.14, pandas 3.0.1 and NumPy 2.3.5. The project environment on this PC shares the bundled runtime libraries; another laptop can install the pinned requirements in its own environment using the README.

Local generated files:

- `data/prepared/store_1_items_1_to_5.csv`
- `artifacts/data_audit.json`
- `artifacts/baseline/validation/metrics.json`
- `artifacts/baseline/validation/predictions.csv`
- `artifacts/baseline/demo_forecast.csv`

These are ignored by Git and can be recreated. The code and this reviewed result summary belong in the repository. See the [README](../README.md) for the run commands.

## Next step

Implement random forest forecasting with the planned past-sales and calendar features. Compare its 2016 errors on the identical complete forecast weeks. Keep the test year out of model selection, then continue with the stock order calculation and dashboard.

Method reference: Hyndman and Athanasopoulos, [Forecasting: Principles and Practice, section 5.2](https://otexts.com/fpp3/simple-methods.html), seasonal naive method. Dataset: [Kaggle Store Item Demand Forecasting](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data).
