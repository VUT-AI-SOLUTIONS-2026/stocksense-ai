# StockSense AI

## Retail sales forecasting and stock replenishment

Vaal University of Technology

Diploma in Information Technology

Business Analysis 3 Module 2

Subject code AIBUY3A

Group VUT AI Solutions

Theme: An AI Solution for Industries

Submission date: 2 November 2026

## Declaration and group members

We declare that the submitted project is our own work and that we have referenced the work and ideas of others where used. Each member must review and sign this declaration before submission. The signature spaces below are intentionally blank.

| Full name | Student number | Signature | Date |
| --- | --- | --- | --- |
| Morris Sambo | 240699874 | | |
| Percy Mduduzi Jr Dlamini | 224057855 | | |
| Ungakimi Nkambule | 222072385 | | |
| Wandile Samuel Mazibuko | 224067737 | | |
| Mick Ndaj Kongal | 224342924 | | |
| Neo Mokoena | 240111699 | | |
| Buhle Refiloe Mdluli | 224661612 | | |
| Senamile Nhlanhla | 224110519 | | |
| Sibongiseni John Mokobori | 224133209 | | |
| Zama Angel Mtetwa | 225039907 | | |

<!-- PAGE -->

## 1 Background and theme relevance

StockSense AI uses historical sales to help Sunrise Mini Market, a fictional retailer, plan stock purchases. Kaggle's Store Item Demand Forecasting dataset supplies anonymous sales records [1]. The Python prototype covers store 1 and items 1 to 5, predicts seven daily quantities and calculates order suggestions using entered stock and delivery assumptions. It fits the theme An AI Solution for Industries by applying machine learning to a retail decision. The intended benefit is a consistent estimate before ordering. A local dashboard and text assistant make the estimates and assumptions accessible. 

## 2 Problem definition

### The problem

In our fictional retail case, the manager decides how much stock to order by checking current stock and recent sales. The process does not use a consistent forecast for the period ahead. If the manager underestimates sales, products may run out before the next delivery. If the manager overestimates sales, money is tied up in stock that sells slowly. The manager needs a simple way to estimate upcoming sales and compare those estimates with available stock before placing an order. This case study assumption defines the business problem. The selected dataset provides historical sales for testing forecasts, but does not establish that a particular South African retailer experiences this problem.

### The benefit of solving it

StockSense AI produces seven-day sales estimates and demonstration order suggestions. This supports the retail industry by applying AI to stock planning. The intended benefits are more consistent ordering and clearer information for the manager. Forecast accuracy was tested on historical data. Reductions in stockouts, waste or costs would require a separate inventory simulation or business trial before they could be claimed as achieved results.

For the community, more reliable stock could improve residents' access to goods and reduce repeat shopping trips. Supporting local small retailers could also benefit economic activity in the municipality. These are intended benefits, not measured outcomes.

## 3 Business analysis

### 3.1 Business background and current process

Sunrise Mini Market represents a small retailer that records daily sales and orders goods from a supplier. Products 1 to 5 correspond to the anonymous dataset item IDs; their actual names and the store location are unknown.

The assumed current process is to review recent sales, check available stock and choose an order quantity manually. In the proposed process, the manager opens the application, selects an item and checks its sales history and seven-day forecast. The manager enters stock and delivery information, then reviews the suggested quantity and its calculation. Ordering remains a business decision made by the manager.

### 3.2 Main objective

Develop a small Python application that forecasts seven days of sales for five items and uses those estimates to support understandable stock decisions. Compare the learned models with a weekly benchmark and retain a simple local demonstration that every member can explain.

### 3.3 Business objectives and success criteria

| Objective | Acceptance criterion | Evidence and status |
| --- | --- | --- |
| Consistent estimate | Seven dated values for all five items | All five items passed automated forecast checks; see Section 11. |
| Lower daily forecast error | Beat weekly benchmark on identical dates | Random forest final MAE 4.812 versus 6.273 units, about 23.3% lower. |
| Transparent stock suggestion | At least ten arithmetic cases and invalid inputs | Automated calculation cases and dashboard checks passed. |
| Practical local response | Saved forecasts displayed within ten seconds | AppTest initial render 7.29 seconds; warm selections 0.20-0.23 seconds. Timings exclude browser latency. |
| Useful text requests | At least 20 of 25 supported intents recognised | Saved fresh evaluation: 24/25, plus 8/8 unrelated requests rejected. |

The business objectives include reducing waste, stockouts and costs; these require a separate business trial to measure.

### 3.4 Requirements

