import json
import logging
from typing import Union

import requests

logger = logging.getLogger(__name__)


JSONValue = Union[dict, list, str, int, float, bool, None]


def response_to_json_value(
    response: requests.Response, encoding: str = "utf-8"
) -> JSONValue:
    try:
        response.raise_for_status()
    except requests.HTTPError:
        logger.error(f"Response is {response.status_code}: {response.text}")
        raise

    try:
        # requests does not handle the old BOM correctly, so better to decode it manually
        response_str = response.content.decode(encoding)
        return json.loads(response_str)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode response {response.text}")
        raise
