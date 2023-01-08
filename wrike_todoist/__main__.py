#!/usr/bin/env python
import json
from os import environ
from pprint import pformat

from requests import get, post

from wrike_todoist import models

WRIKE_ACCESS_TOKEN = environ["WRIKE_ACCESS_TOKEN"]
TODOIST_ACCESS_TOKEN = environ["TODOIST_ACCESS_TOKEN"]
TODOIST_PROJECT_NAME = environ["TODOIST_PROJECT_NAME"]
TODOIST_LABEL = environ["TODOIST_LABEL"]

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
        "subTasks": True,
        "fields": "[description,briefDescription,superTaskIds,subTaskIds]",
        "limit": 500,
    },
)
wrike_tasks = models.WrikeTaskCollection.from_response(wrike_tasks_response.json())

todoist_projects_response = get(
    "https://api.todoist.com/rest/v2/projects",
    headers={"Authorization": f"Bearer {TODOIST_ACCESS_TOKEN}"},
)

todoist_projects = models.TodoistProjectCollection.from_response(todoist_projects_response.json())

todoist_project = todoist_projects[TODOIST_PROJECT_NAME]

todoist_labels_response = get(
    "https://api.todoist.com/rest/v2/labels",
    headers={"Authorization": f"Bearer {TODOIST_ACCESS_TOKEN}"},
)

todoist_labels = models.TodoistLabelCollection.from_response(todoist_labels_response.json())

try:
    todoist_label = todoist_labels[TODOIST_LABEL]
except KeyError:
    todoist_label = models.TodoistLabel(id=models.PendingValue(), name=TODOIST_LABEL)

    todoist_label_response = post(
        "https://api.todoist.com/rest/v2/labels",
        headers={"Authorization": f"Bearer {TODOIST_ACCESS_TOKEN}"},
        json=todoist_label.serialize(),
    )

    todoist_label = models.TodoistLabel.from_response(todoist_label_response.json())

todoist_tasks_response = get(
    "https://api.todoist.com/rest/v2/tasks",
    params={"project_id": todoist_project.id, "label": TODOIST_LABEL},
    headers={"Authorization": f"Bearer {TODOIST_ACCESS_TOKEN}"},
)
actual_todoist_tasks = models.TodoistTaskCollection.from_response(todoist_tasks_response.json())

expected_todoist_tasks = models.TodoistTaskCollection.from_wrike_tasks(wrike_tasks, todoist_project.id)

comparison_result = models.TodoistTaskCollection.compare(expected_todoist_tasks, actual_todoist_tasks)

for todoist_task in comparison_result.to_add:
    create_task_response = post(
        "https://api.todoist.com/rest/v2/tasks",
        headers={"Authorization": f"Bearer {TODOIST_ACCESS_TOKEN}"},
        json=todoist_task.serialize(),
    )
    print(json.dumps(todoist_task.serialize()))
    # todoist_task.update_from_response(create_task_response.json())
    raise NotImplementedError(create_task_response.text, todoist_task)

for todoist_task in comparison_result.to_update:
    raise NotImplementedError(todoist_task)


raise NotImplementedError(len(actual_todoist_tasks), len(expected_todoist_tasks), pformat(comparison_result))
