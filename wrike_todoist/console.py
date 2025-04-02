import logging

import click
import pendulum

from wrike_todoist import config
from wrike_todoist.google_calendar import api as google_calendar_api
from wrike_todoist.wrike import api as wrike_api, models as wrike_models
from wrike_todoist.todoist import api as todoist_api, models as todoist_models
from wrike_todoist.harmonogram import api as harmonogram_api

logger = logging.getLogger(__name__)


def google_calendar_todoist_main():
    calendar_events = google_calendar_api.pull_todays_events()
    calendar_events = calendar_events.filter(
        lambda event: event.eventType == "default" and event.kind == "calendar#event"
    )

    todoist_project = todoist_api.todoist_get_project_by_name(
        "Calendar"  # @TODO: Parametrize
    )
    actual_todoist_tasks = todoist_api.todoist_get_tasks(
        todoist_project, only_due_today=True
    )
    actual_todoist_tasks_only_due_today = actual_todoist_tasks.filter(
        lambda task: task.due and task.due.date == pendulum.today()
    )
    actual_todoist_tasks_completed_today = todoist_api.todoist_get_completed_tasks(
        todoist_project, since=pendulum.today()
    )
    actual_todoist_tasks = (
        actual_todoist_tasks_only_due_today + actual_todoist_tasks_completed_today
    ).distinct()
    expected_todoist_tasks = todoist_models.TodoistTaskCollection.from_calendar_events(
        calendar_events, todoist_project.id
    )

    comparison_result = todoist_models.TodoistTaskCollection.compare_calendar(
        expected_todoist_tasks, actual_todoist_tasks
    )

    todoist_api.todoist_create_tasks(comparison_result.to_add)
    todoist_api.todoist_update_tasks(comparison_result.to_update)
    todoist_api.todoist_remove_tasks(comparison_result.to_close)


def harmonogram_main():
    collection_days = harmonogram_api.pull_future_collection_days()

    todoist_project = todoist_api.todoist_get_project_by_name(
        "Śmieci"  # @TODO: Parametrize
    )
    actual_todoist_tasks_active = todoist_api.todoist_get_tasks(todoist_project)
    actual_todoist_tasks_completed_last_seven_days = (
        todoist_api.todoist_get_completed_tasks(
            todoist_project, since=pendulum.today().subtract(days=7)
        )
    )
    actual_todoist_tasks = (
        actual_todoist_tasks_active + actual_todoist_tasks_completed_last_seven_days
    ).distinct()

    expected_todoist_tasks = todoist_models.TodoistTaskCollection.from_harmonogram(
        collection_days, todoist_project.id
    )

    comparison_result = todoist_models.TodoistTaskCollection.compare_harmonogram(
        expected_todoist_tasks, actual_todoist_tasks
    )

    todoist_api.todoist_remove_tasks(comparison_result.to_close)
    todoist_api.todoist_create_tasks(comparison_result.to_add)
    todoist_api.todoist_update_tasks(comparison_result.to_update)


def wrike_todoist_main():
    wrike_user = wrike_api.wrike_get_current_user()
    wrike_folders = wrike_api.wrike_get_folders()
    wrike_folders = [
        wrike_folders.get(permalink=f"https://www.wrike.com/open.htm?id={folder_id}")
        for folder_id in config.config.wrike_folders
    ]
    wrike_tasks = wrike_models.WrikeTaskCollection()
    for wrike_folder in wrike_folders:
        wrike_tasks += wrike_api.wrike_get_tasks(wrike_user, wrike_folder)

    todoist_project = todoist_api.todoist_get_project_by_name(
        config.config.todoist_project_name
    )
    actual_todoist_tasks = todoist_api.todoist_get_tasks(todoist_project)

    expected_todoist_tasks = todoist_models.TodoistTaskCollection.from_wrike_tasks(
        wrike_tasks, todoist_project.id
    )

    comparison_result = todoist_models.TodoistTaskCollection.compare_wrike(
        expected_todoist_tasks, actual_todoist_tasks
    )

    todoist_api.todoist_create_tasks(comparison_result.to_add)
    todoist_api.todoist_update_tasks(comparison_result.to_update)
    todoist_api.todoist_close_tasks(comparison_result.to_close)


@click.command()
@click.option(
    "--harmonogram/--no-harmonogram", default=True, help="Run harmonogram_main"
)
@click.option(
    "--google-calendar/--no-google-calendar",
    default=True,
    help="Run google_calendar_todoist_main",
)
@click.option(
    "--wrike-todoist/--no-wrike-todoist", default=True, help="Run wrike_todoist_main"
)
def main(harmonogram, google_calendar, wrike_todoist):
    logging.basicConfig(level=logging.INFO)
    if harmonogram:
        harmonogram_main()
    if google_calendar:
        google_calendar_todoist_main()
    if wrike_todoist:
        wrike_todoist_main()
