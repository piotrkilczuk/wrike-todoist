#!/usr/bin/env python
from os import environ
from pprint import pformat

from requests import get

from wrike_todoist import models

WRIKE_ACCESS_TOKEN = environ["WRIKE_ACCESS_TOKEN"]
TODOIST_ACCESS_TOKEN = environ["TODOIST_ACCESS_TOKEN"]
TODOIST_PROJECT_ID = environ["TODOIST_PROJECT_ID"]

wrike_user_response = get(
    "https://www.wrike.com/api/v4/contacts?me=true",
    params={"access_token": WRIKE_ACCESS_TOKEN},
)
wrike_user = models.WrikeUser.from_response(wrike_user_response.json())

wrike_tasks_response = get(
    "https://www.wrike.com/api/v4/tasks",
    params={
        "access_token": WRIKE_ACCESS_TOKEN,
        "status": "Active",
        "responsibles": f"[{wrike_user.id}]",
    },
)
wrike_tasks = models.WrikeTaskCollection.from_response(wrike_tasks_response.json())

todoist_tasks_response = get(
    "https://api.todoist.com/rest/v2/tasks",
    params={"project_id": TODOIST_PROJECT_ID},
    headers={"Authorization": f"Bearer {TODOIST_ACCESS_TOKEN}"},
)
todoist_tasks = models.TodoistTaskCollection.from_response(todoist_tasks_response.json())

raise NotImplementedError(pformat(todoist_tasks))
