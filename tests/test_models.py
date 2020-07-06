from unittest import mock

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.http.request import HttpRequest
from django.utils import timezone

from magic_link.exceptions import (
    ExpiredToken,
    InactiveToken,
    InvalidTokenUse,
    UserMismatch,
)
from magic_link.models import (
    MagicLink,
    MagicLinkUse,
    parse_remote_addr,
    parse_ua_string,
)


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
    def test_is_valid(self):
        link = MagicLink()
        assert link.is_active
        assert not link.has_expired
        assert link.is_valid

    def test_is_inactive(self):
        link = MagicLink(user=User(), is_active=False)
        assert not link.is_active
        assert not link.has_expired
        assert not link.is_valid

    def test_has_expired(self):
        link = MagicLink(user=User(), expires_at=None)
        assert link.has_expired is None
        link = MagicLink(user=User(), expires_at=timezone.now())
        assert link.is_active
        assert link.has_expired
        assert not link.is_valid

    def test_validate__inactive(self):
        link = MagicLink(is_active=False)
        request = mock.Mock(spec=HttpRequest)
        with pytest.raises(InactiveToken):
            link.validate(request)

    def test_validate__expired(self):
        link = MagicLink(expires_at=timezone.now())
        request = mock.Mock(spec=HttpRequest)
        with pytest.raises(ExpiredToken):
            link.validate(request)

    def test_validate__wrong_user(self):
        link = MagicLink(user=User(id=1))
        request = mock.Mock(spec=HttpRequest, user=User(id=2))
        with pytest.raises(UserMismatch):
            link.validate(request)

    def test_validate__anonymous(self):
        link = MagicLink()
        request = mock.Mock(spec=HttpRequest, user=AnonymousUser())
        link.validate(request)

    def test_login(self):
        # Regression test only - not functionally useful.
        link = MagicLink(user=User())
        request = mock.Mock(spec=HttpRequest, user=link.user)
        with mock.patch("magic_link.models.login") as mock_login:
            link.login(request)
            assert mock_login.called_once_with(request, link.user)

    @pytest.mark.django_db
    def test_audit(self):
        user = User.objects.create(username="Job Bluth")
        link = MagicLink.objects.create(user=user)
        headers = {"X-Forwarded-For": "127.0.0.1", "User-Agent": "Chrome"}
        session = mock.Mock(session_key="")
        request = mock.Mock(
            spec=HttpRequest, method="GET", user=user, headers=headers, session=session
        )
        log = link.audit(request)
        assert MagicLinkUse.objects.count() == 1
        assert log.link == link
        assert log.error == ""

    @pytest.mark.django_db
    def test_log_error(self):
        user = User.objects.create(username="Job Bluth")
        link = MagicLink.objects.create(user=user)
        headers = {"X-Forwarded-For": "127.0.0.1", "User-Agent": "Chrome"}
        session = mock.Mock(session_key="")
        request = mock.Mock(
            spec=HttpRequest, method="GET", user=user, headers=headers, session=session
        )
        log = link.audit(request, InvalidTokenUse("Test error"))
        assert log.link == link
        assert log.error == "Test error"

    @pytest.mark.django_db
    def test_disable(self):
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user)
        expiry = link.expires_at
        assert link.is_valid
        link.disable()
        assert not link.is_valid
        assert link.expires_at < expiry
