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
        "link_is_valid",
        "error",
    )
    exclude = ("ua_string",)
    extra = 0


class MagicLinkAdmin(admin.ModelAdmin):

    list_display = ("user", "token", "expires_at", "is_active", "is_valid")
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__username",
        "token",
    )
    raw_id_fields = ("user",)
    readonly_fields = ("token", "created_at", "has_expired")
    ordering = ("-created_at",)
    inlines = (MagicLinkUseInline,)


admin.site.register(MagicLink, MagicLinkAdmin)


class MagicLinkUseAdmin(admin.ModelAdmin):

    list_display = ("link", "http_method", "session_key", "link_is_valid")
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
        "link_is_valid",
    )
    ordering = ("-timestamp",)


admin.site.register(MagicLinkUse, MagicLinkUseAdmin)
