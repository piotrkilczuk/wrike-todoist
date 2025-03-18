from __future__ import annotations

import dataclasses
from typing import Optional, Dict


@dataclasses.dataclass
class Creator:
    displayName: str
    email: str
    self: bool


@dataclasses.dataclass
class TimeInfo:
    dateTime: str
    timeZone: str


@dataclasses.dataclass
class Reminders:
    useDefault: bool


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
            creator=Creator(**response["creator"]),
            end=TimeInfo(**response["end"]),
            etag=response["etag"],
            eventType=response["eventType"],
            htmlLink=response["htmlLink"],
            iCalUID=response["iCalUID"],
            id=response["id"],
            kind=response["kind"],
            organizer=Creator(**response["organizer"]),
            originalStartTime=TimeInfo(**response.get("originalStartTime")),
            recurringEventId=response.get("recurringEventId"),
            reminders=Reminders(**response["reminders"]),
            sequence=response["sequence"],
            start=TimeInfo(**response["start"]),
            status=response["status"],
            summary=response["summary"],
            updated=response["updated"],
        )
