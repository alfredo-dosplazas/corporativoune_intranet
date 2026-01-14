from django.contrib import admin

from apps.auditoria.models import UserAccessLog


@admin.register(UserAccessLog)
class UserAccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'path', 'method', 'user_agent', 'created_at']
    list_per_page = 20
