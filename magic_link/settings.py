from os import getenv
from typing import Any, Callable

from django.conf import settings


def _env_or_setting(key: str, default: Any, cast_func: Callable = lambda x: x) -> Any:
    return cast_func(getenv(key) or getattr(settings, key, default))


# default link expiry, in seconds; defaults to 60s / 1 mins
DEFAULT_EXPIRY = _env_or_setting("MAGIC_LINK_DEFAULT_EXPIRY", 60, lambda x: int(x))


# default redirect URL; defaults to 'root'
DEFAULT_REDIRECT = _env_or_setting("MAGIC_LINK_DEFAULT_REDIRECT", "/")


# the authentication backend used when calling the login method
AUTHENTICATION_BACKEND = _env_or_setting(
    "MAGIC_LINK_AUTHENTICATION_BACKEND", "django.contrib.auth.backends.ModelBackend"
)
