# Presentation plan

20 minutes of presentation followed by five minutes of questions, as required by the original brief. This running order is proposed, not a completed group rehearsal. Speakers must confirm their allocation; it follows the existing responsibilities and does not reassign GitHub issues.

| Slide | Topic | Time | Proposed speaker |
| --- | --- | --- | --- |
| 1 | StockSense AI and fictional retailer | 0:00-0:30 | Morris |
| 2 | Retail ordering problem | 0:30-2:00 | Zama |
| 3 | Objectives and scope | 2:00-3:30 | Senamile |
| 4 | Dataset and validation | 3:30-5:00 | Mick |
| 5 | Development sales patterns | 5:00-6:00 | Percy |
| 6 | Methods and chronological split | 6:00-7:30 | Neo |
| 7 | 2016 validation and frozen choice | 7:30-8:30 | Ungakimi |
| 8 | 2017 final results and trade-offs | 8:30-10:00 | Ungakimi |
| 9 | Small LSTM specification | 10:00-11:30 | Neo |
| 10 | Stock calculation and arrivals | 11:30-13:00 | Morris |
| 11 | NLP classification and answer retrieval | 13:00-14:30 | Sibongiseni |
| 12 | Setup, testing and second-machine evidence | 14:30-16:00 | Buhle and Wandile |
| 13 | Application demonstration | 16:00-19:00 | Sibongiseni and Morris |
| 14 | Findings, limits and questions | 19:00-20:00 | Senamile |

## Demonstration sequence

1. Open the already running app at localhost:8501. Identify the historical cut-off and anonymous item IDs. Select items and show seven dated predictions.
2. Item 1 defaults: stock 50, outstanding 0, lead time 2, review interval 3 and buffer 10. Calculate the 38-unit suggestion. Explain forecast demand 77.52, target 87.52 and rounding.
3. Enter lead time 6 and review interval 3. Submit and show the invalid coverage message. Restore lead time 2, enter stock 0 and submit to show shortage before delivery.
4. Restore defaults and calculate. Ask "Show the sales forecast". Check the same 114.9-unit total and explain the missing actual January 2018 outcomes.
5. Open validation and final tables. State that selection used 2016 daily MAE and remained fixed. Compare daily error with weekly-total trade-offs.

Use saved files during the presentation. Do not retrain or repeat final evaluation. Before the campus session, rehearse within 20 minutes, confirm the slot and arrive 30 minutes early. Keep slides, PDFs and a backup demonstration recording on a separate device or storage location. A human-led recording and timed rehearsal remain pending.

## Questions to prepare

- Why a fictional retailer? The dataset supplies anonymous IDs, and no local business trial exists.
- Why random forest? It won the predeclared daily validation MAE criterion. LSTM's weekly-total result is retained as a trade-off.
- How is leakage prevented? Chronological split, train-only scaling, bounded target windows and fixed weights with past-only inputs.
- Does 23.3% mean accuracy? It means relative reduction in final daily MAE compared with the benchmark.
- Does this prove better inventory outcomes? No. Inventory, delivery, prices and costs need a separate trial or simulation.
- Is the assistant a general chatbot? It classifies five intents and retrieves actual application objects. The small curated test is limited evidence.
- What is verified here? Real setup, matching dataset hashes, preserved evaluation, all 45 tests and a second-machine technical rehearsal. Human review and signatures are separate.
