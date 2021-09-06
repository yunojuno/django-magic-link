from django.urls import path

from . import views

urlpatterns = [
    path(
        "<uuid:token>/",
        views.MagicLinkView.as_view(),
        name="magic_link",
    ),
]
