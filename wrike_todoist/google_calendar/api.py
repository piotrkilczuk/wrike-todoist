import datetime
from pprint import pprint
import time
from typing import Callable, Iterator

from google.oauth2.credentials import Credentials
from googleapiclient import discovery
import pendulum

from wrike_todoist import config
from wrike_todoist.google_calendar import models


def requires_service(func) -> Callable:
    credentials = Credentials.from_authorized_user_info(
        {
            "refresh_token": config.config.google_calendar_refresh_token,
            "client_id": config.config.gcp_client_id,
            "client_secret": config.config.gcp_client_secret,
        },
        scopes=["https://www.googleapis.com/auth/calendar.readonly"],
    )
    service = discovery.build("calendar", "v3", credentials=credentials).events()

    def wrapper(*args, **kwargs):
        return func(service, *args, **kwargs)

    return wrapper


def page_iterator(
    service: discovery.Resource,
    calendar_id: str,
    time_min: datetime.datetime,
    time_max: datetime.datetime,
) -> Iterator[dict]:
    request = service.list(
        calendarId=calendar_id,
        timeMin=time_min.isoformat(),
        timeMax=time_max.isoformat(),
        singleEvents=True,
        orderBy="startTime",
    )
    while request:
        response = request.execute()
        items = response.get("items", [])
        for item in items:
            yield item
        request = service.events().list_next(request, response)


@requires_service
def pull_todays_events(service: discovery.Resource):
    start_of_day = pendulum.today()
    end_of_day = pendulum.tomorrow()

    print(start_of_day, end_of_day)

    events = page_iterator(
        service, config.config.google_calendar_id, start_of_day, end_of_day
    )
    for event_response in events:
        print()
        pprint(event_response)
        calendar_event = models.CalendarEvent.from_response(event_response)

        print()
        print(calendar_event)
        time.sleep(1)

    raise NotImplementedError(...)
