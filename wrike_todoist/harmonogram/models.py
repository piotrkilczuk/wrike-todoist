from __future__ import annotations

import dataclasses
from urllib.parse import urlencode, quote

import pendulum

from wrike_todoist.models import Collection


@dataclasses.dataclass
class CollectionDay:
    date: pendulum.Date
    description: str

    @classmethod
    def from_response(
        cls, response: dict, description_map: dict
    ) -> list[CollectionDay]:
        """
        Returns a list, because a single row in response can contain multiple collections.
        """
        year = int(response["year"])
        month = int(response["month"])
        days = [int(d) for d in response["days"].split(";")]

        collections = []
        for day in days:
            date = pendulum.Date(year=year, month=month, day=day)
            collections.append(
                cls(
                    date=date,
                    description=description_map[response["scheduleDescriptionId"]],
                )
            )

        return collections

    @property
    def permalink(self) -> str:
        base_url = "https://pluginssl.ecoharmonogram.pl/pluginssl/show/rzeszow.php?community=rzeszow&schedulegroup=true#/community/60/schedules"
        tail = ":".join([self.date.isoformat(), quote(self.description)])
        return base_url + "&" + tail


class CollectionDayCollection(Collection):
    type = CollectionDay
    primary_key_field_name = "permalink"

    @classmethod
    def from_response(cls, response: dict) -> CollectionDayCollection:
        description_map = {}
        for description_dict in response["scheduleDescription"]:
            description_map[description_dict["id"]] = description_dict[
                "name"
            ].capitalize()

        all_collections = []
        for collection_dict in response["schedules"]:
            months_collections = CollectionDay.from_response(
                collection_dict, description_map
            )
            all_collections.extend(months_collections)

        return cls(*all_collections)
