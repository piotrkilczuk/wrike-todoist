from __future__ import annotations

import dataclasses
from typing import Dict, List

from wrike_todoist.models import Item, Collection


@dataclasses.dataclass
class WrikeUser(Item):
    id: str

    @classmethod
    def from_response(cls, response: Dict) -> WrikeUser:
        return cls(id=response["data"][0]["id"])


@dataclasses.dataclass
class WrikeFolder(Item):
    id: str
    title: str
    permalink: str

    @classmethod
    def from_response(cls, response: Dict):
        return cls(id=response["id"], title=response["title"], permalink=response["permalink"])


class WrikeFolderCollection(Collection):
    type = WrikeFolder

    @classmethod
    def from_response(cls, response: List[Dict]) -> WrikeFolderCollection:
        return cls(*[cls.type.from_response(item) for item in response])


@dataclasses.dataclass
class WrikeTask(Item):
    id: str
    title: str
    permalink: str
    sub_task_ids: List[str]

    @property
    def numeric_id(self) -> int:
        return int(self.permalink.split("=")[-1])

    @classmethod
    def from_response(cls, response: Dict) -> WrikeTask:
        return cls(
            id=response["id"],
            title=response["title"],
            permalink=response["permalink"],
            sub_task_ids=response["subTaskIds"],
        )


class WrikeTaskCollection(Collection):
    type = WrikeTask

    @classmethod
    def from_response(cls, response: Dict) -> WrikeTaskCollection:
        return cls(*[cls.type.from_response(item) for item in response["data"]])
