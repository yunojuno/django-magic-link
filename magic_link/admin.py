from django.contrib import admin

from .models import MagicLink, MagicLinkUse


class LoggedInMixin:
    """Mixin used to provide a logged_in method for display purposes."""

    def logged_in(self, obj: MagicLinkUse) -> bool:
        """Return True if the object was the one used to login."""
        return obj.timestamp == obj.link.logged_in_at

    logged_in.boolean = True  # type: ignore
    logged_in.short_description = "Used for login"  # type: ignore


class MagicLinkUseInline(LoggedInMixin, admin.TabularInline):
    model = MagicLinkUse
    readonly_fields = (
        "link",
        "timestamp",
        "session_key",
        "remote_addr",
        "http_method",
        "logged_in",
        "error",
    )
    exclude = ("ua_string",)
    extra = 0


class MagicLinkAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "token",
        "expires_at",
        "accessed_at",
        "logged_in_at",
        "is_active",
        "has_been_used",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__username",
        "token",
    )
    raw_id_fields = ("user",)
    readonly_fields = (
        "token",
        "created_at",
        "expires_at",
        "accessed_at",
        "logged_in_at",
        "has_expired",
        "has_been_used",
    )
    ordering = ("-created_at",)
    inlines = (MagicLinkUseInline,)


admin.site.register(MagicLink, MagicLinkAdmin)


class MagicLinkUseAdmin(LoggedInMixin, admin.ModelAdmin):

    list_display = ("link", "http_method", "session_key", "logged_in")
    search_fields = (
        "session_key",
        "link__token",
    )
    raw_id_fields = ("link",)
    readonly_fields = (
        "link",
        "timestamp",
        "session_key",
        "remote_addr",
        "http_method",
        "ua_string",
        "error",
        "logged_in",
    )
    ordering = ("-timestamp",)


admin.site.register(MagicLinkUse, MagicLinkUseAdmin)
