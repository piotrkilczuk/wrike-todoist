from __future__ import annotations

import dataclasses
from typing import Optional, Dict, Union

from wrike_todoist.models import Collection


@dataclasses.dataclass
class Creator:
    displayName: str
    email: str
    self: bool

    @classmethod
    def from_response(cls, response: Union[Dict, None]):
        if response is None:
            raise NotImplementedError(response)
        return cls(
            displayName=response["displayName"],
            email=response["email"],
            self=response["self"],
        )


@dataclasses.dataclass
class TimeInfo:
    dateTime: str
    timeZone: str

    @classmethod
    def from_response(cls, response: Union[Dict, None]):
        if response is None:
            return None
        return cls(
            dateTime=response["dateTime"],
            timeZone=response["timeZone"],
        )


@dataclasses.dataclass
class Reminders:
    useDefault: bool

    @classmethod
    def from_response(cls, response: Union[Dict, None]):
        if response is None:
            raise NotImplementedError(response)
        return cls(useDefault=response["useDefault"])


@dataclasses.dataclass
class CalendarEvent:
    created: str  # @TODO: Should be datetime
    creator: Creator
    end: TimeInfo
    etag: str
    eventType: str
    htmlLink: str
    iCalUID: str
    id: str
    kind: str
    organizer: Creator
    originalStartTime: Optional[TimeInfo]
    recurringEventId: Optional[str]
    reminders: Reminders
    sequence: int
    start: TimeInfo
    status: str
    summary: str
    updated: str  # @TODO: Should be datetime

    @classmethod
    def from_response(cls, response: Dict) -> CalendarEvent:
        return cls(
            created=response["created"],
            creator=Creator.from_response(response["creator"]),
            end=TimeInfo.from_response(response["end"]),
            etag=response["etag"],
            eventType=response["eventType"],
            htmlLink=response["htmlLink"],
            iCalUID=response["iCalUID"],
            id=response["id"],
            kind=response["kind"],
            organizer=Creator(**response["organizer"]),
            originalStartTime=TimeInfo.from_response(response.get("originalStartTime")),
            recurringEventId=response.get("recurringEventId"),
            reminders=Reminders.from_response(response["reminders"]),
            sequence=response["sequence"],
            start=TimeInfo.from_response(response["start"]),
            status=response["status"],
            summary=response["summary"],
            updated=response["updated"],
        )


class CalendarEventCollection(Collection):
    type = CalendarEvent

    @classmethod
    def from_response(cls, response: Dict) -> CalendarEventCollection:
        return cls(*[cls.type.from_response(item) for item in response["items"]])
