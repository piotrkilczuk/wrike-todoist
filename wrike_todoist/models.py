from __future__ import annotations

import dataclasses
import enum
import logging
from typing import Dict, List, Type, Optional, Union, NamedTuple, TypeVar, Any, Callable

from wrike_todoist import config

logger = logging.getLogger(__name__)


class PendingValue:
    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f"<PendingValue #{id(self)}>"


class Item:
    def serialize(self) -> Dict:
        data = {}
        for field in dataclasses.fields(self):
            name = field.name
            value = getattr(self, name)
            if not isinstance(value, PendingValue):
                data[name] = value
        return data


CollectionType = TypeVar("CollectionType", bound=Item)


class Collection:
    primary_key_field_name: str
    type: Type[CollectionType]

    _members: List[CollectionType]

    def __init__(self, *members: CollectionType):
        for member in members:
            if not isinstance(member, self.type):
                raise ValueError(f"Invalid member {member}. Required type is {self.type}.")
        self._members = list(members)

    def __iter__(self):
        return iter(self._members)

    def __len__(self):
        return len(self._members)

    def __contains__(self, item):
        try:
            self.get(**{self.primary_key_field_name: getattr(item, self.primary_key_field_name)})
            return True
        except ValueError:
            return False

    def __getitem__(self, index):
        return self._members[index]

    def __add__(self, other: CollectionType):
        if isinstance(other, Collection):
            self._members += other._members
        else:
            self._members.append(other)
        return self

    def filter(self, fn: Optional[Callable[[Item], bool]] = None, **fields: Any) -> Collection:
        if fn and fields:
            raise ValueError("Use either fn or **fields.")

        collection_type = type(self)
        members = []

        for item in self:
            if fn and fn(item):
                members.append(item)

            for field_name, field_value in fields.items():
                if getattr(item, field_name) != field_value:
                    break
            else:
                members.append(item)

        return collection_type(*members)

    def get(self, fn: Optional[Callable[[Item], bool]] = None, **fields: Any) -> CollectionType:
        filtered = self.filter(fn, **fields)
        if not filtered:
            raise ValueError(f"No objects found - {fn=} {fields=}.")
        if len(filtered) > 1:
            raise ValueError(f"Multiple objects found - {fn=} {fields=}.")
        return filtered[0]


@dataclasses.dataclass
class WrikeUser(Item):
    id: str

    @property
    def primary_key(self) -> str:
        return self.id

    @classmethod
    def from_response(cls, response: Dict) -> WrikeUser:
        return cls(id=response["data"][0]["id"])


@dataclasses.dataclass
class WrikeFolder(Item):
    id: str
    title: str

    @property
    def primary_key(self):
        return self.title

    @classmethod
    def from_response(cls, response: Dict):
        return cls(id=response["id"], title=response["title"])


class WrikeFolderCollection(Collection):
    type = WrikeFolder

    @classmethod
    def from_response(cls, response: Dict) -> WrikeFolderCollection:
        return cls(*[cls.type.from_response(item) for item in response["data"]])


@dataclasses.dataclass
class WrikeTask(Item):
    id: str
    title: str
    permalink: str
    sub_task_ids: List[str]

    @property
    def primary_key(self) -> str:
        return self.id

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


@dataclasses.dataclass
class TodoistProject(Item):
    id: int
    name: str

    @property
    def primary_key(self) -> str:
        return self.name

    @classmethod
    def from_response(cls, response: Dict) -> TodoistProject:
        return cls(id=response["id"], name=response["name"])


class TodoistProjectCollection(Collection):
    type = TodoistProject

    @classmethod
    def from_response(cls, response: List[Dict]) -> TodoistProjectCollection:
        return cls(*[cls.type.from_response(item) for item in response])


class TodoistTaskPriorityMapping(enum.IntEnum):
    P1 = 4
    P2 = 3
    P3 = 2
    P4 = 1


@dataclasses.dataclass
class TodoistTask(Item):
    id: Union[int, PendingValue]
    content: str
    description: str
    project_id: int
    labels: List[str]
    priority: int = TodoistTaskPriorityMapping[config.config.todoist_default_priority]

    @property
    def primary_key(self) -> str:
        return self.content

    @classmethod
    def from_response(cls, response: Dict) -> TodoistTask:
        return cls(
            id=response["id"],
            content=response["content"],
            description=response["description"],
            project_id=response["project_id"],
            labels=response["labels"],
        )

    def update_from_response(self, response: Dict):
        self.id = response.get("id") or self.id
        self.content = response.get("content") or self.content
        self.description = response.get("description") or self.description


class TaskComparisonResult(NamedTuple):
    to_add: TodoistTaskCollection
    to_close: TodoistTaskCollection


class TodoistTaskCollection(Collection):
    primary_key_field_name = "content"
    type = TodoistTask

    @classmethod
    def from_response(cls, response: List[Dict]) -> TodoistTaskCollection:
        return cls(*[cls.type.from_response(item) for item in response])

    @classmethod
    def from_wrike_tasks(cls, wrike_tasks: WrikeTaskCollection, todoist_project_id: int) -> TodoistTaskCollection:
        tasks = []

        for wrike_task in wrike_tasks:
            if wrike_task.sub_task_ids:
                logger.info(f"Skipping Wrike Task {wrike_task.primary_key} as has sub-tasks.")
                continue

            content = f"[#{wrike_task.numeric_id}] {wrike_task.title}"
            todoist_task = TodoistTask(
                id=PendingValue(),
                description=wrike_task.permalink,
                content=content,
                project_id=todoist_project_id,
                priority=config.config.todoist_default_priority,
                labels=["Wrike"],
            )
            tasks.append(todoist_task)

        return cls(*tasks)

    @classmethod
    def compare(cls, wrike_tasks: TodoistTaskCollection, todoist_tasks: TodoistTaskCollection) -> TaskComparisonResult:
        to_add = TodoistTaskCollection()
        to_skip = TodoistTaskCollection()
        to_close = TodoistTaskCollection()

        for wrike_task in wrike_tasks:
            if wrike_task not in todoist_tasks:
                to_add += wrike_task
                logger.info(f"Need to add task {wrike_task.primary_key}.")
            else:
                to_skip += wrike_task
                logger.info(f"Skipping Wrike Task {wrike_task.primary_key} as already in Todoist.")

        for todoist_task in todoist_tasks:
            if todoist_task not in to_skip:
                to_close += todoist_task
                logger.info(f"Need to complete task {todoist_task.primary_key}.")

        return TaskComparisonResult(to_add=to_add, to_close=to_close)


@dataclasses.dataclass
class TodoistLabel(Item):
    id: Union[int, PendingValue]
    name: str

    @property
    def primary_key(self) -> str:
        return self.name

    @classmethod
    def from_response(cls, response: Dict) -> TodoistLabel:
        return cls(id=response["id"], name=response["name"])


@dataclasses.dataclass
class TodoistLabelCollection(Collection):
    type = TodoistLabel

    @classmethod
    def from_response(cls, response: List[Dict]) -> TodoistLabelCollection:
        return cls(*[cls.type.from_response(item) for item in response])
