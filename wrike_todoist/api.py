import logging
from pprint import pformat

import requests

from wrike_todoist import models, config

logger = logging.getLogger(__name__)


def wrike_get_current_user() -> models.WrikeUser:
    wrike_user_response = requests.get(
        "https://www.wrike.com/api/v4/contacts?me=true",
        params={"access_token": config.config.wrike_access_token},
    )
    return models.WrikeUser.from_response(wrike_user_response.json())


def wrike_get_folders() -> models.WrikeFolderCollection:
    wrike_folders_response = requests.get(
        "https://www.wrike.com/api/v4/folders",
        params={"access_token": config.config.wrike_access_token},
    )
    return models.WrikeFolderCollection.from_response(wrike_folders_response.json())


def wrike_get_tasks(wrike_user: models.WrikeUser, wrike_folder: models.WrikeFolder) -> models.WrikeTaskCollection:
    wrike_tasks_response = requests.get(
        f"https://www.wrike.com/api/v4/folders/{wrike_folder.id}/tasks",
        params={
            "access_token": config.config.wrike_access_token,
            "status": "Active",
            "responsibles": f"[{wrike_user.id}]",
            "subTasks": True,
            "descendants": True,
            "fields": "[description,briefDescription,superTaskIds,subTaskIds]",
            "limit": 500,
        },
    )
    return models.WrikeTaskCollection.from_response(wrike_tasks_response.json())


def todoist_get_project_by_name(name: str) -> models.TodoistProject:
    todoist_projects_response = requests.get(
        "https://api.todoist.com/rest/v2/projects",
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )

    todoist_projects = models.TodoistProjectCollection.from_response(todoist_projects_response.json())

    return todoist_projects[name]


def todoist_get_or_create_label(name: str) -> models.TodoistLabel:
    todoist_labels_response = requests.get(
        "https://api.todoist.com/rest/v2/labels",
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )

    todoist_labels = models.TodoistLabelCollection.from_response(todoist_labels_response.json())

    try:
        return todoist_labels[name]

    except KeyError:
        todoist_label = models.TodoistLabel(id=models.PendingValue(), name=name)

        todoist_label_response = requests.post(
            "https://api.todoist.com/rest/v2/labels",
            headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
            json=todoist_label.serialize(),
        )

        return models.TodoistLabel.from_response(todoist_label_response.json())


def todoist_get_tasks(todoist_project: models.TodoistProject, todoist_label: str) -> models.TodoistTaskCollection:
    todoist_tasks_response = requests.get(
        "https://api.todoist.com/rest/v2/tasks",
        params={"project_id": todoist_project.id, "label": todoist_label},
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )
    return models.TodoistTaskCollection.from_response(todoist_tasks_response.json())


def todoist_create_tasks(todoist_tasks: models.TodoistTaskCollection) -> models.TodoistTaskCollection:
    created = {}

    for todoist_task in todoist_tasks:
        create_task_response = requests.post(
            "https://api.todoist.com/rest/v2/tasks",
            headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
            json=todoist_task.serialize(),
        )
        created_todoist_task = models.TodoistTask.from_response(create_task_response.json())
        created[created_todoist_task.primary_key] = created_todoist_task

    return models.TodoistTaskCollection(members=created)
