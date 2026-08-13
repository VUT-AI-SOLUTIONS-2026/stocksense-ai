# Contributing

This guide exists so that ten people can work on the same project without standing on each other's feet. Read it once before your first commit. It takes five minutes and saves hours.

## Ground rules

1. Nothing gets committed straight to `main`. Ever. `main` must always be in a state we could demo without warning.
2. Every piece of work starts as an issue. If it is not on the [project board](https://github.com/orgs/VUT-AI-SOLUTIONS-2026/projects), it is not being tracked, and two people will end up doing it.
3. One issue, one branch, one pull request. Small pull requests get reviewed in minutes. Big ones sit for days.
4. Your pull request needs approval from one other member before it can be merged.
5. Never commit data or secrets. No customer data, no `.env` files, no API keys, no exported spreadsheets. See [SECURITY.md](SECURITY.md).

## Getting set up

```bash
git clone https://github.com/VUT-AI-SOLUTIONS-2026/stocksense-ai.git
```

```bash
cd stocksense-ai
```

Once there is code to run, the setup steps will be added here.

## The workflow

### 1. Claim an issue

Assign yourself on the project board and move the issue to In Progress. If no issue exists for what you are about to do, create one first.

### 2. Branch

Always branch from an up to date `main`.

```bash
git checkout main && git pull && git checkout -b docs/12-problem-definition
```

Branch names follow `type/issue-number-short-description`.

| Type | Use it for |
| --- | --- |
| `feat/` | A new capability |
| `fix/` | A bug fix |
| `docs/` | Documentation only |
| `model/` | Model training, tuning or evaluation |
| `data/` | Data pipeline, schema or validation work |
| `test/` | Tests only |
| `chore/` | Tooling, CI, dependencies, housekeeping |

### 3. Commit

Write the message as `type(scope): summary`, in the imperative.

```
docs(problem): tighten problem definition to 240 words
feat(inventory): add reorder point calculation
fix(features): correct lag alignment across store boundaries
```

Keep the summary under 72 characters. If the reason is not obvious, explain it in the body. A commit message that just says "update" tells a reviewer nothing.

### 4. Push and open a pull request

```bash
git push -u origin docs/12-problem-definition
```

Open the pull request against `main`, fill in the template, and write `Closes #12` so the issue closes by itself when the work merges.

### 5. Get it reviewed

Ask someone who did not write the work to review it. Reviewers, be specific and comment on the work rather than the person. Authors, assume good faith and push a fix rather than arguing in the comments.

### 6. Merge

Once the review is approved, use Squash and merge, then delete the branch.

## Writing standards

The documents in `docs/` are marked work, so the brief's formatting rules apply to anything we export for submission:

* Arial, size 12
* Line spacing 1.5
* Text justified
* Run it through Grammarly, and keep the report. The brief requires it to be submitted with the project.

Markdown in this repository does not need to look like that. The formatting matters when the document is exported to PDF for Blackboard.

## Where to ask

If you have been stuck for more than thirty minutes, ask. Comment on the issue or message the group. Struggling in silence is the most expensive thing anyone can do on a deadline.
