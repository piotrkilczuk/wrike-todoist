import logging
from typing import Union

import requests

logger = logging.getLogger(__name__)


JSONValue = Union[dict, list, str, int, float, bool, None]


def response_to_json_value(response: requests.Response) -> JSONValue:
    try:
        response.raise_for_status()
    except requests.HTTPError:
        logger.error(f"Response is {response.status_code}: {response.text}")
        raise

    try:
        return response.json()
    except requests.JSONDecodeError:
        logger.error(f"Failed to decode response {response.text}")
        raise