The system must load the sales CSV, check its required columns and organise records by store, item and date. It must let the manager choose from items 1 to 5 at store 1, show recent sales and produce a seven-day forecast. Stock inputs must lead to a visible order suggestion and explanation. The manager can use the web dashboard or terminal chat. Both interfaces must retrieve the same forecasts and apply the same stock calculation rule, with separate session inputs.

The application must reject negative quantities, unknown item IDs and unsupported delivery horizons. It must explain when insufficient history prevents a forecast. Saved models and demonstration files should allow it to run without a paid cloud service. The forecast cut-off date must remain visible so that a historical demonstration is not mistaken for a live forecast.

All sales, stock and order quantities are expressed in units. We use Python for the application and GitHub Projects to assign and track work.

### 3.5 Constraints

Our scope is one store, five items and a seven-day forecast. We will not connect the prototype to a till system or place supplier orders. The data covers 2013 to 2017, so the demonstration is historical. Kaggle's description notes that there are no holiday effects or store closures [1]. We will not claim that the data measures South African holidays, pay cycles or load shedding.

Stock levels, outstanding orders, supplier lead times and the buffer stock quantity are demonstration inputs. Prices and purchase costs are absent, which prevents a financial savings calculation. The available laptop and submission deadline also limit the size of the model comparison.

### 3.6 Risks and responses

| Risk | Response |
| --- | --- |
| Future sales enter the training features | Build each sample from information available at its forecast date. Keep all seven target dates inside the assigned training period. |
| A complex model performs poorly | Compare every candidate with the same simple baseline and retain the more reliable method for the demonstration. |
| A stock recommendation is treated as a guarantee | Display its inputs and assumptions. Flag possible shortages before delivery and explain that uncertain sales can differ from the forecast. |
| The demonstration fails on another laptop | Save dependencies and model files, rehearse on another machine and keep a backup recording. |
| Report sections disagree | Use the same scope and data splits throughout and review the complete report together. |

### 3.7 Tools and techniques

Python and pandas validate and prepare the sales records. scikit-learn supplies random forest regression and text classification. Keras with a local PyTorch backend supplies the small LSTM comparison. Streamlit combines the history, forecast, stock form and assistant on one page. A terminal interface provides the same planning and text functions without a browser. Both interfaces use the shared forecasting loader and saved models. Scripts train models separately. No paid online language service is required.

The weekly benchmark is easy to explain. Random forest uses recent sales and known calendar information. LSTM provides a small sequence experiment and a measured deep-learning comparison. The two interfaces share this logic and keep the scope explainable. Git stores source and documentation; raw data, the environment and trained models remain local. GitHub Projects tracks assigned work through Todo, In Progress and Done columns [12]. Member discussions record poster choices and meeting coordination [9, 10].

## 4 Machine learning approach

### 4.1 Prediction task

This is supervised regression: observed daily sales are the targets, and each model predicts seven quantities. Sales can understate demand when inventory is unavailable. The dataset has no stockout information, so we forecast recorded sales rather than claim unconstrained demand.

Random forest inputs are 28 sales lags, 7-, 14- and 28-day means, and sine/cosine encodings of each target date's weekday and annual position. Dates are known at the cut-off; target sales are excluded from inputs. Every fitting window keeps all seven target days inside the training boundary.

### 4.2 Compared methods

The weekly seasonal naive benchmark repeats the last observed week's sales on matching weekdays [3]. One random forest per item predicts seven outputs with 100 trees, depth 10, minimum leaf size 3, seed 42 [4]. These fixed settings are the implemented comparison; no tree-depth search was performed. One small LSTM per item uses 28 chronological sales inputs and seven outputs, without calendar inputs.

The predefined criterion is overall daily 2016 validation MAE, with simpler methods retained on ties. Random forest won this criterion. The method and training settings were fixed before 2017 scoring. The LSTM's stronger weekly-total result is reported rather than changing the criterion afterwards.

## 5 Data

### 5.1 Source and verified structure

The supplied Kaggle archive contains train.csv, test.csv and sample_submission.csv. The training file contains 913,000 rows and four columns, covering 1 January 2013 to 31 December 2017. There are 10 stores and 50 items, giving 500 combinations of stores and items. Each series has 1,826 daily records.

| Field | Data type | Actual example | Meaning and use |
| --- | --- | --- | --- |
| date | Temporal: calendar date | 2013-01-01 | Day of the record; sorts history and supplies calendar features. |
| store | Categorical ID, stored as an integer | 1 | Anonymous store identity; selects store 1. |
| item | Categorical ID, stored as an integer | 1 | Anonymous product identity; selects items 1 to 5. |
| sales | Numerical: discrete whole-number count | 13 | Units sold that day; historical input and prediction target. |

