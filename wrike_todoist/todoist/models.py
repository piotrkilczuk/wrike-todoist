from __future__ import annotations

import dataclasses
import enum
import re
from typing import Dict, List, Union, NamedTuple

from wrike_todoist import config
from wrike_todoist.models import Item, Collection, PendingValue, logger


@dataclasses.dataclass
class TodoistProject(Item):
    id: int
    name: str

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

    RE_PRIMARY_KEY = re.compile(r"\[#([\d]+)\]")

    @property
    def wrike_numeric_id(self) -> str:
        match = self.RE_PRIMARY_KEY.search(self.content)
        if match is None:
            raise ValueError(f"Unable to infer wrike_numeric_id from: {self.content}")
        return match.group(1)

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
    to_update: TodoistTaskCollection
    to_close: TodoistTaskCollection


class TodoistTaskCollection(Collection):
    primary_key_field_name = "description"
    type = TodoistTask

    @classmethod
    def from_response(cls, response: List[Dict]) -> TodoistTaskCollection:
        return cls(*[cls.type.from_response(item) for item in response])

    # @TODO: This should be an adapter, outside of the per-service model
    @classmethod
    def from_wrike_tasks(cls, wrike_tasks: Collection, todoist_project_id: int) -> TodoistTaskCollection:
        tasks = []

        for wrike_task in wrike_tasks:
            if wrike_task.sub_task_ids:
                logger.info(f"Skipping Wrike Task {wrike_task.numeric_id} as has sub-tasks.")
                continue

            content = f"[#{wrike_task.numeric_id}] {wrike_task.title}"
            todoist_task = TodoistTask(
                id=PendingValue(),
                description=wrike_task.permalink,
                content=content,
                project_id=todoist_project_id,
                labels=["Wrike"],
            )
            tasks.append(todoist_task)

        return cls(*tasks)

    @classmethod
    def compare(cls, wrike_tasks: TodoistTaskCollection, todoist_tasks: TodoistTaskCollection) -> TaskComparisonResult:
        to_add = TodoistTaskCollection()
        to_update = TodoistTaskCollection()
        to_close = TodoistTaskCollection()

        for wrike_task in wrike_tasks:
            if wrike_task not in todoist_tasks:
                to_add += wrike_task
                logger.info(f"Need to add task {wrike_task.wrike_numeric_id}.")

            else:
                todoist_task = todoist_tasks.get(description=wrike_task.description)
                todoist_task.content = wrike_task.content
                todoist_task.description = wrike_task.description
                to_update += todoist_task
                logger.info(f"Need to update task {wrike_task.wrike_numeric_id}.")

        for todoist_task in todoist_tasks:
            if (todoist_task not in to_add) and (todoist_task not in to_update):
                to_close += todoist_task
                logger.info(f"Need to complete task {todoist_task.wrike_numeric_id}.")

        return TaskComparisonResult(to_add=to_add, to_update=to_update, to_close=to_close)


@dataclasses.dataclass
class TodoistLabel(Item):
    id: Union[int, PendingValue]
    name: str

    @classmethod
    def from_response(cls, response: Dict) -> TodoistLabel:
        return cls(id=response["id"], name=response["name"])


@dataclasses.dataclass
class TodoistLabelCollection(Collection):
    type = TodoistLabel

    @classmethod
    def from_response(cls, response: List[Dict]) -> TodoistLabelCollection:
        return cls(*[cls.type.from_response(item) for item in response])
