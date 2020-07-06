from django.contrib import admin
from django.urls import include, path

# import magic_link.urls
admin.autodiscover()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("magic-link/", include("magic_link.urls")),
]
