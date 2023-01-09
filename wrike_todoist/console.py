import logging

from wrike_todoist import api, const, models


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    wrike_user = api.wrike_get_current_user()
    wrike_tasks = api.wrike_get_tasks(wrike_user)

    todoist_project = api.todoist_get_project_by_name(const.TODOIST_PROJECT_NAME)
    actual_todoist_tasks = api.todoist_get_tasks(todoist_project, const.TODOIST_LABEL)

    expected_todoist_tasks = models.TodoistTaskCollection.from_wrike_tasks(wrike_tasks, todoist_project.id)

    comparison_result = models.TodoistTaskCollection.compare(expected_todoist_tasks, actual_todoist_tasks)

    created_todoist_tasks = api.todoist_create_tasks(comparison_result.to_add)

    raise NotImplementedError(...)
