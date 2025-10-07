# admin.py
from django.contrib import admin
from .models import (
    # Your existing models
    Marker, UserLocation, Task, Location,
    # New location/friends models
    UserProfile, Friendship, ProximityAlert, ProximityNotification
)

# Your existing models admin
@admin.register(Marker)
class MarkerAdmin(admin.ModelAdmin):
    list_display = ('title', 'latitude', 'longitude', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'accuracy_m', 'captured_at')
    list_filter = ('captured_at', 'accuracy_m')
    search_fields = ('user__username',)
    readonly_fields = ('captured_at',)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'start_time', 'end_time', 'is_snoozed')
    list_filter = ('is_snoozed', 'start_time', 'end_time')
    search_fields = ('user__username', 'title')
    date_hierarchy = 'start_time'

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)

# New location/friends models admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'latitude', 'longitude', 'location_sharing_enabled', 'last_location_update')
    list_filter = ('location_sharing_enabled', 'proximity_notifications_enabled', 'last_location_update')
    search_fields = ('user__username',)
    readonly_fields = ('last_location_update',)

@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ('requester', 'addressee', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('requester__username', 'addressee__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ProximityAlert)
class ProximityAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'friend', 'distance_threshold', 'is_active', 'last_triggered')
    list_filter = ('is_active', 'distance_threshold', 'last_triggered')
    search_fields = ('user__username', 'friend__username')
    readonly_fields = ('created_at', 'last_triggered')

@admin.register(ProximityNotification)
class ProximityNotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'friend', 'distance', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('user__username', 'friend__username')
    readonly_fields = ('created_at',)
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notifications marked as read.')
    mark_as_read.short_description = 'Mark selected notifications as read'
    
    actions = ['mark_as_read']