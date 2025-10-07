from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Marker(models.Model):
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Marker at ({self.latitude}, {self.longitude})"
    
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

# Create your models here.
class TodoItem(models.Model):
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
  
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

class Marker(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Marker at ({self.latitude}, {self.longitude})"
    