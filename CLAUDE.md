# wrike-todoist

Python app that syncs external sources into Todoist:

* Google Calendar
* GitHub Issues and Pull Requests
* Bin collections via ecoharmonogram.pl

Deployed as AWS Lambda functions.

## Style

- Black formatter, line-length 120
- Always use single-line commit messages, no co-authors, no emojis, no prefixes.

## Tools

### Sentry

- Organization: `kilczukdev-zi`, region: `https://de.sentry.io`
- Project: `python-awslambda`

## Quirks

### ecoharmonogram API

The ecoharmonogram.pl API changes `schedulePeriodId` periodically. 
When it goes stale, the API returns JSON `null` with HTTP 200. 
If you see this, find the new period ID via the `townsForCommunity` endpoint (communityId=60).
