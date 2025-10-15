import os
from typing import NamedTuple, List, TypeVar, Type

import yaml


class Config(NamedTuple):
    gcp_client_id: str
    gcp_client_secret: str
    google_calendar_refresh_token: str
    google_calendar_id: str
    todoist_access_token: str
    todoist_project_name: str
    todoist_label: str
    todoist_default_priority: str
    wrike_access_token: str
    wrike_folders: List[str]
    github_classic_token: str


Undefined = object()


Expected = TypeVar("Expected")


def read_from_any(
    key: str, *dicts, default=Undefined, expected: Type[Expected] = str
) -> Expected:
    value = default
    for dikt in dicts:
        if key in dikt:
            value = dikt[key]
        if key.lower() in dikt:
            value = dikt[key.lower()]
        if key.upper() in dikt:
            value = dikt[key.upper()]
        value = value.strip()
    if expected is list and isinstance(value, str):
        value = [v.strip() for v in value.split(",")]
    if not isinstance(value, expected):
        raise ValueError(f"{key} expected to be a {expected} but is {type(value)}")
    if value is not Undefined:
        return value
    raise KeyError(f"Key {key} not found.")


def read_config() -> Config:
    try:
        file = open(os.path.expanduser("~/wrike-todoist.yml"))
        read_from_yaml = yaml.safe_load(file)
    except IOError:
        read_from_yaml = {}
    return Config(
        gcp_client_id=read_from_any("gcp_client_id", os.environ, read_from_yaml),
        gcp_client_secret=read_from_any(
            "gcp_client_secret", os.environ, read_from_yaml
        ),
        google_calendar_id=read_from_any(
            "google_calendar_id", os.environ, read_from_yaml
        ),
        google_calendar_refresh_token=read_from_any(
            "google_calendar_refresh_token", os.environ, read_from_yaml
        ),
        todoist_access_token=read_from_any(
            "todoist_access_token", os.environ, read_from_yaml
        ),
        todoist_project_name=read_from_any(
            "todoist_project_name", os.environ, read_from_yaml
        ),
        todoist_label=read_from_any("todoist_label", os.environ, read_from_yaml),
        todoist_default_priority=read_from_any(
            "todoist_default_priority", os.environ, read_from_yaml, default="P4"
        ),
        wrike_access_token=read_from_any(
            "wrike_access_token", os.environ, read_from_yaml
        ),
        wrike_folders=read_from_any(
            "wrike_folders", os.environ, read_from_yaml, expected=list
        ),
        github_classic_token=read_from_any(
            "github_classic_token", os.environ, read_from_yaml
        ),
    )


config = read_config()
