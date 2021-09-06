from __future__ import annotations

import datetime
import uuid

from django.conf import settings
from django.contrib.auth import login
from django.core.exceptions import PermissionDenied
from django.db import models
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone

from .exceptions import ExpiredLink, InactiveLink, InvalidLink, UsedLink
from .settings import (
    AUTHENTICATION_BACKEND,
    DEFAULT_EXPIRY,
    DEFAULT_REDIRECT,
    SESSION_EXPIRY,
)


def parse_remote_addr(request: HttpRequest) -> str:
    """Extract client IP from request."""
    x_forwarded_for = request.headers.get("X-Forwarded-For", "")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR", "")


def parse_ua_string(request: HttpRequest) -> str:
    """Extract client user-agent from request."""
    return request.headers.get("User-Agent", "")


def link_expires_at(interval: int = DEFAULT_EXPIRY) -> datetime.datetime:
    """Return timestamp used as default link exires_at value."""
    return timezone.now() + datetime.timedelta(seconds=interval)


class MagicLink(models.Model):
    """A unique token used for magic links."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="magic_links"
    )
    token = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, help_text="Unique login token"
    )
    redirect_to = models.CharField(
        help_text="URL to which user will be redirected after logging in. ('/')",
        max_length=255,
        default=DEFAULT_REDIRECT,
    )
    created_at = models.DateTimeField(
        default=timezone.now, help_text="When the link was originally created"
    )
    expires_at = models.DateTimeField(
        help_text="When the link is due to expire (uses DEFAULT_EXPIRY)",
        default=link_expires_at,
    )
    accessed_at = models.DateTimeField(
        help_text="When the link was first used (GET)", blank=True, null=True
    )
    logged_in_at = models.DateTimeField(
        help_text="When the link was used to login", blank=True, null=True
    )
    is_active = models.BooleanField(
        default=True, help_text="Set to False to deactivate the token"
    )

    def __str__(self) -> str:
        return f"Magic link ({self.id}) for {self.user.username}"

    def __repr__(self) -> str:
        return f"<MagicLink id={self.id} user_id={self.user_id} token='{self.token}'>'"

    def get_absolute_url(self) -> str:
        return reverse("magic_link", kwargs={"token": self.token})

    @property
    def has_expired(self) -> bool | None:
        """Return True if the link is past its expiry timestamp."""
        if self.expires_at:
            return self.expires_at < timezone.now()
        return None

    @property
    def has_been_used(self) -> bool:
        """Return True if the link has been used to login already."""
        return self.logged_in_at is not None

    @property
    def is_valid(self) -> bool:
        """Return True if the link can be used."""
        return self.is_active and not self.has_expired and not self.has_been_used

    def validate(self) -> None:
        """
        Check token and request and raise InvalidLink if necessary.

        This method checks the is_valid property, and if found to be False,
        it then runs through the possibilities and raises an appropriate error.

        """
        if not self.is_active:
            raise InactiveLink("Link is inactive")
        if self.has_expired:
            raise ExpiredLink("Link has expired")
        if self.has_been_used:
            raise UsedLink("Link has already been used")
        # theoretically impossible, but belt-and-braces -
        # ensures that is_valid and validate method are kept in sync.
        if not self.is_valid:
            raise InvalidLink("Link is invalid")

    def authorize(self, user: settings.AUTH_USER_MODEL) -> None:
        """
        Check the user may access this link.

        Raises PermissionDenied if the user is authenticated already, and is not
        the user defined in the link.

        """
        if user.is_authenticated and user != self.user:
            raise PermissionDenied("User is already logged in as another user.")

    def login(self, request: HttpRequest) -> None:
        """Call login as the link.user."""
        login(request, self.user, backend=AUTHENTICATION_BACKEND)
        request.session.set_expiry(SESSION_EXPIRY)
        self.logged_in_at = timezone.now()
        self.save()

    def disable(self) -> None:
        """Disable the link regardless of expiry - used as a kill switch."""
        self.is_active = False
        self.save()

    def audit(
        self,
        request: HttpRequest,
        error: InvalidLink | None = None,
        timestamp: datetime.datetime | None = None,
    ) -> MagicLinkUse:
        """
        Create a MagicLinkUse from an HtttpRequest.

        The timestamp parameter is used to force the timestamp of the log to a specific
        value - this is useful for aligning logs with parent link values.

        """
        log = MagicLinkUse.objects.create(
            link=self,
            timestamp=timestamp or timezone.now(),
            http_method=request.method,
            remote_addr=parse_remote_addr(request),
            ua_string=parse_ua_string(request),
            session_key=request.session.session_key or "",
            error=str(error) if error else "",
        )
        if not self.accessed_at:
            self.accessed_at = log.timestamp
            self.save()
        return log


class MagicLinkUse(models.Model):
    """
    Record the use of a token.

    This model is used for auditing purposes - tracking when the token was
    used, recording the IP address and User-Agent of the client, and their
    session id. This allows us to perform diagnostics when tokens fail.

    The canonical pattern of use is to have two records per token - the first
    being a GET to render the login page, and the second being a POST to log
    the user in.

    """

    link = models.ForeignKey(MagicLink, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(
        help_text="When the token page was requested", default=timezone.now
    )
    http_method = models.CharField(
        max_length=10,
    )
    session_key = models.CharField(
        max_length=40, help_text="The request session identifier", blank=True
    )
    remote_addr = models.CharField(
        max_length=100,
        blank=True,
        help_text="The client IP address, extracted from HttpRequest",
    )
    ua_string = models.TextField(
        help_text="The client User-Agent, extracted from HttpRequest headers",
        blank=True,
    )
    error = models.CharField(
        max_length=100,
        help_text="If the link use failed the error will be recorded here",
        blank=True,
    )

    class Meta:
        get_latest_by = ("timestamp",)

    def __str__(self) -> str:
        if self.error:
            return f"Magic link ({self.link_id}) failed at {self.timestamp}"
        return f"Magic link ({self.link_id}) used at {self.timestamp}"

    def __repr__(self) -> str:
        return (
            f"<MagicLinkUse id={self.id} link_id={self.link_id} "
            f"timestamp='{self.timestamp}''>"
        )
