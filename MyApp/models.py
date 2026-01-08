from django.conf import settings
from django.db import models
from django.utils import timezone


class Marker(models.Model):
    title = models.CharField(max_length=200, default="Location Point")
    description = models.TextField(blank=True, null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} at ({self.latitude}, {self.longitude})"


class UserLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True
    )
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy_m = models.IntegerField(null=True, blank=True)
    captured_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.latitude}, {self.longitude} at {self.captured_at}"


class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    location_sharing_enabled = models.BooleanField(default=False)
    proximity_notifications_enabled = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user}'s Profile"

    def update_location(self, lat, lng):
        self.latitude = float(lat)
        self.longitude = float(lng)
        self.last_location_update = timezone.now()
        self.save(update_fields=["latitude", "longitude", "last_location_update"])

    def get_distance_to(self, other_profile):
        """
        Distance in KM using a simple haversine implementation.
        (No external dependencies like geopy.)
        """
        if not all(
            [
                self.latitude is not None,
                self.longitude is not None,
                other_profile.latitude is not None,
                other_profile.longitude is not None,
            ]
        ):
            return None

        import math

        lat1 = math.radians(float(self.latitude))
        lon1 = math.radians(float(self.longitude))
        lat2 = math.radians(float(other_profile.latitude))
        lon2 = math.radians(float(other_profile.longitude))

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))
        R = 6371.0  # Earth radius in km
        return R * c


class Friendship(models.Model):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (ACCEPTED, "Accepted"),
        (DECLINED, "Declined"),
    ]

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_sent",
    )
    addressee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_requests_received",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["requester", "addressee"], name="unique_friendship_request"
            )
        ]

    def __str__(self):
        return f"{self.requester} -> {self.addressee} ({self.status})"

    @classmethod
    def get_friends(cls, user):
        return settings.AUTH_USER_MODEL and (
            models.get_model  # not used; keep method below
        )

    @classmethod
    def get_friends(cls, user):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        return User.objects.filter(
            models.Q(
                friend_requests_sent__addressee=user,
                friend_requests_sent__status=cls.ACCEPTED,
            )
            | models.Q(
                friend_requests_received__requester=user,
                friend_requests_received__status=cls.ACCEPTED,
            )
        ).distinct()


class ProximityAlert(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="proximity_alerts"
    )
    friend = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_proximity_alerts",
    )
    distance_threshold = models.FloatField(default=1.0)  # kilometers
    is_active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "friend"], name="unique_prox_alert")
        ]

    def __str__(self):
        return f"{self.user} -> {self.friend} alert"


class ProximityNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    friend = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="friend_notifications",
    )
    distance = models.FloatField()  # km
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user}: {self.friend} is nearby"
