from __future__ import annotations

import dataclasses
import enum
import re
from typing import Dict, List, Union, NamedTuple, Optional

import pendulum

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
class Due:
    date: pendulum.Date  # would be good to convert to pendulum.Date
    is_recurring: bool
    datetime: pendulum.DateTime  # would be good to convert to pendulum.DateTime
    string: str
    timezone: str

    @classmethod
    def from_response(cls, response: Union[Dict, None]) -> Union[Due, None]:
        if response is None:
            return None
        raw_datetime = response.get("datetime") or response.get("date")
        datetime = pendulum.parse(raw_datetime) if raw_datetime else None
        timezone = response.get("timezone", "UTC")
        return cls(
            date=pendulum.parse(response["date"]),
            is_recurring=response["is_recurring"],
            datetime=datetime,
            string=response["string"],
            timezone=timezone,
        )


@dataclasses.dataclass
class TodoistTask(Item):
    id: Union[int, PendingValue]
    content: str
    description: str
    project_id: int
    labels: List[str]
    priority: int = TodoistTaskPriorityMapping[config.config.todoist_default_priority]

    # These two are only used during write
    due_string: Optional[str] = None
    due_lang: Optional[str] = None

    # These are only used during read
    due: Optional[Due] = None
    is_completed: bool = False

    RE_PERMALINK = re.compile(r"https?://[^\s<>\"]+")

    @property
    def permalink(self) -> str:
        match = self.RE_PERMALINK.search(self.description)
        if match is None:
            raise ValueError(f"Unable to infer permalink from: {self.description}")
        return match.group(0)

    @classmethod
    def from_response(cls, response: Dict) -> TodoistTask:
        due = Due.from_response(response["due"])
        return cls(
            id=response["id"],
            content=response["content"],
            description=response["description"],
            project_id=response["project_id"],
            labels=response["labels"],
            due=due,
            is_completed=response.get("is_completed", False),
        )

    def update_from_response(self, response: Dict):
        self.id = response.get("id") or self.id
        self.content = response.get("content") or self.content
        self.description = response.get("description") or self.description


class TaskComparisonResult(NamedTuple):
    to_add: TodoistTaskCollection
    to_update: TodoistTaskCollection
    to_close: TodoistTaskCollection
    to_reopen: TodoistTaskCollection


