import logging

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import InvalidLink, MagicLink

logger = logging.getLogger(__name__)


class MagicLinkView(View):
    def get(self, request: HttpRequest, token: str) -> HttpResponse:
        """
        Render login page.

        If the link is invalid, or the user is already logged in, then this
        view will raise a PermissionDenied, which will render the 403 template.

        """
        link = get_object_or_404(MagicLink, token=token)
        try:
            link.validate()
            link.authorize(request.user)
        except (PermissionDenied, InvalidLink) as ex:
            link.audit(request, error=ex)
            return render(
                request,
                template_name="magic_link/error.html",
                context={"link": link, "error": ex},
                status=403,
            )
        else:
            link.audit(request)
            return render(
                request,
                template_name="magic_link/logmein.html",
                context={"link": link},
                status=200,
            )

    @transaction.atomic
    def post(self, request: HttpRequest, token: str) -> HttpResponse:
        """
        Handle the login POST request.

        If the link is invalid, or the user is already logged in, then this
        view will raise a PermissionDenied, which will render the 403 template.

        If the use is valid then this will call the login() method, and redirect
        the user (now authenticated).

        The token will be rendered inactive at this point.

        """
        link = get_object_or_404(MagicLink, token=token)
        try:
            link.validate()
            link.authorize(request.user)
        except (PermissionDenied, InvalidLink) as ex:
            link.audit(request, error=ex)
            return render(
                request,
                template_name="magic_link/error.html",
                context={"link": link, "error": ex},
                status=403,
            )
        else:
            link.login(request)
            link.disable()
            link.audit(request, timestamp=link.logged_in_at)
            return HttpResponseRedirect(link.redirect_to)
