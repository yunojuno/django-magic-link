from unittest import mock

import pytest
from django.contrib.auth.models import User
from django.test import Client

from magic_link.models import MagicLink


# we are mocking out the audit method in all these tests as it's orthogonal
# to the core functions of the views. We just need to know that it has been called.
@pytest.mark.django_db
@mock.patch.object(MagicLink, "audit")
class TestMagicLinkViewGet:
    def test_get_missing_link_404(self, mock_audit):
        client = Client()
        response = client.get("/magic-link")
        assert response.status_code == 404
        assert mock_audit.call_count == 0

    def test_get_invalid_link_403(self, mock_audit):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user, is_active=False)
        # assert not link.is_valid
        response = client.get(link.get_absolute_url())
        assert response.status_code == 403
        assert mock_audit.call_count == 1

    def test_get_invalid_request_403(self, mock_audit):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        user2 = User.objects.create(username="Job")
        link = MagicLink.objects.create(user=user)
        # assert link.is_valid
        client.force_login(user2)
        response = client.get(link.get_absolute_url())
        assert response.status_code == 403
        assert mock_audit.call_count == 1

    def test_get_valid_request_200(self, mock_audit):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user)
        response = client.get(link.get_absolute_url())
        assert response.status_code == 200
        assert mock_audit.call_count == 1


@pytest.mark.django_db
@mock.patch.object(MagicLink, "audit")
class TestMagicLinkViewPost:
    def test_post_missing_link_404(self, mock_audit):
        client = Client()
        response = client.post("/magic-link")
        assert response.status_code == 404
        assert mock_audit.call_count == 0

    def test_post_invalid_link_403(self, mock_audit):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user, is_active=False)
        response = client.post(link.get_absolute_url())
        assert response.status_code == 403
        assert mock_audit.call_count == 1

    def test_post_invalid_request_403(self, mock_audit):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        user2 = User.objects.create(username="Job")
        link = MagicLink.objects.create(user=user)
        client.force_login(user2)
        response = client.post(link.get_absolute_url())
        link.refresh_from_db()
        assert response.status_code == 403
        assert mock_audit.call_count == 1

    def test_post_valid_request_302(self, mock_audit):
        """Check that valid link POST redirects and disables the link."""
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user, redirect_to="/foo/bar")
        response = client.post(link.get_absolute_url())
        link.refresh_from_db()
        assert response.status_code == 302
        assert response.url == link.redirect_to
        assert not link.is_active
        assert link.logged_in_at is not None
        assert mock_audit.call_count == 1