Store and item numbers identify categories; a larger ID does not imply a larger store or better product. Dates have daily resolution, without a recorded time of day. These semantic data types explain the fields' meanings, while their storage formats support validation and filtering.

The chosen subset contains 9,130 records. The five items have different average sales levels, which lets us check whether a method works consistently across items rather than showing only one favourable example.

### 5.2 Actual sample records

These are the first five source records for store 1 and item 1.

| date | store | item | sales |
| --- | --- | --- | --- |
| 2013-01-01 | 1 | 1 | 13 |
| 2013-01-02 | 1 | 1 | 11 |
| 2013-01-03 | 1 | 1 | 14 |
| 2013-01-04 | 1 | 1 | 13 |
| 2013-01-05 | 1 | 1 | 10 |

### 5.3 Data quality checks and preparation

We found no missing cells, duplicate rows, repeated date-store-item keys or negative sales. Quantities range from 0 to 231. The complete source has one zero-sales record. Every combination of a store and an item has a complete daily history over the same date range.

Preparation preserves train.csv, selects the five series and sorts by date. Checks reject missing columns, invalid dates, duplicate daily keys, missing days and negative or fractional quantities. Zero sales remains a valid value. No missing day is silently converted to zero. Each item has 1,061 initial fitting windows and 1,427 final refit windows.

### 5.4 Other data used by the application

Stock data is entered manually for the demonstration. For example, item 1 has 20 units available and 5 units already ordered. The assumed supplier lead time is 3 days, the review interval is 1 day, and the buffer stock is 10 units. These values are assumptions, not Kaggle observations.

Stock, outstanding orders and buffer quantities are numerical whole-number unit counts. Lead time and review interval are numerical whole-number day counts. The item reference remains a categorical identifier.

The assistant's training corpus contains short labelled English examples. For example, "How much will item 2 sell next week?" is unstructured text with the categorical intent label forecast. TF-IDF converts that text to derived numerical features. The resulting answer retrieves the relevant forecast rather than invent a number.

Output records contain a categorical item ID, temporal forecast date, numerical predicted quantity and categorical model label. Predictions can contain fractions, unlike the original whole-number sales counts. Recommendation records include the stock inputs and calculated whole-number order quantity. Charts visually summarise the numerical sales and temporal dates; they are presentation outputs rather than image inputs to a model. We document these derived outputs separately from original observations.

The source contains anonymous IDs rather than customer details. We will use those IDs for this project and follow the dataset's competition terms. The raw CSV will remain separate from report drafts and application source code.

## 6 Model evaluation and time series analysis

### 6.1 Chronological evaluation

| Period | Raw records for five items | Role |
| --- | --- | --- |
| 2013-2015 | 5,475 | Initial fitting |
| 2016 | 1,830 | Validation and frozen selection |
| 2017 | 1,825 | Final evaluation |

Each evaluation uses 52 complete weeks per item: 364 daily predictions per item, 1,820 overall and 260 item-week totals. Validation scores 1 January to 29 December 2016 and excludes 30-31 December. Final testing scores 1 January to 30 December 2017 and excludes 31 December. All methods use the same dates.

Observed history advances between forecast weeks, while learned weights remain fixed. Each forecast sees sales only before its cut-off. Final models were refitted using data through 31 December 2016, with fixed validation-selected LSTM epochs and no early stopping on 2017. Save/reload checks ensure the scored models match persisted files. The separate Kaggle 2018 test.csv has no sales column and cannot supply local accuracy scores.

### 6.2 Error measures

Daily MAE averages absolute predicted-minus-observed errors in units [5]. RMSE weights larger errors more strongly. Weekly-total MAE compares each predicted and observed seven-day total. Predictions are clipped at zero and scored without rounding. Percentage error reduction equals 100 times (benchmark MAE minus selected MAE) divided by benchmark MAE. It is a relative reduction in error, not a percentage of accuracy. Stock order rounding happens only after the calculation.

### 6.3 Observed time series patterns

The following charts use store 1 and items 1 to 5 from 2013 through 2016. We have left 2017 out of the descriptive charts used to design the models.

![Monthly sales for the five selected items](assets/monthly_sales.png)

Figure 1. Monthly total units for store 1 and items 1 to 5, using development data only.

