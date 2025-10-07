# from django.db import models
# from django.contrib.auth.models import User
# from django.conf import settings

# class Marker(models.Model):
#     title = models.CharField(max_length=200, default='Location Point')
#     description = models.TextField(blank=True, null=True)
#     latitude = models.DecimalField(max_digits=10, decimal_places=7)
#     longitude = models.DecimalField(max_digits=10, decimal_places=7)
#     created_at = models.DateTimeField(auto_now_add=True)
    
#     def __str__(self):
#         return f"{self.title} at ({self.latitude}, {self.longitude})"
    
#     class Meta:
#         ordering = ['-created_at']

# class UserLocation(models.Model):
#     user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
#     latitude = models.DecimalField(max_digits=9, decimal_places=6)
#     longitude = models.DecimalField(max_digits=9, decimal_places=6)
#     accuracy_m = models.IntegerField(null=True, blank=True)
#     captured_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f"{self.latitude}, {self.longitude} at {self.captured_at}"
  
# class Task(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     title = models.CharField(max_length=100)
#     start_time = models.DateTimeField()
#     end_time = models.DateTimeField()
#     reminder_time = models.DateTimeField(null=True, blank=True)
#     is_snoozed = models.BooleanField(default=False)
#     snoozed_until = models.DateTimeField(null=True, blank=True)

#     def __str__(self):
#         return self.title
    
# class Location(models.Model):
#     name = models.CharField(max_length=100)
#     latitude = models.FloatField()
#     longitude = models.FloatField()

#     def __str__(self):
#         return self.name

# models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.conf import settings
from geopy.distance import geodesic

# Your existing models
class Marker(models.Model):
    title = models.CharField(max_length=200, default='Location Point')
    description = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} at ({self.latitude}, {self.longitude})"
    
    class Meta:
        ordering = ['-created_at']

class UserLocation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    accuracy_m = models.IntegerField(null=True, blank=True)
    captured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.latitude}, {self.longitude} at {self.captured_at}"
  
class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reminder_time = models.DateTimeField(null=True, blank=True)
    is_snoozed = models.BooleanField(default=False)
    snoozed_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
    
class Location(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()

    def __str__(self):
        return self.name

# New location/friends models
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    location_sharing_enabled = models.BooleanField(default=False)
    proximity_notifications_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_location(self, lat, lng):
        """Update user's location and timestamp"""
        self.latitude = lat
        self.longitude = lng
        self.last_location_update = timezone.now()
        self.save()
    
    def get_distance_to(self, other_profile):
        """Calculate distance to another user in kilometers"""
        if not all([self.latitude, self.longitude, other_profile.latitude, other_profile.longitude]):
            return None
        
        coords_1 = (float(self.latitude), float(self.longitude))
        coords_2 = (float(other_profile.latitude), float(other_profile.longitude))
        return geodesic(coords_1, coords_2).kilometers

class Friendship(models.Model):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    DECLINED = 'declined'
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (ACCEPTED, 'Accepted'),
        (DECLINED, 'Declined'),
    ]
    
    requester = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_sent')
    addressee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_requests_received')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('requester', 'addressee')
    
    def __str__(self):
        return f"{self.requester.username} -> {self.addressee.username} ({self.status})"
    
    @classmethod
    def get_friends(cls, user):
        """Get all accepted friends for a user"""
        return User.objects.filter(
            models.Q(friend_requests_sent__addressee=user, friend_requests_sent__status=cls.ACCEPTED) |
            models.Q(friend_requests_received__requester=user, friend_requests_received__status=cls.ACCEPTED)
        ).distinct()

class ProximityAlert(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proximity_alerts')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_proximity_alerts')
    distance_threshold = models.FloatField(default=1.0)  # kilometers
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'friend')
    
    def __str__(self):
        return f"{self.user.username} -> {self.friend.username} alert"

class ProximityNotification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_notifications')
    distance = models.FloatField()  # distance in km when notification was sent
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Notification for {self.user.username}: {self.friend.username} is nearby"