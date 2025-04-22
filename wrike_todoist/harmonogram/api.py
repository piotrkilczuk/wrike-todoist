import pendulum
import requests

from wrike_todoist.api_utils import response_to_json_value
from wrike_todoist.harmonogram import models
from wrike_todoist.models import Collection


HOUSE_NUMBER = "188/E/1"


def find_street_id(street_name: str) -> int:
    payload = {
        "groupId": 1,
        "number": HOUSE_NUMBER,
        "schedulePeriodId": 7781,
        "schedulegroup": "j",
        "streetName": street_name,
        "townId": 1119,
    }
    streets_response = requests.post(
        "https://pluginssl.ecoharmonogram.pl/api/v1/plugin/v1/streets",
        data=payload,
    )
    streets = response_to_json_value(streets_response, "utf-8-sig")
    return int(streets["streets"][0]["id"])


def pull_future_collection_days(street_id: int) -> Collection:
    schedules_response = requests.post(
        "https://pluginssl.ecoharmonogram.pl/api/v1/plugin/v1/schedules",
        data={
            "number": HOUSE_NUMBER,
            "schedulegroup": "j",
            "streetId": street_id,
        },
    )
    schedules_list = response_to_json_value(schedules_response, "utf-8-sig")

    all_collections = models.CollectionDayCollection.from_response(schedules_list)
    future_collections = all_collections.filter(
        lambda c: c.date >= pendulum.today().date()
    )

    return future_collections
