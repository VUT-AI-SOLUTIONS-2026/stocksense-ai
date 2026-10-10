# Team

VUT AI Solutions · Diploma: Information Technology

| # | GitHub | Full name | Student number | Preferred commit email | Main responsibility |
| --- | --- | --- | --- | --- | --- |
| 1 | [@morrissambo18-oss](https://github.com/morrissambo18-oss) | Morris Sambo | 240699874 | 240699874@edu.vut.ac.za | Project lead / AI Engineer |
| 2 | [@junior07-oss](https://github.com/junior07-oss) | Percy Mduduzi Jr Dlamini | 224057855 | 224057855@edu.vut.ac.za | AI Data Analyst |
| 3 | [@Kimzo-2](https://github.com/Kimzo-2) | Ungakimi Nkambule | 222072385 | akim.nkambule@icloud.com | AI Evaluation Engineer |
| 4 | [@mazii14](https://github.com/mazii14) | Wandile Samuel Mazibuko | 224067737 | 224067737@edu.vut.ac.za | QA Tester |
| 5 | [@Mick92-r](https://github.com/Mick92-r) | Mick Ndaj Kongal | 224342924 | 224342924@edu.vut.ac.za | Data Engineer / Data Collector |
| 6 | [@NeoMokoena2214](https://github.com/NeoMokoena2214) | Neo Mokoena | 240111699 | 240111699@edu.vut.ac.za | AI Model Specialist |
| 7 | [@refiloemdluli75](https://github.com/refiloemdluli75) | Buhle Refiloe Mdluli | 224661612 | refiloemdluli75@gmail.com | MLOps Engineer |
| 8 | [@SenamileNhlanhla](https://github.com/SenamileNhlanhla) | Senamile Nhlanhla | 224110519 | senamilenhl@gmail.com | Presentation / Business Lead |
| 9 | [@SiboM2](https://github.com/SiboM2) | Sibongiseni John Mokobori | 224133209 | sebongisenijohn@gmail.com | Frontend / Dashboard developer |
| 10 | [@zamajobe237](https://github.com/zamajobe237) | Zama Angel Mtetwa | 225039907 | 225039907@edu.vut.ac.za | Documentation / Business Analyst |

## Next contributions

Each task below has an open GitHub issue assigned to its owner. All ten members have repository access to push changes, checked on 9 October 2026. Members should confirm or exchange tasks before starting. No task below is recorded as completed.

| Owner | Contribution to make | Evidence to provide | Reviewer | GitHub task |
| --- | --- | --- | --- | --- |
| Morris | Specify the stock calculation and integrate the prototype components. | A written calculation with delivery assumptions and examples; integration changes after review. | Zama | [#23](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/23) |
| Percy | Analyse the five items using development data through 2016 and recommend forecasting features. | Short findings with calculations, feature choices and reasons. | Mick | [#24](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/24) |
| Ungakimi | Review the benchmark evaluation and define the model comparison. | Check the 52 scored weeks, excluded dates and error calculations; prepare the comparison table and corrections. | Wandile | [#25](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/25) |
| Wandile | Design application and stock calculation tests. | At least 10 input/expected-output cases, including invalid inputs, sufficient stock and shortages before delivery. | Ungakimi | [#26](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/26) |
| Mick | Check the dataset preparation against the original CSV. | Record the source hash, row counts, date coverage and results of running preparation; identify corrections if needed. | Percy | [#27](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/27) |
| Neo | Specify and review the random forest and small LSTM experiments. | Explain model inputs, starting settings and a limited validation comparison; review the resulting implementation. | Ungakimi | [#28](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/28) |
| Buhle | Verify the installation and repeatable run process. | A checked setup guide, actual package versions and a run log; organise the later rehearsal on another laptop. | Morris | [#29](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/29) |
| Senamile | Connect the retailer's problem to the demonstration and presentation. | A short business explanation, proposed demo sequence and poster outline; replace planned outcomes with measured results later. | Zama | [#30](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/30) |
| Sibongiseni | Design the dashboard layout and input messages. | A simple layout showing history, forecast, stock inputs and assistant; clear date labels and validation messages. | Senamile | [#31](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/31) |
| Zama | Review and update the report against the implemented baseline. | Explain the 6.320-unit validation MAE in plain language, distinguish validation from final testing and correct unsupported claims. | Percy | [#41](https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai/issues/41) |

The assistant's initial question sets and measured results are now available in [the question corpus](../resources/assistant_questions.json) and [assistant results](assistant-results.md). The shared next task is to review the wording and test independently written questions. Record who supplies or corrects each set and keep new test questions separate from training examples.

## Working from one PC

1. The owner produces the requirements, analysis, examples, tests, text or code for their task. They can work on Morris's PC or send their contribution for integration.
2. Keep the submitted contribution with the task: a file, suggested changes or notes that lead to a specific change. Codex can help implement and explain it.
3. The reviewer checks the result and records findings. Fix the issues and run the relevant checks before committing.
4. Commit the completed contribution with an accurate description, then push it from the authorised account. Human task ownership, commit authorship and the account pushing a commit are separate things.

Members can also open issues or review pull requests through their own GitHub accounts. Repository members need the appropriate access for the actions they perform. Commit attribution alone does not grant repository access.

## Commit credit

Morris is the default commit author for this repository, using the full name and student email listed above. Before crediting another member, confirm their agreement to the chosen identity and the specific contribution being credited.

On 9 October 2026, Morris confirmed that all ten members were helping during the shared working session and requested co-author credit in line with their existing roles. For changes they contribute to together, Morris remains the primary author and the nine other members are listed with `Co-authored-by` trailers. Their roles and task ownership remain in the tables above; a co-author trailer does not describe a role or mark an assigned task complete.

The repository includes a [commit message template](../.gitmessage) for this shared workflow. It is configured on this PC. On another laptop, run `git config --local commit.template .gitmessage`, then use `git commit` to open the template in the editor. Commands using `git commit -m` or `git commit -F` must include the trailers explicitly because they do not use this template. Keep only the members who contributed to the particular change.

The preferred names are the full names in the member table. Morris supplied the nine other members' email addresses on 9 October 2026; the table now uses those addresses instead of assuming that every member uses a student email. Morris's existing student address remains unchanged. Their association with members' GitHub accounts has not been independently verified. Each member should confirm that their listed address is added and verified in GitHub Settings > Emails so that GitHub can link commits using that address to their profile. Listing an address here does not verify it or grant repository access.

Use the member as author for a contribution they authored. Use `Co-authored-by` trailers when several people contributed to the change. Record review findings separately; being assigned a task or simply approving a change does not automatically make someone a co-author of all its code.

The record should describe AI assistance where it was used. Do not redistribute existing commits, invent completed work, backdate changes or add members solely to increase contribution counts.

GitHub connects authorship to account-linked email addresses. Profile contribution counts also depend on the repository and branch criteria; commits on the current working branch may count after they reach the default branch. See [GitHub co-author guidance](https://docs.github.com/en/pull-requests/how-tos/commit-changes/creating-a-commit-with-multiple-authors) and [contribution criteria](https://docs.github.com/en/account-and-profile/reference/profile-contributions-reference).

## Contribution record

Add a row when a contribution is completed. Record an actual change and its evidence; a proposed task is not a completed contribution.

| Date | Change | Human contribution and AI assistance | Evidence | Review status |
| --- | --- | --- | --- | --- |
| 9 October 2026 | Initial data preparation and weekly forecast benchmark, commit `273698d` | Morris requested and directed the milestone. OpenAI Codex generated the implementation, tests, setup instructions and result summary. | Real dataset preparation and evaluation succeeded; 18 automated tests passed. See [baseline results](baseline-results.md). | Group review pending. |

For the final report, describe who actually specified, implemented, tested and reviewed each part, including the assistance used. Each member should be able to explain their contribution and the complete demonstration.

## 10 October 2026 continuation

Morris requested and directed the personal-PC verification and submission draft integration, with Codex assistance. The recorded shared-team co-author agreement in the handover applies to this submission milestone. This credit does not claim that each member has independently reviewed the draft or completed their assigned issue. The technical rehearsal passed 45 tests; editable report, poster and presentation materials are available in `docs/submission/`. Human reviews, signatures, independent questions and speaking-role confirmation remain pending.
