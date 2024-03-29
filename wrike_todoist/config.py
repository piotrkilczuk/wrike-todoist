import os
from pprint import pformat, pprint
from typing import NamedTuple, Type, List

import yaml


class Config(NamedTuple):
    wrike_access_token: str
    wrike_folders: List[str]
    todoist_access_token: str
    todoist_project_name: str
    todoist_label: str
    todoist_default_priority: str


Undefined = object()


def read_from_any(key: str, *dicts, default=Undefined, expected=str):
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
        wrike_access_token=read_from_any("wrike_access_token", os.environ, read_from_yaml),
        wrike_folders=read_from_any("wrike_folders", os.environ, read_from_yaml, expected=list),
        todoist_access_token=read_from_any("todoist_access_token", os.environ, read_from_yaml),
        todoist_project_name=read_from_any("todoist_project_name", os.environ, read_from_yaml),
        todoist_label=read_from_any("todoist_label", os.environ, read_from_yaml),
        todoist_default_priority=read_from_any("todoist_default_priority", os.environ, read_from_yaml, default="P4"),
    )


config = read_config()
