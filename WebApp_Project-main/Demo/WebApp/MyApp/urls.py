from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="Home"),
    path("todos/", views.todos, name="Todos"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("api/tasks/", views.task_events, name="task_events"),
    path("tasks/create/", views.create_task, name="create_task"),
    path("tasks/delete/<int:task_id>/", views.delete_task, name="delete_task"),
    path("tasks/snooze/<int:task_id>/", views.snooze_task, name="snooze_task"),
    path('map/', views.map_view, name='map'),
    path('add_marker/', views.add_marker, name='add_marker'),
    path('delete_marker/<int:marker_id>/', views.delete_marker, name='delete_marker'),
    path('clear_markers/', views.clear_markers, name='clear_markers'),
    
]