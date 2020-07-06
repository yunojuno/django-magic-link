import logging

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
        try:
            link.validate(request)
        except InvalidTokenUse as ex:
            link.log_use(request, status_code=403)
            return render(
                request,
                template_name="error.html",
                context={"link": link, "error": ex},
                status=403,
            )
        else:
            link.log_use(request, status_code=200)
            return render(
                request,
                template_name="logmein.html",
                context={"link": link},
                status=200,
            )

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
        try:
            link.validate(request)
        except InvalidTokenUse as ex:
            link.log_use(request, status_code=403)
            return render(
                request,
                template_name="error.html",
                context={"link": link, "error": ex},
                status=403,
            )
        else:
            link.login(request)
            link.log_use(request, status_code=302)
            link.disable()
            return HttpResponseRedirect(link.redirect_to)
