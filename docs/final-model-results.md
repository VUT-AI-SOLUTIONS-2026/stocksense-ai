# Final forecasting comparison

Measured on 10 October 2026 for store 1, items 1–5. Random forest remains the dashboard method because it had the lowest **2016 daily validation MAE**. The LSTM is a completed deep-learning experiment, with its results retained even though it did not win that comparison.

## Evaluation design

Training uses 2013–2015, validation uses 2016, and the final evaluation uses 2017. All three methods predict seven days at a time, advancing by seven days. Each period contains 52 complete weeks per item: 364 daily predictions per item, 1,820 overall, and 260 item-week totals.

- Validation scores 1 January–29 December 2016; 30–31 December are excluded as an incomplete week.
- Final testing scores 1 January–30 December 2017; 31 December is excluded as an incomplete week.
- Each forecast uses only observations available by its cut-off. Observed history advances between weeks, but model weights stay fixed throughout each evaluation.
- Model choice, settings and LSTM epoch counts were saved before final scoring. The learned models were then refitted through 31 December 2016. No 2017 sales were used for fitting, scaling, early stopping or choosing the method.
- All forecasts are clipped at zero. Errors use unrounded quantities; only stock-order recommendations are rounded upwards.

MAE is average absolute error; RMSE gives more weight to larger errors. Weekly-total MAE measures the absolute difference between each predicted and observed seven-day total. Lower is better for all three. They are errors in units, not percentages of accuracy.

## 2016 validation

| Method | Daily MAE | Daily RMSE | Weekly-total MAE |
| --- | ---: | ---: | ---: |
| Weekly benchmark | 6.320 | 8.217 | 18.758 |
| Random forest | **4.911** | **6.596** | 19.797 |
| Small LSTM | 5.439 | 7.227 | **17.280** |

| Item | Benchmark daily MAE | Random forest daily MAE | LSTM daily MAE |
| --- | ---: | ---: | ---: |
| 1 | 5.277 | 3.849 | 4.298 |
| 2 | 9.082 | 7.454 | 8.120 |
| 3 | 7.228 | 5.500 | 6.460 |
| 4 | 5.173 | 3.960 | 4.397 |
| 5 | 4.841 | 3.790 | 3.920 |

Random forest won the predefined daily-error criterion on all five items. The LSTM had the best overall weekly-total error. This trade-off matters for stock planning: lower daily error alone does not prove better stock orders. We retained the documented selection criterion instead of switching metrics after seeing the results.

## 2017 final test

| Method | Daily MAE | Daily RMSE | Weekly-total MAE |
| --- | ---: | ---: | ---: |
| Weekly benchmark | 6.273 | 8.218 | 18.427 |
| Random forest | **4.812** | **6.387** | 17.973 |
| Small LSTM | 5.411 | 7.261 | **17.343** |

| Item | Method | Daily MAE | Daily RMSE | Weekly-total MAE |
| --- | --- | ---: | ---: | ---: |
| 1 | Benchmark | 5.258 | 6.625 | 15.500 |
| 1 | Random forest | 3.991 | 4.987 | 13.441 |
| 1 | LSTM | 4.335 | 5.506 | 13.796 |
| 2 | Benchmark | 8.978 | 11.384 | 30.038 |
| 2 | Random forest | 6.981 | 9.051 | 29.620 |
| 2 | LSTM | 8.005 | 10.356 | 28.134 |
| 3 | Benchmark | 7.143 | 9.087 | 19.923 |
| 3 | Random forest | 5.489 | 7.027 | 20.663 |
| 3 | LSTM | 6.383 | 8.235 | 20.096 |
| 4 | Benchmark | 5.387 | 6.851 | 13.596 |
| 4 | Random forest | 4.162 | 5.272 | 13.951 |
| 4 | LSTM | 4.482 | 5.750 | 13.062 |
| 5 | Benchmark | 4.599 | 5.891 | 13.077 |
| 5 | Random forest | 3.438 | 4.470 | 12.188 |
| 5 | LSTM | 3.851 | 5.016 | 11.628 |

The selected random forest's daily MAE is approximately 23.3% lower than the benchmark on this final period. Its weekly-total error is also slightly lower overall, but worse for items 3 and 4. The LSTM again has the best overall weekly-total error. These findings describe this historical five-item subset; they do not establish cost savings, stockout reduction or general superiority of one algorithm.

