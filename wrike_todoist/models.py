from __future__ import annotations

import dataclasses
from typing import Dict, List, Type, Optional, Union, NamedTuple


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


class Collection:
    members: Dict
    type: Type

    def __len__(self):
        return len(self.members)

    def __contains__(self, item):
        return item.primary_key in self.members

    def __getitem__(self, item):
        return self.members[item]

    def __iter__(self):
        return iter(self.members.values())


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
class WrikeTask(Item):
    id: str
    title: str
    permalink: str

    @property
    def primary_key(self) -> str:
        return self.id

    @property
    def numeric_id(self) -> int:
        return int(self.permalink.split("=")[-1])

    @classmethod
    def from_response(cls, response: Dict) -> WrikeTask:
        return cls(id=response["id"], title=response["title"], permalink=response["permalink"])


@dataclasses.dataclass
class WrikeTaskCollection(Collection):
    members: Dict[Union[str, PendingValue], WrikeTask]
    type = WrikeTask

    @classmethod
    def from_response(cls, response: Dict) -> WrikeTaskCollection:
        return cls(members={item["id"]: cls.type.from_response(item) for item in response["data"]})


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


@dataclasses.dataclass
class TodoistProjectCollection(Collection):
    members: Dict[Union[int, PendingValue], TodoistTask]
    type = TodoistProject

    @classmethod
    def from_response(cls, response: List[Dict]) -> Collection:
        return cls(members={item["name"]: cls.type.from_response(item) for item in response})


@dataclasses.dataclass
class TodoistTask(Item):
    id: Union[int, PendingValue]
    content: str
    description: str
    project_id: str
    parent_id: Optional[str]
    # priority: int
    labels: List[str]

    parent: Optional[TodoistTask] = None
    children: List[TodoistTask] = dataclasses.field(default_factory=list)

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
            parent_id=response["parent_id"],
            # priority=response["priority"],
            labels=response["labels"],
        )

    def update_from_response(self, response: Dict):
        self.id = response.get("id") or self.id
        self.content = response.get("content") or self.content
        self.description = response.get("description") or self.description


class TaskComparisonResult(NamedTuple):
    to_add: TodoistTaskCollection
    to_update: TodoistTaskCollection
    to_complete: TodoistTaskCollection


@dataclasses.dataclass
class TodoistTaskCollection(Collection):
    members: Dict[Union[str, PendingValue], TodoistTask] = dataclasses.field(default_factory=dict)
    type = TodoistTask

    @classmethod
    def from_response(cls, response: List[Dict]) -> TodoistTaskCollection:
        return cls(members={item["content"]: cls.type.from_response(item) for item in response})

    @classmethod
    def from_wrike_tasks(cls, wrike_tasks: WrikeTaskCollection, todoist_project_id: str) -> TodoistTaskCollection:
        tasks = {}
        for wrike_task in wrike_tasks:
            primary_key = PendingValue()
            content = f"[#{wrike_task.numeric_id}] {wrike_task.title}"
            todoist_task = TodoistTask(
                id=PendingValue(),
                description=wrike_task.permalink,
                content=content,
                project_id=todoist_project_id,
                parent_id=None,
                # priority=0,
                labels=["Wrike"],
            )
            tasks[primary_key] = todoist_task
        return cls(members=tasks)

    @classmethod
    def compare(cls, wrike_tasks: TodoistTaskCollection, todoist_tasks: TodoistTaskCollection) -> TaskComparisonResult:
        to_add = TodoistTaskCollection()
        to_update = TodoistTaskCollection()
        to_complete = TodoistTaskCollection()

        print(todoist_tasks)

        for wrike_task in wrike_tasks:

            print(wrike_task)

            if wrike_task in todoist_tasks:
                to_update.members[wrike_task.primary_key] = wrike_task
            else:
                to_add.members[wrike_task.primary_key] = wrike_task
        return TaskComparisonResult(to_add=to_add, to_update=to_update, to_complete=to_complete)


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
    members: Dict[Union[str, PendingValue], TodoistLabel]
    type = TodoistLabel

    @classmethod
    def from_response(cls, response: List[Dict]) -> Collection:
        return cls(members={item["name"]: cls.type.from_response(item) for item in response})
