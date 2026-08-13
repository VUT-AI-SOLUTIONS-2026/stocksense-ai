# Security and data rules

## Reporting a problem

Do not open a public issue for a security problem. Message the project lead directly, describing what the problem is, how to reproduce it, and what someone could do with it. You will get a response within three days.

This is a student project, so nothing here is production hardened and there is no bounty. We still fix what gets reported.

## Handling data

The solution processes retail sales data. Most of that is commercially sensitive, and some of it could be personal information covered by the Protection of Personal Information Act. These rules are not negotiable.

**Never commit real business data.** No sales exports, no customer records, no supplier contracts. For demonstrations, screenshots and the presentation, use generated sample data instead.

**Never commit secrets.** No API keys, tokens, passwords, connection strings or `.env` files. Keep those in a local `.env` file, which `.gitignore` already excludes.

**Anonymise before analysing.** If a partner shop ever gives us real data, strip anything that identifies a person before it goes near a notebook.

**Data stays out of the repository.** The `data/` folder is ignored by git on purpose. Do not use `git add -f` to get around it.

## If a secret does get committed

Deleting it in a later commit is not enough. It stays in the git history, and on a public repository you have to assume someone already has it.

1. Change or cancel the credential immediately. This is the only step that actually protects anything.
2. Tell the project lead.
3. Remove it from the history properly, using `git filter-repo` or the BFG Repo-Cleaner, then force push.
4. Add the pattern to `.gitignore` so it cannot happen twice.

## Dependencies

Add a package only when it genuinely earns its place, and only if it is maintained and widely used. Pin versions so that a setup which worked yesterday still works on presentation day. If Dependabot raises an alert, deal with it rather than closing it.