class TodoistTaskCollection(Collection):
    primary_key_field_name = "description"
    type = TodoistTask

    RE_PRIORITY = r"\b([Pp][1-4])\b"

    @classmethod
    def from_response(cls, response: List[Dict]) -> TodoistTaskCollection:
        return cls(*[cls.type.from_response(item) for item in response])

    @classmethod
    def from_harmonogram(
        cls, collection_days: Collection, todoist_project_id: int
    ) -> TodoistTaskCollection:
        tasks = []

        for collection_day in collection_days:
            day_before = collection_day.date.subtract(days=1)

            todoist_task = TodoistTask(
                id=PendingValue(),
                content=collection_day.description,
                description=collection_day.permalink,
                project_id=todoist_project_id,
                due_string=day_before.isoformat(),
                due_lang="en",
                labels=["Harmonogram"],
                priority=TodoistTaskPriorityMapping.P1.value,
            )
            tasks.append(todoist_task)

        return cls(*tasks)

    #  @TODO: This should be an adapter, outside of the per-service model
    @classmethod
    def from_calendar_events(
        cls, calendar_events: Collection, todoist_project_id: int
    ) -> TodoistTaskCollection:
        tasks = []

        for calendar_event in calendar_events:
            due_time = calendar_event.start.dateTime.time().isoformat(
                timespec="minutes"
            )
            due_string = f"today {due_time}"

            priority = TodoistTaskPriorityMapping[
                config.config.todoist_default_priority
            ]
            priority_match = re.search(cls.RE_PRIORITY, calendar_event.summary)
            if priority_match:
                priority_str = priority_match.group(1).upper()
                priority = TodoistTaskPriorityMapping[priority_str].value

            todoist_task = TodoistTask(
                id=PendingValue(),
                content=calendar_event.summary,
                description=calendar_event.htmlLink,
                project_id=todoist_project_id,
                due_string=due_string,
                due_lang="en",
                labels=["Calendar"],
                priority=priority,
            )
            tasks.append(todoist_task)

        return cls(*tasks)

    @classmethod
    def from_github_items(
        cls, github_items: Collection, todoist_project_id: int
    ) -> TodoistTaskCollection:
        tasks = []

        for github_item in github_items:
            if github_item.is_pull_request:
                item_type = "My PR" if github_item.created_by_me else "Review PR"
            else:
                item_type = "Issue"
            content = f"[{item_type}] {github_item.repository_name}#{github_item.number}: {github_item.title}"
            todoist_task = TodoistTask(
                id=PendingValue(),
                description=github_item.html_url,
                content=content,
                project_id=todoist_project_id,
                labels=["GitHub"],
                due_string="today",
            )
            tasks.append(todoist_task)

        return cls(*tasks)

    @classmethod
    def compare_calendar(
        cls,
        calendar_events: TodoistTaskCollection,
        todoist_tasks: TodoistTaskCollection,
    ) -> TaskComparisonResult:
        to_add = TodoistTaskCollection()
        to_update = TodoistTaskCollection()
        to_close = TodoistTaskCollection()

        for calendar_event in calendar_events:
            if calendar_event not in todoist_tasks:
                to_add += calendar_event
                logger.info(f"Need to add task {calendar_event.content}.")

            else:
                todoist_task = todoist_tasks.get(description=calendar_event.description)
                todoist_task.content = calendar_event.content
                todoist_task.description = calendar_event.description
                todoist_task.due_string = calendar_event.due_string
                to_update += todoist_task
                logger.info(f"Need to update task {calendar_event.content}.")

        for todoist_task in todoist_tasks:
            if (todoist_task not in to_add) and (todoist_task not in to_update):
                to_close += todoist_task
                logger.info(f"Need to remove task {todoist_task.content}.")

        return TaskComparisonResult(
            to_add=to_add,
            to_update=to_update,
            to_close=to_close,
            to_reopen=TodoistTaskCollection(),
        )

    @classmethod
    def compare_harmonogram(
        cls,
        harmonogram_tasks: TodoistTaskCollection,
        todoist_tasks: TodoistTaskCollection,
    ) -> TaskComparisonResult:
        to_add = TodoistTaskCollection()
        to_update = TodoistTaskCollection()
        to_close = TodoistTaskCollection()

        for harmonogram_task in harmonogram_tasks:
            if harmonogram_task not in todoist_tasks:
                to_add += harmonogram_task
                logger.info(
                    f"Need to add task {harmonogram_task.content} on {harmonogram_task.due_string}."
                )

            else:
                todoist_task = todoist_tasks.get(
                    description=harmonogram_task.description
                )
                todoist_task.content = harmonogram_task.content
                todoist_task.description = harmonogram_task.description
                todoist_task.priority = TodoistTaskPriorityMapping.P1.value
                to_update += todoist_task
                logger.info(
                    f"Need to update task {harmonogram_task.content} on {harmonogram_task.due_string}."
                )

        for todoist_task in todoist_tasks:
            if (todoist_task not in to_add) and (todoist_task not in to_update):
                to_close += todoist_task
                logger.info(
                    f"Need to remove task {todoist_task.content} on {todoist_task.due.date}."
                )

        return TaskComparisonResult(
            to_add=to_add,
            to_update=to_update,
            to_close=to_close,
            to_reopen=TodoistTaskCollection(),
        )

    @classmethod
    def compare_github(
        cls, github_tasks: TodoistTaskCollection, todoist_tasks: TodoistTaskCollection
    ) -> TaskComparisonResult:
        to_add = TodoistTaskCollection()
        to_update = TodoistTaskCollection()
        to_close = TodoistTaskCollection()
        to_reopen = TodoistTaskCollection()

        for github_task in github_tasks:
            if github_task not in todoist_tasks:
                to_add += github_task
                logger.info(f"Need to add task {github_task.content}.")

            else:
                todoist_task = todoist_tasks.get(description=github_task.description)

                # If the task is completed but still in GitHub, it needs to be reopened
                if todoist_task.is_completed:
                    to_reopen += todoist_task
                    logger.info(f"Need to reopen task {github_task.content}.")

                todoist_task.content = github_task.content
                todoist_task.description = github_task.description
                to_update += todoist_task
                logger.info(f"Need to update task {github_task.content}.")

        for todoist_task in todoist_tasks:
            if (todoist_task not in to_add) and (todoist_task not in to_update):
                to_close += todoist_task
                logger.info(f"Need to close task {todoist_task.content}.")

        return TaskComparisonResult(
            to_add=to_add, to_update=to_update, to_close=to_close, to_reopen=to_reopen
        )


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
