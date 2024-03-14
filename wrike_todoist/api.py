import http
import logging
from typing import Union
import uuid

import requests

from wrike_todoist import models, config

logger = logging.getLogger(__name__)


JSONValue = Union[dict, list, str, int, float, bool, None]


def response_to_json_value(response: requests.Response) -> JSONValue:
    try:
        response.raise_for_status()
    except requests.HTTPError:
        logger.error(f"Response is {response.status_code}: {response.text}")
        raise

    try:
        return response.json()
    except requests.JSONDecodeError:
        logger.error(f"Failed to decode response {response.text}")
        raise


def wrike_get_current_user() -> models.WrikeUser:
    wrike_user_response = requests.get(
        "https://www.wrike.com/api/v4/contacts?me=true",
        params={"access_token": config.config.wrike_access_token},
    )
    wrike_user = models.WrikeUser.from_response(response_to_json_value(wrike_user_response))
    logger.info(f"Retrieved Wrike User {wrike_user.id}.")
    return wrike_user


def wrike_get_folders() -> models.WrikeFolderCollection:
    wrike_folders_response = requests.get(
        "https://www.wrike.com/api/v4/folders",
        params={"access_token": config.config.wrike_access_token},
    )
    wrike_folder_collection = models.WrikeFolderCollection.from_response(response_to_json_value(wrike_folders_response))
    logger.info(f"Retrieved {len(wrike_folder_collection)} Wrike Folders.")
    return wrike_folder_collection


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
    wrike_task_collection = models.WrikeTaskCollection.from_response(response_to_json_value(wrike_tasks_response))
    logger.info(
        f"Retrieved {len(wrike_task_collection)} Wrike Tasks "
        f"for user {wrike_user.id} under Folder {wrike_folder.title}"
    )
    return wrike_task_collection


def todoist_get_project_by_name(name: str) -> models.TodoistProject:
    todoist_projects_response = requests.get(
        "https://api.todoist.com/rest/v2/projects",
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )
    todoist_projects = models.TodoistProjectCollection.from_response(response_to_json_value(todoist_projects_response))
    logger.info(f"Retrieved {len(todoist_projects)} Todoist Projects.")
    todoist_project = todoist_projects.get(name=name)
    logger.info(f"{name} is a valid Todoist Project.")
    return todoist_project


def todoist_get_or_create_label(name: str) -> models.TodoistLabel:
    todoist_labels_response = requests.get(
        "https://api.todoist.com/rest/v2/labels",
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )

    todoist_labels = models.TodoistLabelCollection.from_response(response_to_json_value(todoist_labels_response))
    logger.info(f"Retrieved {len(todoist_labels)} Todoist Labels.")

    try:
        todoist_label = todoist_labels[name]
        logger.info(f"{name} is an existing Todoist Label.")
        return todoist_label

    except KeyError:
        logger.info(f"{name} is not an existing Todoist Label, need to create.")
        todoist_label = models.TodoistLabel(id=models.PendingValue(), name=name)

        todoist_label_response = requests.post(
            "https://api.todoist.com/rest/v2/labels",
            headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
            json=todoist_label.serialize(),
        )
        todoist_label = models.TodoistLabel.from_response(response_to_json_value(todoist_label_response))
        logger.info(f"Successfully created Todoist Label {todoist_label.name}")
        return todoist_label


def todoist_get_tasks(todoist_project: models.TodoistProject, todoist_label: str) -> models.TodoistTaskCollection:
    todoist_tasks_response = requests.get(
        "https://api.todoist.com/rest/v2/tasks/",
        params={"project_id": todoist_project.id, "label": todoist_label},
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )
    todoist_task_collection = models.TodoistTaskCollection.from_response(response_to_json_value(todoist_tasks_response))
    logger.info(f"Retrieved {len(todoist_task_collection)} Todoist Tasks.")
    return todoist_task_collection


def todoist_create_tasks(todoist_tasks: models.TodoistTaskCollection) -> models.TodoistTaskCollection:
    created = {}

    for todoist_task in todoist_tasks:
        create_task_response = requests.post(
            "https://api.todoist.com/rest/v2/tasks/",
            headers={
                "Authorization": f"Bearer {config.config.todoist_access_token}",
                "X-Request-Id": uuid.uuid4().hex,
            },
            json=todoist_task.serialize(),
        )

        created_todoist_task = models.TodoistTask.from_response(response_to_json_value(create_task_response))
        logger.info(f"Created new Todoist Task {todoist_task.content}")
        created[created_todoist_task.wrike_numeric_id] = created_todoist_task

    return models.TodoistTaskCollection(*created.values())


def todoist_update_tasks(todoist_tasks: models.TodoistTaskCollection) -> models.TodoistTaskCollection:
    updated = {}

    for todoist_task in todoist_tasks:
        udpate_task_response = requests.post(
            f"https://api.todoist.com/rest/v2/tasks/{todoist_task.id}",
            headers={
                "Authorization": f"Bearer {config.config.todoist_access_token}",
                "X-Request-Id": uuid.uuid4().hex,
            },
            json=todoist_task.serialize(only={"content", "description"}),
        )
        update_task_response.raise_for_status()  # @TODO: or maybe load the contents?
        logger.info(f"Updated Todoist Task {todoist_task.content}")
        updated[todoist_task.wrike_numeric_id] = todoist_task

    return models.TodoistTaskCollection(*updated.values())


def todoist_close_tasks(todist_tasks: models.TodoistTaskCollection):
    closed = {}

    for todoist_task in todist_tasks:
        close_task_response = requests.post(
            f"https://api.todoist.com/rest/v2/tasks/{todoist_task.id}/close",
            headers={
                "Authorization": f"Bearer {config.config.todoist_access_token}",
                "X-Request-Id": uuid.uuid4().hex,
            },
        )
        if close_task_response.status_code == http.HTTPStatus.NO_CONTENT:
            closed[todoist_task.wrike_numeric_id] = todoist_task
            logger.info(f"Closed Todoist Task {todoist_task.wrike_numeric_id}.")

    return models.TodoistTaskCollection(*closed.values())
