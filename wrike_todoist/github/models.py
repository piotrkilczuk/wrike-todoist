from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional

from wrike_todoist.models import Item, Collection


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

    @property
    def permalink(self) -> str:
        return self.html_url

    @classmethod
    def from_response(cls, response: Dict) -> GitHubIssue:
        # Extract repository name from repository_url
        # Format: https://api.github.com/repos/owner/repo
        repository_url = response["repository_url"]
        repository_name = "/".join(repository_url.split("/")[-2:])

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
        )


class GitHubIssueCollection(Collection):
    type = GitHubIssue
    primary_key_field_name = "html_url"

    @classmethod
    def from_response(cls, response: List[Dict]) -> GitHubIssueCollection:
        return cls(*[cls.type.from_response(item) for item in response])
