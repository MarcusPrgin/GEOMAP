from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = "MyApp"

urlpatterns = [
    # Auth
    path("register/", views.register_view, name="register"),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),

    # Pages
    path("", views.dashboard, name="dashboard"),
    path("map/", views.map_view, name="map"),
    path("profile/", views.profile, name="profile"),
    path("notifications/", views.notifications, name="notifications"),

    # Marker API
    path("api/markers/", views.markers_in_bounds, name="markers_in_bounds"),
    path("api/add-marker/", views.add_marker, name="add_marker"),
    path("api/delete-marker/<int:marker_id>/", views.delete_marker, name="delete_marker"),
    path("api/clear-markers/", views.clear_markers, name="clear_markers"),

    # Friends
    path("search/", views.user_search, name="user_search"),
    path("send-friend-request/<int:user_id>/", views.send_friend_request, name="send_friend_request"),
    path("friend-request/<int:friendship_id>/<str:action>/", views.handle_friend_request, name="handle_friend_request"),

    # Location / tracking
    path("update-location/", views.update_location, name="update_location"),
    path("toggle-location-sharing/", views.toggle_location_sharing, name="toggle_location_sharing"),
    path("toggle-tracking/", views.toggle_tracking, name="toggle_tracking"),
    path("get-proximity-notifications/", views.get_proximity_notifications, name="get_proximity_notifications"),
    path("mark-notification-read/<int:notification_id>/", views.mark_notification_read, name="mark_notification_read"),

    # Optional pages
    path("marker-list/", views.marker_list, name="marker_list"),
    path("marker/<int:pk>/", views.marker_detail, name="marker_detail"),
    path("marker/create/", views.marker_create, name="marker_create"),
    path("marker/<int:pk>/update/", views.marker_update, name="marker_update"),
    path("marker/<int:pk>/delete/", views.marker_delete, name="marker_delete"),
]
