from os import getenv
from typing import Any, Callable

from django.conf import settings


def _env_or_setting(key: str, default: Any, cast_func: Callable = lambda x: x) -> Any:
    return cast_func(getenv(key) or getattr(settings, key, default))


# default expiry of a link, in seconds
DEFAULT_EXPIRY = _env_or_setting("MAGIC_LINK_DEFAULT_EXPIRY", 300, lambda x: int(x))
