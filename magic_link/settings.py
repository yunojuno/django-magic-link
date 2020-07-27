from django.conf import settings

_settings = getattr(settings, "MAGIC_LINK", {})

# default link expiry, in seconds; defaults to 60s / 1 mins
DEFAULT_EXPIRY: int = _settings.get("DEFAULT_EXPIRY", 300)

# default redirect URL; defaults to 'root'
DEFAULT_REDIRECT: str = _settings.get("DEFAULT_REDIRECT", "/")

# the authentication backend used when calling the login method
AUTHENTICATION_BACKEND: str = _settings.get(
    "AUTHENTICATION_BACKEND", "django.contrib.auth.backends.ModelBackend"
)

# override session expiry for magic links only (seconds)
SESSION_EXPIRY: int = _settings.get("SESSION_EXPIRY", settings.SESSION_COOKIE_AGE)
