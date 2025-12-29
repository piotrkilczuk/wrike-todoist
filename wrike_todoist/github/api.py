import logging

import requests

from wrike_todoist import config
from wrike_todoist.api_utils import response_to_json_value
from wrike_todoist.github import models

logger = logging.getLogger(__name__)


def github_get_authenticated_user() -> models.GitHubUser:
    """Fetch the authenticated user."""
    response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {config.config.github_classic_token}"},
    )
    return models.GitHubUser.from_response(response_to_json_value(response))


def github_get_assigned_issues(current_user: models.GitHubUser) -> models.GitHubIssueCollection:
    """Get all open issues and PRs assigned to the authenticated user."""
    github_issues_response = requests.get(
        "https://api.github.com/issues",
        params={
            "filter": "assigned",
            "state": "open",
            "per_page": 100,
        },
        headers={"Authorization": f"Bearer {config.config.github_classic_token}"},
    )
    github_issue_collection = models.GitHubIssueCollection.from_response(
        response_to_json_value(github_issues_response), current_user
    )
    logger.info(f"Retrieved {len(github_issue_collection)} assigned GitHub issues/PRs.")
    return github_issue_collection


def github_get_review_requests(current_user: models.GitHubUser) -> models.GitHubIssueCollection:
    """Get all open non-draft PRs where the authenticated user has been requested for review."""
    github_review_requests_response = requests.get(
        "https://api.github.com/search/issues",
        params={
            "q": "is:open is:pr draft:false review-requested:@me",
            "per_page": 100,
        },
        headers={"Authorization": f"Bearer {config.config.github_classic_token}"},
    )
    response_data = response_to_json_value(github_review_requests_response)
    github_review_request_collection = models.GitHubIssueCollection.from_response(
        response_data.get("items", []), current_user
    )
    logger.info(f"Retrieved {len(github_review_request_collection)} GitHub review requests.")
    return github_review_request_collection


def github_get_created_prs(current_user: models.GitHubUser) -> models.GitHubIssueCollection:
    """Get all open non-draft PRs created by the authenticated user."""
    github_created_prs_response = requests.get(
        "https://api.github.com/search/issues",
        params={
            "q": "is:open is:pr draft:false author:@me",
            "per_page": 100,
        },
        headers={"Authorization": f"Bearer {config.config.github_classic_token}"},
    )
    response_data = response_to_json_value(github_created_prs_response)
    github_created_pr_collection = models.GitHubIssueCollection.from_response(
        response_data.get("items", []), current_user
    )
    logger.info(f"Retrieved {len(github_created_pr_collection)} GitHub PRs created by user.")
    return github_created_pr_collection


def github_get_all_items(current_user: models.GitHubUser) -> models.GitHubIssueCollection:
    """Get all GitHub items: assigned issues/PRs, review requests, and created PRs."""
    assigned = github_get_assigned_issues(current_user)
    review_requests = github_get_review_requests(current_user)
    created_prs = github_get_created_prs(current_user)

    # Combine and deduplicate using the distinct() method from Collection
    combined = assigned + review_requests + created_prs
    return combined.distinct()
