import datetime
import http
import uuid

import requests

from wrike_todoist import models, config
from wrike_todoist.api_utils import response_to_json_value
from wrike_todoist.todoist import models
from wrike_todoist.wrike.api import logger


def todoist_get_project_by_name(name: str) -> models.TodoistProject:
    todoist_projects_response = requests.get(
        "https://api.todoist.com/rest/v2/projects",
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )
    todoist_projects = models.TodoistProjectCollection.from_response(
        response_to_json_value(todoist_projects_response)
    )
    logger.info(f"Retrieved {len(todoist_projects)} Todoist Projects.")
    todoist_project = todoist_projects.get(name=name)
    logger.info(f"{name} is a valid Todoist Project.")
    return todoist_project


def todoist_get_or_create_label(name: str) -> models.TodoistLabel:
    todoist_labels_response = requests.get(
        "https://api.todoist.com/rest/v2/labels",
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )

    todoist_labels = models.TodoistLabelCollection.from_response(
        response_to_json_value(todoist_labels_response)
    )
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
        todoist_label = models.TodoistLabel.from_response(
            response_to_json_value(todoist_label_response)
        )
        logger.info(f"Successfully created Todoist Label {todoist_label.name}")
        return todoist_label


def todoist_get_tasks(
    todoist_project: models.TodoistProject, only_due_today: bool = False
) -> models.TodoistTaskCollection:
    todoist_tasks_response = requests.get(
        "https://api.todoist.com/rest/v2/tasks/",
        params={"project_id": todoist_project.id},
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )
    response_as_list_of_dict = response_to_json_value(todoist_tasks_response)
    todoist_task_collection = models.TodoistTaskCollection.from_response(
        response_as_list_of_dict
    )
    logger.info(f"Retrieved {len(todoist_task_collection)} Todoist Tasks.")
    return todoist_task_collection


def todoist_get_completed_task(task_id: int) -> models.TodoistTask:
    todoist_task_response = requests.get(
        "https://api.todoist.com/sync/v9/items/get",
        params={
            "item_id": task_id,
        },
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )
    task_data = response_to_json_value(todoist_task_response)
    return models.TodoistTask.from_response(task_data["item"])


def todoist_get_completed_tasks(
    todoist_project: models.TodoistProject, since: datetime.datetime
) -> models.TodoistTaskCollection:
    todoist_tasks_response = requests.get(
        "https://api.todoist.com/sync/v9/completed/get_all",
        params={
            "project_id": todoist_project.id,
            "since": since.isoformat(),
        },
        headers={"Authorization": f"Bearer {config.config.todoist_access_token}"},
    )

    todoist_tasks = []
    for rudimentary_task_data in response_to_json_value(todoist_tasks_response).get(
        "items", []
    ):
        todoist_task = todoist_get_completed_task(rudimentary_task_data["task_id"])
        todoist_tasks.append(todoist_task)

    return models.TodoistTaskCollection(*todoist_tasks)


def todoist_create_tasks(
    todoist_tasks: models.TodoistTaskCollection,
) -> models.TodoistTaskCollection:
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

        created_todoist_task = models.TodoistTask.from_response(
            response_to_json_value(create_task_response)
        )
        logger.info(f"Created new Todoist Task {todoist_task.content}")
        created[created_todoist_task.permalink] = created_todoist_task

    return models.TodoistTaskCollection(*created.values())


def todoist_update_tasks(
    todoist_tasks: models.TodoistTaskCollection,
) -> models.TodoistTaskCollection:
    updated = {}

    for todoist_task in todoist_tasks:
        update_task_response = requests.post(
            f"https://api.todoist.com/rest/v2/tasks/{todoist_task.id}",
            headers={
                "Authorization": f"Bearer {config.config.todoist_access_token}",
                "X-Request-Id": uuid.uuid4().hex,
            },
            json=todoist_task.serialize(only={"content", "description", "priority"}),
        )
        update_task_response.raise_for_status()  # @TODO: or maybe load the contents?
        logger.info(f"Updated Todoist Task {todoist_task.content}")
        updated[todoist_task.permalink] = todoist_task

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
            closed[todoist_task.permalink] = todoist_task
            logger.info(f"Closed Todoist Task {todoist_task.permalink}.")

    return models.TodoistTaskCollection(*closed.values())


def todoist_remove_tasks(todoist_tasks: models.TodoistTaskCollection):
    removed = {}

    for todoist_task in todoist_tasks:
        remove_task_response = requests.delete(
            f"https://api.todoist.com/rest/v2/tasks/{todoist_task.id}",
            headers={
                "Authorization": f"Bearer {config.config.todoist_access_token}",
                "X-Request-Id": uuid.uuid4().hex,
            },
        )
        if remove_task_response.status_code == http.HTTPStatus.NO_CONTENT:
            removed[todoist_task.permalink] = todoist_task
            logger.info(f"Removed Todoist Task {todoist_task.permalink}.")

    return models.TodoistTaskCollection(*removed.values())
