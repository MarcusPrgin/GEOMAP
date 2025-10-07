from django.contrib import admin
from .models import TodoItem
from .models import Task
from .models import UserLocation
from .models import Location
from .models import Marker

# Register your models here.
admin.site.register(TodoItem)
admin.site.register(Task)
admin.site.register(UserLocation)
admin.site.register(Location)
admin.site.register(Marker)

class MarkerAdmin(admin.ModelAdmin):
    list_display = ('id', 'latitude', 'longitude', 'created_at')
    search_fields = ('latitude', 'longitude')
    ordering = ('-created_at',)