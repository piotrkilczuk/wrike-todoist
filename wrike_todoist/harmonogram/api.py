import pendulum
import requests

from wrike_todoist.api_utils import response_to_json_value
from wrike_todoist.harmonogram import models
from wrike_todoist.models import Collection


HOUSE_NUMBER = "188/E/1"
SCHEDULE_PERIOD_ID = 10351
BASE_URL = "https://api.ecoharmonogram.pl/v1/plugin/v1"


def find_street_id(street_name: str) -> int:
    payload = {
        "groupId": 1,
        "number": HOUSE_NUMBER,
        "schedulePeriodId": SCHEDULE_PERIOD_ID,
        "schedulegroup": "j",
        "streetName": street_name,
        "townId": 1119,
    }
    streets_response = requests.post(
        f"{BASE_URL}/streets",
        data=payload,
    )
    streets = response_to_json_value(streets_response, "utf-8-sig")

    if streets is None:
        raise ValueError(
            f"API returned null for street '{street_name}' — schedulePeriodId may be stale"
        )

    for street in streets["streets"]:
        if street["numbers"] == HOUSE_NUMBER:
            return int(street["id"])

    raise ValueError(
        f"No street found with house number {HOUSE_NUMBER} in {len(streets['streets'])} results"
    )


def pull_future_collection_days(street_id: int) -> Collection:
    schedules_response = requests.post(
        f"{BASE_URL}/schedules",
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
