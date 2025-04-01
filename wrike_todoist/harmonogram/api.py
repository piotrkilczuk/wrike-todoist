import pendulum
import requests

from wrike_todoist.api_utils import response_to_json_value
from wrike_todoist.harmonogram import models
from wrike_todoist.models import Collection


def pull_future_collection_days() -> Collection:
    schedules_response = requests.post(
        "https://pluginssl.ecoharmonogram.pl/api/v1/plugin/v1/schedules",
        data={
            "number": "188/E/1",
            "schedulegroup": "j",
            "streetId": "20305587",
        },
    )
    schedules_list = response_to_json_value(schedules_response, "utf-8-sig")

    all_collections = models.CollectionDayCollection.from_response(schedules_list)
    future_collections = all_collections.filter(
        lambda c: c.date >= pendulum.today().date()
    )

    return future_collections
