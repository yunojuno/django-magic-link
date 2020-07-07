from django.contrib import admin

from .models import MagicLink, MagicLinkUse


class MagicLinkUseInline(admin.TabularInline):
    model = MagicLinkUse
    readonly_fields = (
        "link",
        "timestamp",
        "session_key",
        "remote_addr",
        "http_method",
        "_logged_in",
        "error",
    )
    exclude = ("ua_string",)
    extra = 0

    def _logged_in(self, obj):
        """Used to enable 'boolean' display in admin."""
        return obj.logged_in

    _logged_in.boolean = True


class MagicLinkAdmin(admin.ModelAdmin):

    list_display = ("user", "token", "expires_at", "accessed_at", "logged_in_at", "is_active", "has_been_used")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__username",
        "token",
    )
    raw_id_fields = ("user",)
    readonly_fields = ("token", "created_at", "expires_at", "accessed_at", "logged_in_at", "has_expired", "has_been_used")
    ordering = ("-created_at",)
    inlines = (MagicLinkUseInline,)


admin.site.register(MagicLink, MagicLinkAdmin)


class MagicLinkUseAdmin(admin.ModelAdmin):

    list_display = ("link", "http_method", "session_key", "_logged_in")
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
        "_logged_in",
    )
    ordering = ("-timestamp",)

    def _logged_in(self, obj):
        """Used to enable 'boolean' display in admin."""
        return obj.logged_in

    _logged_in.boolean = True

admin.site.register(MagicLinkUse, MagicLinkUseAdmin)
