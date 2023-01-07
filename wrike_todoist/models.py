from __future__ import annotations

import dataclasses
from typing import Dict, List, Type, Optional, Union


class PendingPrimaryKey:
    def __hash__(self):
        return id(self)


class Collection:
    members: Dict
    type: Type

    def __len__(self):
        return len(self.members)

    def __getitem__(self, item):
        return self.members[item]

    def __iter__(self):
        return iter(self.members.values())


@dataclasses.dataclass
class WrikeUser:
    id: str

    @property
    def primary_key(self) -> str:
        return self.id

    @classmethod
    def from_response(cls, response: Dict) -> WrikeUser:
        return cls(id=response["data"][0]["id"])


@dataclasses.dataclass
class WrikeTask:
    id: str
    title: str
    permalink: str

    @property
    def primary_key(self) -> str:
        return self.id

    @classmethod
    def from_response(cls, response: Dict) -> WrikeTask:
        return cls(id=response["id"], title=response["title"], permalink=response["permalink"])


@dataclasses.dataclass
class WrikeTaskCollection(Collection):
    members: Dict[Union[str, PendingPrimaryKey], WrikeTask]
    type = WrikeTask

    @classmethod
    def from_response(cls, response: Dict) -> WrikeTaskCollection:
        return cls(members={item["id"]: cls.type.from_response(item) for item in response["data"]})


@dataclasses.dataclass
class TodoistProject:
    id: int
    name: str

    @property
    def primary_key(self) -> str:
        return self.name

    @classmethod
    def from_response(cls, response: Dict) -> TodoistProject:
        return cls(id=response["id"], name=response["name"])


@dataclasses.dataclass
class TodoistProjectCollection(Collection):
    members: Dict[Union[int, PendingPrimaryKey], TodoistTask]
    type = TodoistProject

    @classmethod
    def from_response(cls, response: List[Dict]) -> Collection:
        return cls(members={item["name"]: cls.type.from_response(item) for item in response})


@dataclasses.dataclass
class TodoistTask:
    content: str
    description: str
    project_id: str
    parent_id: Optional[str]
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
    members: Dict[Union[str, PendingPrimaryKey], TodoistTask]
    type = TodoistTask

    @classmethod
    def from_response(cls, response: List[Dict]) -> Collection:
        return cls(members={item["id"]: cls.type.from_response(item) for item in response})

    @classmethod
    def from_wrike_tasks(cls, wrike_tasks: WrikeTaskCollection, todoist_project_id: str) -> TodoistTaskCollection:
        tasks = {}
        for wrike_task in wrike_tasks:
            primary_key = PendingPrimaryKey()
            description = f"[{wrike_task.id}] {wrike_task.title}"
            todoist_task = TodoistTask(
                content=wrike_task.permalink,
                description=description,
                project_id=todoist_project_id,
                parent_id=None,
                priority=0,
                labels=["Wrike"],
            )
            tasks[primary_key] = todoist_task
        return cls(members=tasks)
