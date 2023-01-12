import os
from typing import NamedTuple, List

import yaml


class Config(NamedTuple):
    wrike_access_token: str
    wrike_folder: str
    todoist_access_token: str
    todoist_project_name: str
    todoist_label: str


def read_from_any(key: str, *dicts):
    for dict in dicts:
        if key in dict:
            return dict[key]
        if key.lower() in dict:
            return dict[key.lower()]
        if key.upper() in dict:
            return dict[key.upper()]
    raise KeyError(f"Key {key} not found.")


def read_config() -> Config:
    try:
        file = open(os.path.expanduser("~/wrike-todoist.yml"))
        read_from_yaml = yaml.safe_load(file)
    except IOError:
        read_from_yaml = {}

    return Config(
        wrike_access_token=read_from_any("wrike_access_token", os.environ, read_from_yaml),
        wrike_folder=read_from_any("wrike_folder", os.environ, read_from_yaml),
        todoist_access_token=read_from_any("todoist_access_token", os.environ, read_from_yaml),
        todoist_project_name=read_from_any("todoist_project_name", os.environ, read_from_yaml),
        todoist_label=read_from_any("todoist_label", os.environ, read_from_yaml),
    )


config = read_config()
