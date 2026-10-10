# StockSense AI digital poster source

Retail sales forecasting and stock planning. VUT AI Solutions, Business Analysis 3.2, AIBUY3A.

## A fictional retail case

A manager needs a consistent estimate before ordering. The local Python application shows seven daily sales forecasts, a transparent stock suggestion and a five-intent text assistant. Scope: store 1, items 1-5, anonymous Kaggle sales from 2013-2017. Strict validation selects 9,130 rows.

## Measured historical comparison

| Method | 2017 daily MAE | Daily RMSE | Weekly-total MAE |
| --- | ---: | ---: | ---: |
| Weekly benchmark | 6.273 | 8.218 | 18.427 |
| Random forest | 4.812 | 6.387 | 17.973 |
| Small LSTM | 5.411 | 7.261 | 17.343 |

Errors in units. Random forest has about 23.3% lower final daily MAE than the benchmark. LSTM has lower overall weekly-total error. Selection used 2016 daily MAE and stayed frozen before final testing.

## Transparent stock planning

Coverage is lead time plus review interval, up to seven days. Target stock is forecast sales over coverage plus buffer. Suggested order is round upwards max(0, target - stock - outstanding). A separate warning checks possible shortages before delivery.

## Verified evidence and limits

45 automated tests passed on the personal PC, including all five items and stock checks. The assistant recognised 24/25 supported requests and rejected 8/8 unrelated questions in a small curated fresh test.

Historical demonstration only. January 2018 estimates have no observed outcomes. No real savings or stockout reduction has been established. Stock and supplier inputs are demonstration assumptions.

Source: Kaggle Store Item Demand Forecasting and the local frozen evaluation, 10 October 2026. Group content review remains pending.
