from __future__ import annotations

import dataclasses
from typing import Dict, List, Type


class Collection:
    members: List
    type: Type

    def __iter__(self):
        return iter(self.members)


@dataclasses.dataclass
class WrikeUser:
    id: str

    @classmethod
    def from_response(cls, response: Dict) -> WrikeUser:
        return cls(id=response["data"][0]["id"])


@dataclasses.dataclass
class WrikeTask:
    id: str
    title: str
    permalink: str

    @classmethod
    def from_response(cls, response: Dict) -> WrikeTask:
        return cls(id=response["id"], title=response["title"], permalink=response["permalink"])


@dataclasses.dataclass
class WrikeTaskCollection(Collection):
    members: List[WrikeTask]
    type = WrikeTask

    @classmethod
    def from_response(cls, response: List[Dict]) -> Collection:
        return cls(members=[cls.type.from_response(item) for item in response["data"]])


@dataclasses.dataclass
class TodoistTask:
    content: str
    description: str
    project_id: str
    parent_id: str
    priority: int
    labels: List[str]

    @classmethod
    def from_response(cls, response: Dict) -> TodoistTask:
        return cls(
            content=response["content"],
            description=response["description"],
            project_id=response["project_id"],
            parent_id=response["parent_id"],
            priority=response["priority"],
            labels=response["labels"],
        )


@dataclasses.dataclass
class TodoistTaskCollection(Collection):
    members: List[TodoistTask]
    type = TodoistTask

    @classmethod
    def from_response(cls, response: List[Dict]) -> Collection:
        return cls(members=[cls.type.from_response(item) for item in response])
