# Text assistant

Provenance: the original results below describe the office run. The independent personal-PC verification on 10 October 2026 is recorded in [personal-pc-rehearsal.md](personal-pc-rehearsal.md). All 45 tests passed here with no skips; frozen evaluation files were preserved.


Implemented and checked on 9 October 2026. The assistant supports five intents: forecast, reorder, history, performance and help. This supports the NLP and chatbot sections of the rubric through question classification and retrieval of relevant application results.

## How it works

Text is lowercased, numbered item references are normalised, and common English stop words are removed. TF-IDF represents individual words and pairs of words. A logistic regression classifier with C=5, random state 42 and at most 1,000 iterations predicts an intent. The classifier is trained in a script and loaded by the dashboard. It does not generate sales estimates or retrieve information from the internet.

Answers are templates populated from the existing forecast, observed sales, stock calculation and evaluation summaries. Since 10 October, performance answers distinguish 2016 validation from the recorded 2017 final test. Neither is presented as measured January 2018 accuracy. Reorder answers require submitted, valid stock inputs. Changing items clears the stored stock result. An explicit request for a different item asks the user to change the selector. Questions about IDs outside 1–5 receive a scope explanation.

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
