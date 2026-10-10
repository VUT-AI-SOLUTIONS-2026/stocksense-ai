# Personal PC rehearsal

Verified directly on Morris's personal PC on 10 October 2026 at 17:42 SAST, after safely fast-forwarding `prototype-baseline` to handover commit `c4ec9fc`. This is a second-machine technical rehearsal relative to the office record. It is not a member-led presentation rehearsal or independent human review.

## Preserved setup

Project: `C:\Users\morri\stocksense-ai-latest`. The environment, real Kaggle dataset, prepared subset, trained assistant and frozen forecasting outputs already existed. No preparation or training stage was repeated during this rehearsal. The running Streamlit process at `http://localhost:8501` was reused.

Python is 3.14.6 on this PC; the office reference used 3.12.14. Both use NumPy 2.3.5, pandas 3.0.1, scikit-learn 1.9.1, Streamlit 1.65.0, joblib 1.6.0, Keras 3.15.1 and PyTorch 2.14.1. Compatibility checks passed without replacing the environment. Keras emits conversion deprecation warnings, but they do not fail the current tests.

Raw SHA-256: `038f25690a65149c94f86ddd3deceda20c037a5cfd754cafdfc539a72992f2ed`.

Prepared SHA-256: `cc1444c3031a00d3d03c6ac35dfc47997dddae65db78f3ae31dee241db9c325c`.

Both match the office record. The rehearsal checked that these files, selection-lock.json, final-test.json and the assistant model retained their hashes.

## Direct checks

All **45 automated tests passed with no skips**, in 37.450 seconds in this verification run. The separate AppTest rehearsal checked:

- All five selectors, seven predictions each, dated 1-7 January 2018.
- Item 1 default stock order: 38 units, with five-day forecast demand 77.52, buffer 10, stock 50 and outstanding units 0.
- Lead time 6 plus review interval 3: rejected because coverage exceeds seven days.
- Stock 0 and lead time 2: shortage before delivery warning appears.
- Forecast assistant answer matches displayed 114.9-unit item 1 total and preserves a valid stock order.
- Separate 2016 validation and 2017 final tables appear.

| Item | Seven-day forecast total | Warm item-change seconds |
| --- | ---: | ---: |
| 1 | 114.9 units | 0.213 |
| 2 | 310.6 units | 0.227 |
| 3 | 178.7 units | 0.198 |
| 4 | 111.5 units | 0.204 |
| 5 | 90.1 units | 0.209 |

Initial AppTest render took 7.287 seconds. These are one-run test-harness timings, excluding browser network latency. They do not establish a general response guarantee or human usability result. Streamlit was also exercised in the browser in the setup session, and a screenshot is included with the submission source.

## Results and provenance

Local model metrics match the office's documented values to three decimal places. Random forest remains selected by frozen 2016 daily MAE. Final daily MAE is 4.812 units versus benchmark 6.273 and LSTM 5.411. LSTM has lower overall weekly-total MAE. The forecast totals above are January 2018 estimates with no observed outcomes.

The local fresh assistant evaluation is 24/25 supported intents and 8/8 unrelated requests rejected. It was trained during initial setup and preserved during this rehearsal. Office training times in final-model-results.md remain historical office measurements; do not substitute them for personal-PC timings.

Local detailed evidence: `artifacts/rehearsal/personal-pc.json` and `artifacts/rehearsal/tests.txt`. Those generated files remain ignored. The original assignment PDF was found in Downloads and checked directly. Its rubric totals 100, and its report format is Arial 12, 1.5 spacing and justified text.

## Outstanding human work

Group content review, signatures, Grammarly evidence, three-reviewer usability checks, a timed 20-minute group rehearsal, campus slot confirmation and a backup demonstration recording remain pending. Existing assigned GitHub issues #23-31 and #41 were checked and remain open. GitHub Projects could not be inspected with the current CLI credential because `read:project` scope is absent. No additional access was granted and no issue was closed.
