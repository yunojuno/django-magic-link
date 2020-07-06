import pytest
from django.contrib.auth.models import User
from django.test import Client

from magic_link.models import MagicLink


@pytest.mark.django_db
class TestMagicLinkViewGet:
    def test_get_missing_link_404(self):
        client = Client()
        response = client.get("/magic-link")
        assert response.status_code == 404

    def test_get_invalid_link_403(self):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user, is_active=False)
        assert not link.is_valid
        response = client.get(link.get_absolute_url())
        assert response.status_code == 403

    def test_get_invalid_request(self):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        user2 = User.objects.create(username="Job")
        link = MagicLink.objects.create(user=user)
        assert link.is_valid
        client.force_login(user2)
        response = client.get(link.get_absolute_url())
        assert response.status_code == 403

    def test_get_valid_request(self):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user)
        response = client.get(link.get_absolute_url())
        assert response.status_code == 200


@pytest.mark.django_db
class TestMagicLinkViewPost:
    def test_post_missing_link(self):
        client = Client()
        response = client.post("/magic-link")
        assert response.status_code == 404

    def test_post_invalid_link(self):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user, is_active=False)
        assert not link.is_valid
        response = client.post(link.get_absolute_url())
        assert response.status_code == 403

    def test_post_invalid_request(self):
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        user2 = User.objects.create(username="Job")
        link = MagicLink.objects.create(user=user)
        assert link.is_valid
        client.force_login(user2)
        response = client.post(link.get_absolute_url())
        link.refresh_from_db()
        assert link.is_valid
        assert response.status_code == 403

    def test_post_valid_request(self):
        """Check that valid link POST redirects and disables the link."""
        client = Client()
        user = User.objects.create(username="Bob Loblaw")
        link = MagicLink.objects.create(user=user, redirect_to="/foo/bar")
        assert link.is_valid
        response = client.post(link.get_absolute_url())
        link.refresh_from_db()
        assert response.status_code == 302
        assert response.url == link.redirect_to
