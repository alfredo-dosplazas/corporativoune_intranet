from django.contrib import admin

from apps.auditoria.models import UserAccessLog, AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'action', 'app_label', 'model_name', 'object_id', 'old_data', 'new_data',
                    'created_at', 'extra']
    list_per_page = 20


@admin.register(UserAccessLog)
class UserAccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'path', 'method', 'user_agent', 'created_at']
    list_per_page = 20
