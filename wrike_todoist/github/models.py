from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional

from wrike_todoist.models import Item, Collection


@dataclasses.dataclass
class GitHubUser:
    id: int
    login: str
    name: Optional[str]
    html_url: str

    @classmethod
    def from_response(cls, response: Dict) -> GitHubUser:
        return cls(
            id=response["id"],
            login=response["login"],
            name=response.get("name"),
            html_url=response["html_url"],
        )


@dataclasses.dataclass
class GitHubIssue(Item):
    id: int
    number: int
    title: str
    html_url: str
    state: str
    body: Optional[str]
    labels: List[str]
    repository_name: str
    is_pull_request: bool
    draft: bool
    created_by_me: bool = False
    is_dependabot_alert: bool = False

    @property
    def permalink(self) -> str:
        return self.html_url

    @classmethod
    def from_response(cls, response: Dict, current_user: GitHubUser) -> GitHubIssue:
        # Extract repository name from repository_url
        # Format: https://api.github.com/repos/owner/repo
        repository_url = response["repository_url"]
        repository_name = "/".join(repository_url.split("/")[-2:])

        # Draft status is in pull_request.draft for issues endpoint,
        # or directly in draft for search endpoint
        pull_request_info = response.get("pull_request", {})
        draft = response.get("draft", pull_request_info.get("draft", False))

        # Determine if the current user created this item
        author_login = response.get("user", {}).get("login")
        created_by_me = author_login == current_user.login

        return cls(
            id=response["id"],
            number=response["number"],
            title=response["title"],
            html_url=response["html_url"],
            state=response["state"],
            body=response.get("body"),
            labels=[label["name"] for label in response.get("labels", [])],
            repository_name=repository_name,
            is_pull_request="pull_request" in response,
            draft=draft,
            created_by_me=created_by_me,
        )


    @classmethod
    def from_dependabot_alert(cls, alert: Dict, repository_name: str) -> GitHubIssue:
        return cls(
            id=alert["number"],
            number=alert["number"],
            title=alert["security_advisory"]["summary"],
            html_url=alert["html_url"],
            state=alert["state"],
            body=alert["security_advisory"].get("description"),
            labels=[alert["security_vulnerability"]["severity"]],
            repository_name=repository_name,
            is_pull_request=False,
            draft=False,
            is_dependabot_alert=True,
        )


class GitHubIssueCollection(Collection):
    type = GitHubIssue
    primary_key_field_name = "html_url"

    @classmethod
    def from_response(cls, response: List[Dict], current_user: GitHubUser) -> GitHubIssueCollection:
        return cls(*[cls.type.from_response(item, current_user) for item in response])
