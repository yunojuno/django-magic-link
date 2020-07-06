import logging

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views import View

from magic_link.models import InvalidTokenUse, MagicLink

logger = logging.getLogger(__name__)


class MagicLinkView(View):
    def get(self, request: HttpRequest, token: str):
        """
        Render login page.

        If the link is invalid, or the user is already logged in, then this
        view will raise a PermissionDenied, which will render the 403 template.

        """
        link = get_object_or_404(MagicLink, token=token)
        link.use_link(request)
        try:
            link.validate(request)
        except InvalidTokenUse:
            logger.warning("Invalid magic link use")
            raise PermissionDenied("Magic link is invalid.")
        return render(request, template_name="index.html", context={"link": link})

    def post(self, request: HttpRequest, token: str):
        """
        Handle the login POST request.

        If the link is invalid, or the user is already logged in, then this
        view will raise a PermissionDenied, which will render the 403 template.

        If the use is valid then this will call the login() method, and redirect
        the user (now authenticated).

        The token will be rendered inactive at this point.

        """
        link = get_object_or_404(MagicLink, token=token)
        link.use_link(request)
        try:
            link.validate(request)
        except InvalidTokenUse:
            logger.warning("Invalid magic link use")
            raise PermissionDenied("Magic link is invalid.")
        link.login(request)
        link.disable()
        return HttpResponseRedirect("/admin")