Total annual sales for these items rise from 43,208 units in 2013 to 56,943 in 2016. The monthly chart also shows repeated rises and falls across the years. We use calendar features and recent sales levels to represent these patterns. The chart describes the data; it does not establish the cause of the changes.

![Average daily sales by weekday](assets/weekday_sales.png)

Figure 2. Mean units sold per item per day, grouped by weekday, for 2013 through 2016.

The mean is 21.88 units on Mondays and 33.01 on Sundays for this subset. This supports using a weekly seasonal baseline and weekday features. The figures combine five items, so we also report item-level errors rather than assume that each item follows the same pattern.

### 6.4 Measured model comparison

2016 validation:

| Method | Daily MAE | Daily RMSE | Weekly-total MAE |
| --- | ---: | ---: | ---: |
| Weekly benchmark | 6.320 | 8.217 | 18.758 |
| Random forest | 4.911 | 6.596 | 19.797 |
| Small LSTM | 5.439 | 7.227 | 17.280 |

2017 final test:

| Method | Daily MAE | Daily RMSE | Weekly-total MAE |
| --- | ---: | ---: | ---: |
| Weekly benchmark | 6.273 | 8.218 | 18.427 |
| Random forest | 4.812 | 6.387 | 17.973 |
| Small LSTM | 5.411 | 7.261 | 17.343 |

Random forest has the lowest daily error for all five items and approximately 23.3% less overall final daily MAE than the benchmark. LSTM has the lowest overall weekly-total error in both periods. Random forest's weekly-total validation error is worse than the benchmark; its final weekly error is slightly better overall but worse for items 3 and 4. Daily selection therefore does not demonstrate optimal stock orders. The methods also receive different inputs, so this limited configuration comparison cannot establish general algorithm superiority.

Models forecast 1-7 January 2018 in the dashboard using history through 31 December 2017. Actual outcomes are absent, and neither historical table measures those estimates' future accuracy.

## 7 Solution techniques

### 7.1 Performance and fair comparison

We used recent means and known calendar encodings for random forest, chronological sales sequences for LSTM, and validation loss to choose LSTM stopping epochs. The comparison kept one declared forest configuration and one small network architecture. Test-year data did not choose features, settings, scaling or model selection.

Future work could compare stock decisions through an inventory simulation. Any further model tuning would need new, untouched evaluation data.

### 7.2 Stock recommendation rule

The demonstration uses a simple periodic review rule. Its inputs are supplier lead time L, review interval R, stock available S, outstanding units O due within the coverage period and a fixed buffer B. We limit L plus R to seven days. Outstanding units and an order placed today arrive after the entered lead time. Lead time 2 means before forecast day 3; lead time 0 means before day 1. Outstanding units do not cover sales before that arrival.

The target stock is the sum of predicted sales over the next L plus R days, plus B. Inventory position is S plus O. The suggested order is the positive difference between target stock and inventory position, rounded upwards. If the inventory position exceeds the target, the suggested order is zero. This is a transparent planning rule rather than an optimised inventory policy.

The interface flags a possible shortage before delivery when forecast sales before delivery exceed currently available stock. An order placed today cannot automatically resolve a shortage before the supplier arrives. We state the simplified arrival assumptions with the recommendation.

### 7.3 Difficult cases

The system rejects unknown items, invalid stock quantities and forecast requests with less than 28 days of history. Sparse sales may require a different forecasting method.

## 8 Natural language processing

The assistant recognises five English intents: forecast, reorder, history, performance and help. It lowercases text, normalises numbered item references and removes stop words. TF-IDF converts words and word pairs into numerical features [6]. Logistic regression classifies the request, using a confidence threshold to reject unrelated questions. Answers retrieve application data rather than generate unsupported quantities.

The corpus contains 60 training questions and 15 validation questions. Threshold 0.35 achieved 15/15 correct validation decisions. A separate recorded evaluation recognised 24/25 supported requests and rejected 8/8 unrelated requests; one history request was mistaken for a forecast. These small curated results measure intent recognition. Conversation and retrieval rules have separate automated checks. Voice and multilingual support are outside scope.

## 9 Deep learning

Each item's LSTM receives 28 chronological daily sales values, uses one 16-unit recurrent layer and produces seven daily estimates [7]. It has 1,271 trainable parameters and no calendar features. Inputs and targets are standardised using training data only; predictions are converted back to sales units.

Training uses Adam, mean squared error, batches of 32 and a maximum of 50 epochs without shuffling. Early stopping monitors 2016 validation loss with patience 5 and restores the best weights [8]. The selected epoch counts are fixed before final refitting through 2016; 2017 data is reserved for testing.

