from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("<uuid:token>/", views.MagicLinkView.as_view(), name="use_magic_link",),
]
