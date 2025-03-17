from django.contrib import admin
from .models import UserQuery, OpenAISettings

@admin.register(UserQuery)
class UserQueryAdmin(admin.ModelAdmin):
    list_display = ('query_preview', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('query', 'response', 'user__username')
    
    def query_preview(self, obj):
        return obj.query[:50] + '...' if len(obj.query) > 50 else obj.query
    query_preview.short_description = 'Query Preview'

@admin.register(OpenAISettings)
class OpenAISettingsAdmin(admin.ModelAdmin):
    list_display = ('api_key_name', 'is_active', 'last_updated')
    list_filter = ('is_active',)
    search_fields = ('api_key_name',)
    readonly_fields = ('last_updated',)
    fieldsets = (
        ('API Settings', {
            'fields': ('api_key_name', 'api_key', 'is_active')
        }),
        ('Time Information', {
            'fields': ('last_updated',)
        }),
    )
