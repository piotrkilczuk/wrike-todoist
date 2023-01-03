#!/usr/bin/env python
from os import environ
from pprint import pformat

from requests import get

user_response = get(
    "https://www.wrike.com/api/v4/contacts?me=true",
    params={"access_token": environ["WRIKE_ACCESS_TOKEN"]},
)
user_id = user_response.json()["data"][0]["id"]

response = get(
    "https://www.wrike.com/api/v4/tasks",
    params={
        "access_token": environ["WRIKE_ACCESS_TOKEN"],
        "status": "Active",
        "responsibles": f"[{user_id}]",
    },
)

raise NotImplementedError(pformat(response.json()))