## Small LSTM specification

Each item has a separate model: 28 chronological daily sales values, one 16-unit LSTM layer and a seven-output dense layer. Each model has 1,271 trainable parameters. It uses no calendar features, whereas the random forest includes known calendar information. This is a limited comparison of these configurations, not a controlled claim about the algorithms in general. The layer follows the [Keras LSTM API](https://keras.io/api/layers/recurrent_layers/lstm/).

Inputs and targets are standardised using the item's training-period mean and standard deviation only. A constant series uses scale 1. Predictions are transformed back to sales units before non-negative clipping and scoring. The final refit recomputes the scaler through 2016 only.

Training uses Adam at learning rate 0.001, mean squared error loss, batch size 32, no shuffling and a maximum of 50 epochs. Seeds are 42 plus the item ID. PyTorch runs on CPU with one thread and deterministic algorithms enabled. [Early stopping](https://keras.io/api/callbacks/early_stopping/) monitors 2016 validation loss with patience 5 and restores the best weights. Epoch counts are selected by validation loss; the overall forecast method is selected by daily validation MAE. There was no architecture or hyperparameter search.

| Item | Validation-training epochs run | Selected epoch / final-refit epochs | Validation fit seconds |
| --- | ---: | ---: | ---: |
| 1 | 44 | 39 | 12.243 |
| 2 | 50 | 50 | 13.091 |
| 3 | 17 | 12 | 3.599 |
| 4 | 50 | 50 | 11.550 |
| 5 | 26 | 21 | 7.682 |

Items 2 and 4 reached the predeclared 50-epoch limit; it was not extended after evaluation. Each item has 1,061 daily training windows in the initial fit and 1,427 in the final refit. All seven targets of a training window must fall within its fitting period. The final refit uses the fixed epoch counts above and no test-year validation callbacks.

The complete LSTM validation-training call took 54.901 seconds, including runtime setup and window preparation. Individual fit times in the table exclude that setup. Final refit calls took 72.011 seconds for all five LSTMs and 7.821 seconds for the five random forests, excluding scoring and saving. Timings depend on the PC and are not dashboard response times.

Versions: Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, scikit-learn 1.9.1, Streamlit 1.65.0, joblib 1.6.0, Keras 3.15.1 and PyTorch 2.14.1. Optional deep-learning dependencies are pinned separately. The random forest settings remain 100 trees, maximum depth 10, minimum leaf size 3, seed 42 and one worker.

## Reproduction and evidence

Follow the README's preparation, initial comparison, LSTM validation and final-evaluation commands in that order on a fresh setup. The validation stage saves `selection-lock.json`; the final stage checks that settings, dataset and method still match. Scripts refuse to overwrite the frozen comparison or rerun a completed final evaluation in that directory. Reproduction on another PC should confirm the recorded design, not be used to tune against 2017.

Prepared dataset SHA-256: `cc1444c3031a00d3d03c6ac35dfc47997dddae65db78f3ae31dee241db9c325c`.

Local evidence in `artifacts/forecasters/` includes the comparison, selection lock, final-test summary, individual prediction CSVs and saved LSTM metadata with full loss histories. Both final learned models were saved and reloaded before scoring. Data and trained files remain outside Git; this reviewed summary is tracked.

The dashboard continues to use random forest. It displays separate validation and final-evaluation tables for all three methods. The assistant retrieves both periods from the same saved results. The demonstration uses sales through 31 December 2017 to forecast 1–7 January 2018; actual outcomes for those dates are absent, so their accuracy is unverified.

All 45 automated tests passed. Added checks cover chronological sequence order, fitting/scaling boundaries, complete validation weeks, fixed-epoch refitting without test validation, unchanged predictions when future sales change, fixed forecast weights, saved-model reproduction and distinct validation/final-test answers. Existing checks cover the five-item dashboard, stock calculations and assistant state. Keras emitted NumPy compatibility deprecation warnings during conversion; they did not fail training or the checks. Optional LSTM integration tests skip when the extra dependencies are absent.

A Chrome check confirmed the final-performance answer and both comparison sections. Desktop and mobile previews were inspected; wide metric tables scroll horizontally on a small screen. The running preview needed restarting to load the changed Python modules.

Group review, a second-laptop rehearsal and updates to the submission PDF, poster and presentation remain pending. The fictional retailer and manually entered stock/supplier assumptions must remain clearly labelled.
