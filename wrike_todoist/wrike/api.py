from itertools import chain
import logging

import requests

from wrike_todoist import config
from wrike_todoist.api_utils import response_to_json_value
from wrike_todoist.wrike import models

logger = logging.getLogger(__name__)


def wrike_get_current_user() -> models.WrikeUser:
    wrike_user_response = requests.get(
        "https://www.wrike.com/api/v4/contacts?me=true",
        params={"access_token": config.config.wrike_access_token},
    )
    wrike_user = models.WrikeUser.from_response(
        response_to_json_value(wrike_user_response)
    )
    logger.info(f"Retrieved Wrike User {wrike_user.id}.")
    return wrike_user


def wrike_get_folders() -> models.WrikeFolderCollection:
    wrike_folders_response_preparatory = requests.get(
        "https://www.wrike.com/api/v4/folders",
        params={"access_token": config.config.wrike_access_token},
    )

    wrike_folder_ids = [
        folder["id"] for folder in wrike_folders_response_preparatory.json()["data"]
    ]
    wrike_folder_ids_partitioned = [
        wrike_folder_ids[i : i + 100] for i in range(0, len(wrike_folder_ids), 100)
    ]

    wrike_folders_response_batched = [
        requests.get(
            f"https://www.wrike.com/api/v4/folders/{','.join(folders)}",
            params={
                "access_token": config.config.wrike_access_token,
            },
        )
        for folders in wrike_folder_ids_partitioned
    ]
    wrike_folders_response_chained = list(
        chain(
            *[response_to_json_value(r)["data"] for r in wrike_folders_response_batched]
        )
    )
    wrike_folder_collection = models.WrikeFolderCollection.from_response(
        wrike_folders_response_chained
    )
    logger.info(f"Retrieved {len(wrike_folder_collection)} Wrike Folders.")
    return wrike_folder_collection


def wrike_get_tasks(
    wrike_user: models.WrikeUser, wrike_folder: models.WrikeFolder
) -> models.WrikeTaskCollection:
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
    wrike_task_collection = models.WrikeTaskCollection.from_response(
        response_to_json_value(wrike_tasks_response)
    )
    logger.info(
        f"Retrieved {len(wrike_task_collection)} Wrike Tasks "
        f"for user {wrike_user.id} under Folder {wrike_folder.title}"
    )
    return wrike_task_collection
