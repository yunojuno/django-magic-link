import datetime
from unittest import mock

import freezegun
import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.sessions.backends.base import SessionBase
from django.core.exceptions import PermissionDenied
from django.http.request import HttpRequest
from django.utils import timezone

from magic_link.exceptions import ExpiredToken, InactiveToken, InvalidToken, UsedToken
from magic_link.models import (
    MagicLink,
    MagicLinkUse,
    parse_remote_addr,
    parse_ua_string,
)

# standard "now" time used for freezegun
FREEZE_TIME_NOW = timezone.now()


class TestMAgicLinkFunctions:
    @pytest.mark.parametrize(
        "xff,remote,output",
        (
            ("", "", ""),
            ("127.0.0.1", "", "127.0.0.1"),
            ("127.0.0.1,192.168.0.1", "", "127.0.0.1"),
            ("127.0.0.1", "192.168.0.1", "127.0.0.1"),
            ("", "192.168.0.1", "192.168.0.1"),
        ),
    )
    def test_remote_addr(self, xff, remote, output):
        headers = {"X-Forwarded-For": xff} if xff else {}
        meta = {"REMOTE_ADDR": remote} if remote else {}
        request = mock.Mock(spec=HttpRequest, headers=headers, META=meta)
        assert parse_remote_addr(request) == output

    @pytest.mark.parametrize("ua_string", ("", "Chrome"))
    def test_ua_string(self, ua_string):
        headers = {"User-Agent": ua_string} if ua_string else {}
        request = mock.Mock(spec=HttpRequest, headers=headers)
        assert parse_ua_string(request) == ua_string


class TestMagicLink:
    def test_has_been_used(self):
        link = MagicLink(user=User(), logged_in_at=None)
        assert not link.has_been_used
        link.logged_in_at = timezone.now()
        assert link.has_been_used

    def test_has_expired(self):
        link = MagicLink(user=User(), expires_at=None)
        assert link.has_expired is None
        link = MagicLink(user=User(), expires_at=timezone.now())
        assert link.is_active
        assert link.has_expired

    def test_validate__inactive(self):
        link = MagicLink(is_active=False)
        with pytest.raises(InactiveToken):
            link.validate()

    def test_validate__expired(self):
        link = MagicLink(expires_at=timezone.now())
        with pytest.raises(ExpiredToken):
            link.validate()

    def test_validate__used(self):
        link = MagicLink(logged_in_at=timezone.now())
        with pytest.raises(UsedToken):
            link.validate()

    def test_authorize__anonymous(self):
        """Check that an anonymous user can access the link."""
        user1 = User(id=1)
        link = MagicLink(user=user1)
        link.authorize(AnonymousUser())

    def test_authorize__link_user(self):
        """Check that the link user themselves can access it."""
        user1 = User(id=1)
        link = MagicLink(user=user1)
        link.authorize(user1)

    def test_authorize__user_denied(self):
        """Check that an authenticated user cannot use the link."""
        user1 = User(id=1)
        link = MagicLink(user=user1)
        with pytest.raises(PermissionDenied):
            link.authorize(User(id=2))

    @freezegun.freeze_time(FREEZE_TIME_NOW)
    @pytest.mark.django_db
    def test_login(self):
        # Regression test only - not functionally useful.
        user = User.objects.create_user(username="Fernando")
        link = MagicLink(user=user)
        assert not link.logged_in_at
        request = mock.Mock(spec=HttpRequest, user=link.user)
        with mock.patch("magic_link.models.login") as mock_login:
            link.login(request)
            assert mock_login.called_once_with(request, link.user)
            assert link.logged_in_at == FREEZE_TIME_NOW

    @pytest.mark.django_db
    def test_audit(self):
        user = User.objects.create(username="Job Bluth")
        link = MagicLink.objects.create(user=user)
        request = mock.Mock(
            spec=HttpRequest,
            method="GET",
            user=user,
            headers={"X-Forwarded-For": "127.0.0.1", "User-Agent": "Chrome"},
            session=mock.Mock(spec=SessionBase, session_key=""),
        )
        log = link.audit(request)
        assert MagicLinkUse.objects.count() == 1
        assert log.link == link
        assert log.error == ""
        assert link.accessed_at == log.timestamp

    @pytest.mark.django_db
    def test_audit__accessed_at(self):
        """Check that accessed_at is not overwritten by a second visit."""
        user = User.objects.create(username="Job Bluth")
        link = MagicLink.objects.create(user=user, accessed_at=FREEZE_TIME_NOW)
        request = mock.Mock(
            spec=HttpRequest,
            method="GET",
            user=user,
            headers={"X-Forwarded-For": "127.0.0.1", "User-Agent": "Chrome"},
            session=mock.Mock(spec=SessionBase, session_key=""),
        )
        assert timezone.now() != FREEZE_TIME_NOW
        log = link.audit(request)
        assert link.accessed_at == FREEZE_TIME_NOW

    @pytest.mark.django_db
    def test_audit__timestamp(self):
        user = User.objects.create(username="Job Bluth")
        link = MagicLink.objects.create(user=user)
        request = mock.Mock(
            spec=HttpRequest,
            method="GET",
            user=user,
            headers={"X-Forwarded-For": "127.0.0.1", "User-Agent": "Chrome"},
            session=mock.Mock(spec=SessionBase, session_key=""),
        )
        # create a timestamp that differs from 'now'
        with freezegun.freeze_time(FREEZE_TIME_NOW):
            timestamp = FREEZE_TIME_NOW - datetime.timedelta(seconds=10)
            log = link.audit(request, timestamp=timestamp)
            assert log.timestamp == timestamp
            assert log.timestamp != FREEZE_TIME_NOW

    @pytest.mark.django_db
    def test_audit__error(self):
        user = User.objects.create(username="Job Bluth")
        link = MagicLink.objects.create(user=user)
        headers = {"X-Forwarded-For": "127.0.0.1", "User-Agent": "Chrome"}
        session = mock.Mock(session_key="")
        request = mock.Mock(
            spec=HttpRequest, method="GET", user=user, headers=headers, session=session
        )
        log = link.audit(request, InvalidToken("Test error"))
        assert log.link == link
        assert log.error == "Test error"

    @pytest.mark.django_db
    def test_disable(self):
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user)
        assert link.is_active
        link.disable()
        assert not link.is_active
