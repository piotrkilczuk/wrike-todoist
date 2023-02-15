import logging
from pprint import pformat

from wrike_todoist import api, models, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    wrike_user = api.wrike_get_current_user()
    wrike_folders = api.wrike_get_folders()
    wrike_folder = wrike_folders.get(title=config.config.wrike_folder)

    wrike_tasks = api.wrike_get_tasks(wrike_user, wrike_folder)

    todoist_project = api.todoist_get_project_by_name(config.config.todoist_project_name)
    actual_todoist_tasks = api.todoist_get_tasks(todoist_project, config.config.todoist_label)

    expected_todoist_tasks = models.TodoistTaskCollection.from_wrike_tasks(wrike_tasks, todoist_project.id)

    comparison_result = models.TodoistTaskCollection.compare(expected_todoist_tasks, actual_todoist_tasks)

    api.todoist_create_tasks(comparison_result.to_add)
    api.todoist_update_tasks(comparison_result.to_update)
    api.todoist_close_tasks(comparison_result.to_close)
