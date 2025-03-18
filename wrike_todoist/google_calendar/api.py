import datetime
from pprint import pprint
import time
from typing import Callable, Iterator

from google.oauth2.service_account import Credentials
from googleapiclient import discovery
import pendulum

from wrike_todoist import config
from wrike_todoist.google_calendar import models


def requires_service(func) -> Callable:
    credentials = Credentials.from_service_account_info(
        {
            "type": "service_account",
            "project_id": config.config.gcp_project_id,
            "private_key_id": config.config.gcp_private_key_id,
            "private_key": config.config.gcp_private_key,
            "client_email": config.config.gcp_client_email,
            "client_id": config.config.gcp_client_id,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/wrike-todoist-google-calendar%40utopian-plane-453519-d4.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com",
        }
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
