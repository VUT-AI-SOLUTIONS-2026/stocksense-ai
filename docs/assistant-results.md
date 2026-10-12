# Text assistant

Provenance: the original results below describe the office run. The independent personal-PC verification on 10 October 2026 is summarised in [model results](final-model-results.md). All 45 tests passed there with no skips; frozen evaluation files were preserved.


Implemented and checked on 9 October 2026. The assistant supports five intents: forecast, reorder, history, performance and help. This supports the NLP and chatbot sections of the rubric through question classification and retrieval of relevant application results.

## How it works

Text is lowercased, numbered item references are normalised, and common English stop words are removed. TF-IDF represents individual words and pairs of words. A logistic regression classifier with C=5, random state 42 and at most 1,000 iterations predicts an intent. The classifier is trained in a script and loaded by the dashboard. It does not generate sales estimates or retrieve information from the internet.

Answers are templates populated from the existing forecast, observed sales, stock calculation and evaluation summaries. Since 10 October, performance answers distinguish 2016 validation from the recorded 2017 final test. Neither is presented as measured January 2018 accuracy. Reorder answers require submitted, valid stock inputs. Changing items clears the stored stock result. Since 11 October, a question can name a different item to retrieve its forecast or sales history. Questions about IDs outside 1–5 receive a scope explanation.

## Question split and measured results

The checked-in corpus contains 60 training questions, 15 validation questions (10 supported and 5 unrelated), 25 fresh supported test questions and 8 fresh unrelated test questions. No normalised question appears in more than one split. The corpus also retains an earlier 25-question and 8-question development check for transparency.

An initial model recognised 16/25 supported questions and rejected 7/8 unrelated ones. That check exposed problems caused by common words and conservative confidence. After revising text processing, those questions became development data. They are not presented as fresh test evidence.

The revised classifier selected its confidence threshold using validation alone:

| Threshold | Correct validation decisions |
| --- | ---: |
| 0.35 | 15/15 |
| 0.45 | 14/15 |
| 0.55 | 12/15 |

With the selected threshold of 0.35, the fresh check measured:

| Check | Result |
| --- | ---: |
| Supported intent classification | 24/25 (96%) |
| Unrelated questions rejected | 8/8 |

The missed question was "Give me a summary of historical demand for item 5": it was classified as forecast instead of history. No further tuning was performed against the fresh test results. The question sets are small and curated; these figures do not establish general conversational accuracy. Independent group questions and a presentation rehearsal are still needed.

## Integration checks

All 37 automated tests passed. The eight added tests cover forecast totals and dates, observed sales totals, stock prerequisites and shortage warnings, validation metrics, item scope, fallback answers, persistence across questions and clearing stale stock results. A question after a stock calculation keeps the order visible. A change of item or invalid submitted coverage cannot reuse the old order.

Run `python -m scripts.train_assistant` to reproduce training and evaluation. Exact predictions and validation comparisons are saved to `artifacts/assistant/evaluation.json`. Run `python -m unittest discover -s tests -v` for implementation checks; dashboard integration tests require prepared data and the saved assistant model.

## Greeting and suggested questions, 11 October 2026

A small deterministic rule now welcomes greeting-only inputs such as hi, hello and hey. It shows four supported question examples, also displayed above the question form. Mixed greeting-and-forecast questions still reach the existing classifier. The five trained intents, saved classifier and frozen forecast evaluations were preserved; no retraining or threshold change was made.

All 47 automated tests passed with no skips in 42.539 seconds on the personal PC. New checks cover greetings without classification, a mixed forecast query, visible suggestions and preservation of the submitted stock order. This extends the earlier 45-test rehearsal; it does not replace the historical assistant classification scores. Detailed local test output is in artifacts/rehearsal/greeting-tests.txt.

## Item questions and stock guidance, 11 October 2026

Questions can name an item using a number or a word, such as "forecast for item 2" or "recent sales for product two". The assistant retrieves that item's saved-model forecast and observed history without changing the dashboard selector. It never uses another item's stock plan. Multiple explicit item references prompt a request for one item at a time.

Simple phrase rules support stock questions such as "Will I run out?", "Do I have enough stock?" and "Should I restock?". If no valid plan is available for the requested item, the assistant asks for stock available, outstanding units, supplier lead time, review interval and buffer stock through the existing form. It does not assume the form defaults describe the user's stock. An unclear question offers supported topics and examples. There is no general conversation memory or free-text stock-input parser.

All 51 automated tests passed with no skips in 48.526 seconds on this PC. Checks include named-item answers against dashboard totals, stock-plan isolation, missing inputs and delivery shortages. The trained classifier, question corpus and frozen forecasting results were unchanged. The earlier 24/25 classification result remains historical evidence, not a new score for the extended question handling.

## Chat interface, 11 October 2026

Ask StockSense now displays user and assistant message bubbles, four clickable question shortcuts, a send-on-Enter input and a Clear button. It retains the latest 20 exchanges for the browser session. Previous answers keep their original selected-item context; conversation display does not add conversational reasoning or infer missing stock inputs. Clearing the chat preserves the current stock calculation.

All eight dashboard integration tests passed in 24.412 seconds, covering chat history, shortcuts, clearing, stock persistence, named items, all five forecasts and invalid stock inputs. The narrow browser layout and forecast shortcut were visually checked. The saved models and evaluation files were unchanged.

## Interface refresh, 11 October 2026

The dashboard gained a wide desktop layout, teal introductory panel, chart beside the forecast summary, and separate stock-planning and assistant cards. The personal-PC record reports checks at 390- and 1280-pixel widths and 47 automated tests passing with no skips in 59.452 seconds. Item 1 still forecast 114.9 units, the default order was 38 units, and Hi returned the welcome and examples. No model training or new dependencies were introduced. Local log: `artifacts/rehearsal/ui-tests.txt`. This is technical evidence, not an independent human usability review.
