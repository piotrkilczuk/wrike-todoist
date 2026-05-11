# wrike-todoist

Python app that syncs external sources into Todoist:

* Google Calendar
* GitHub Issues and Pull Requests
* Bin collections via ecoharmonogram.pl

Deployed as AWS Lambda functions.

## Style

- Black formatter, line-length 120.
- Always use single-line commit messages, no co-authors, no emojis, no prefixes.
- Do not use `_private_function` convention, just `private_function`.

## Tools

### Sentry

- Organization: `kilczukdev-zi`, region: `https://de.sentry.io`
- Project: `python-awslambda`

## Quirks

### ecoharmonogram API

The ecoharmonogram.pl API changes `schedulePeriodId` periodically. The `/streets` endpoint returns JSON `null` with HTTP 200 when the supplied ID is stale.
`harmonogram.api.discover_schedule_period_id` resolves this at runtime by reading `perId` from `/streetsForTown` for the matching street. Do not hardcode the period ID. The `townsForCommunity` endpoint is unreliable — it sometimes reports a stale ID even when `/streets` rejects it.
