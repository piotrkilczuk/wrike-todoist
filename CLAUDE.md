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

The ecoharmonogram.pl API changes `schedulePeriodId` periodically.
When it goes stale, the `/streets` endpoint returns JSON `null` with HTTP 200.
To find the current ID, POST to `/streetsForTown` with `townId=1119` and read the `perId` field of the matching street. The `townsForCommunity` endpoint is unreliable — it sometimes reports a stale ID even when `/streets` rejects it.
