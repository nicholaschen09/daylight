from django.contrib import admin
from core.models import Device, TelemetryReading


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'device_type', 'is_active', 'created_at']
    list_filter = ['device_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'device_type', 'is_active')
        }),
        ('Configuration', {
            'fields': ('properties', 'current_state')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TelemetryReading)
class TelemetryReadingAdmin(admin.ModelAdmin):
    list_display = ['device', 'timestamp', 'power_watts', 'charge_wh']
    list_filter = ['device__device_type', 'timestamp']
    search_fields = ['device__name']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'timestamp'