Final daily MAE is 5.411 units and weekly-total MAE is 17.343 units. The LSTM has higher daily error than random forest but lower weekly-total error, showing that a more complex model does not win on every measure.

## 10 Chatbot design

Ask StockSense combines intent recognition with retrieval and response templates. It shows dated forecasts, compares products, summarises sales history, explains stock suggestions and defines planning or model terms. Performance answers distinguish validation from final testing. A short conversation context supports follow-up questions.

For example, "How much will Product 2 sell next week?" retrieves Product 2's seven-day forecast. Asking "and Product 3?" then retrieves Product 3's forecast. After a valid stock calculation, "Why should I order this amount?" explains the forecast, buffer, inventory position and rounding.

Missing stock inputs prompt the user to calculate an order first. Unsupported questions show available options. Changing products clears the previous stock plan. Both web and terminal chat use the same classifier, saved forecasts and calculation rule, but keep separate session inputs. Terminal users select products with /product and enter stock values with /stock.

## 11 Practical solution and demonstration

The Streamlit application shows recent history, seven dated estimates, a stock form, Ask StockSense and evaluation tables. Run python -m streamlit run app.py in the project's Python environment, then open the displayed Local URL. Terminal chat runs with python -m stocksense.terminal [11]. Both interfaces load saved models; training takes place separately. README.md contains installation instructions and dependency versions.

On 16 October 2026, all 79 tests passed with no skips. Checks covered forecasts, product comparisons, follow-up questions, stock calculations, invalid inputs and saved-model loading across web and terminal interfaces. The application was also technically rehearsed on a second computer. These checks verify implementation behaviour; independent human usability results are unavailable.

The following example matches the dashboard. Item 1's seven-day forecast totals 114.9 units. With stock 50, outstanding orders 0, lead time 2 days, review interval 3 days and buffer 10 units, the five-day forecast is 77.52 units. Target stock is 87.52 units, so the suggested order is 38 units after rounding up.

![StockSense forecast and stock calculation](assets/stocksense-ready.png)

Figure 3. Dashboard example showing the inputs and resulting 38-unit order suggestion.

The demonstration sequence is product selection, dated forecast, stock calculation, invalid input handling, shortage warning, assistant response and evaluation tables.

## 12 Conclusion

StockSense AI demonstrates sales forecasting and stock planning through web and terminal interfaces. Random forest achieved about 23.3% lower final daily MAE than the weekly benchmark, while LSTM performed better on weekly totals. The assistant makes forecasts and calculations easier to explore. Automated checks support the implementation; real stockout, cost and usability benefits require further evaluation.

## References

[1] Kaggle. Store Item Demand Forecasting Challenge. Data description. https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data. Accessed 9 October 2026. The group supplied the associated archive; numerical data findings and Figures 1 and 2 were calculated directly from its train.csv.

[2] Kaggle. Store Item Demand Forecasting Challenge. Overview. https://www.kaggle.com/c/demand-forecasting-kernels-only/overview. Accessed 9 October 2026.

[3] Hyndman, R. J. and Athanasopoulos, G. Forecasting Principles and Practice, third edition. Some simple forecasting methods. https://otexts.com/fpp3/simple-methods.html. Accessed 9 October 2026.

[4] scikit-learn. RandomForestRegressor documentation. https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestRegressor.html. Accessed 9 October 2026.

[5] scikit-learn. mean_absolute_error documentation. https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_error.html. Accessed 9 October 2026.

[6] scikit-learn. TfidfVectorizer documentation. https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html. Accessed 9 October 2026.

[7] Keras. LSTM layer documentation. https://keras.io/api/layers/recurrent_layers/lstm/. Accessed 9 October 2026.

[8] Keras. EarlyStopping documentation. https://keras.io/api/callbacks/early_stopping/. Accessed 9 October 2026.

[9] VUT AI Solutions. Stock Sense Poster. GitHub Discussion with member comments comparing poster designs. https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/discussions/44. Checked on 14 October 2026.

[10] VUT AI Solutions. Project walkthrough meeting. GitHub Discussion with meeting responses. https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/discussions/49. Checked on 14 October 2026.

[11] VUT AI Solutions. Add terminal chat with shared forecasts and stock planning. Source commit and recorded 79-test validation, 13 October 2026. https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/commit/12f4e5b.

[12] VUT AI Solutions. StockSense AI Projects board. https://github.com/orgs/VUT-AI-SOLUTIONS-2026/projects/1. Configured and verified on 14 October 2026. The board is private to the organisation.
