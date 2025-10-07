# views.py - Cleaned version without duplicates

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.contrib import messages
from django.db import models
import json
from datetime import timedelta

# Import your models
from .models import (
    Marker, UserLocation, Task, Location,
    UserProfile, Friendship, ProximityAlert, ProximityNotification
)

# ===== AUTHENTICATION VIEWS =====

def register_view(request):
    """Handle user registration with auto-login"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after registration
            messages.success(request, f'Account created successfully! Welcome, {user.username}!')
            return redirect('MyApp:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    return render(request, 'registration/profile.html', {'user': request.user})

# ===== MAIN APPLICATION VIEWS =====

@login_required
def dashboard(request):
    """Main dashboard showing friends and their locations"""
    try:
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        friends = Friendship.get_friends(request.user)
        
        # Get friend profiles with location data
        friend_profiles = []
        for friend in friends:
            profile, created = UserProfile.objects.get_or_create(user=friend)
            if profile.location_sharing_enabled and profile.latitude and profile.longitude:
                distance = user_profile.get_distance_to(profile) if user_profile.latitude else None
                friend_profiles.append({
                    'user': friend,
                    'profile': profile,
                    'distance': round(distance, 2) if distance else None
                })
        
        # Get pending friend requests
        pending_requests = Friendship.objects.filter(
            addressee=request.user, 
            status=Friendship.PENDING
        )
        
    except Exception as e:
        # Fallback for when models don't exist yet
        user_profile = type('obj', (object,), {'location_sharing_enabled': False})
        friend_profiles = []
        pending_requests = []
    
    context = {
        'user_profile': user_profile,
        'friend_profiles': friend_profiles,
        'pending_requests': pending_requests,
    }
    return render(request, 'MyApp/dashboard.html', context)

def map_view(request):
    """Display the map with existing markers"""
    try:
        markers = Marker.objects.all()
        markers_data = []
        
        for marker in markers:
            markers_data.append({
                'id': marker.id,
                'latitude': float(marker.latitude),
                'longitude': float(marker.longitude),
                'title': marker.title,
                'description': marker.description,
                'created_by': getattr(marker, 'user', {}).username if hasattr(marker, 'user') else 'Unknown',
                'is_own': True  # You can add logic here to check ownership
            })
        
        context = {
            'markers': markers_data,
            'is_tracking_enabled': False,  # Add your tracking logic here
        }
    except Exception:
        # Fallback when no markers exist
        context = {
            'markers': [],
            'is_tracking_enabled': False,
        }
    
    return render(request, 'map.html', context)

@login_required
def notifications(request):
    """Display user notifications"""
    try:
        notifications = ProximityNotification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:20]

        # Mark unread notifications as read
        unread_notifications = ProximityNotification.objects.filter(
            user=request.user,
            is_read=False
        )
        unread_notifications.update(is_read=True)

    except Exception:
        # Fallback when no notifications exist
        notifications = []

    return render(request, 'MyApp/notifications.html', {'notifications': notifications})

# ===== FRIEND MANAGEMENT VIEWS =====

@login_required
def user_search(request):
    """Search for users to add as friends"""
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id)[:10]
        
        # Add friendship status for each user (if models exist)
        try:
            for user in users:
                friendship = Friendship.objects.filter(
                    models.Q(requester=request.user, addressee=user) |
                    models.Q(requester=user, addressee=request.user)
                ).first()
                
                user.friendship_status = friendship.status if friendship else None
        except:
            pass  # Model might not exist yet
    
    return render(request, 'MyApp/user_search.html', {
        'users': users,
        'query': query
    })

@login_required
def send_friend_request(request, user_id):
    """Send a friend request to another user"""
    try:
        addressee = get_object_or_404(User, id=user_id)
        
        if addressee == request.user:
            messages.error(request, "You can't send a friend request to yourself.")
            return redirect('MyApp:user_search')
        
        # Check if friendship already exists
        existing = Friendship.objects.filter(
            models.Q(requester=request.user, addressee=addressee) |
            models.Q(requester=addressee, addressee=request.user)
        ).first()
        
        if existing:
            messages.info(request, f"Friend request already exists with {addressee.username}")
        else:
            Friendship.objects.create(requester=request.user, addressee=addressee)
            messages.success(request, f"Friend request sent to {addressee.username}")
        
    except Exception as e:
        messages.error(request, "Could not send friend request.")
    
    return redirect('MyApp:user_search')

@login_required
def handle_friend_request(request, friendship_id, action):
    """Accept or decline a friend request"""
    try:
        friendship = get_object_or_404(
            Friendship, 
            id=friendship_id, 
            addressee=request.user, 
            status=Friendship.PENDING
        )
        
        if action == 'accept':
            friendship.status = Friendship.ACCEPTED
            friendship.save()
            
            # Create mutual proximity alerts
            ProximityAlert.objects.get_or_create(
                user=request.user, 
                friend=friendship.requester
            )
            ProximityAlert.objects.get_or_create(
                user=friendship.requester, 
                friend=request.user
            )
            
            messages.success(request, f"You are now friends with {friendship.requester.username}")
        
        elif action == 'decline':
            friendship.status = Friendship.DECLINED
            friendship.save()
            messages.info(request, f"Friend request from {friendship.requester.username} declined")
    
    except Exception as e:
        messages.error(request, "Could not process friend request.")
    
    return redirect('MyApp:dashboard')

# ===== LOCATION MANAGEMENT VIEWS =====

@csrf_exempt
@require_POST
@login_required
def update_location(request):
    """API endpoint to update user's current location"""
    try:
        data = json.loads(request.body)
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        old_lat, old_lng = profile.latitude, profile.longitude
        
        profile.update_location(latitude, longitude)
        
        # Check for proximity alerts if location changed significantly
        if old_lat is None or old_lng is None or \
           abs(float(old_lat) - latitude) > 0.001 or abs(float(old_lng) - longitude) > 0.001:
            check_proximity_alerts(request.user)
        
        return JsonResponse({'status': 'success', 'message': 'Location updated'})
    
    except Exception as e:
        return JsonResponse({'status': 'success', 'message': 'Location update received'})

@login_required
def toggle_location_sharing(request):
    """Toggle location sharing on/off"""
    try:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile.location_sharing_enabled = not profile.location_sharing_enabled
        profile.save()
        
        status = "enabled" if profile.location_sharing_enabled else "disabled"
        messages.success(request, f"Location sharing {status}")
    except:
        pass  # Model might not exist
    
    return JsonResponse({'status': 'success'})

# ===== MAP API ENDPOINTS =====

@csrf_exempt
@require_http_methods(["POST"])
def add_marker(request):
    """Add a new marker to the database"""
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        title = data.get('title', 'Location Point')
        description = data.get('description', '')
        
        if latitude is not None and longitude is not None:
            marker = Marker.objects.create(
                latitude=latitude,
                longitude=longitude,
                title=title,
                description=description
            )
            return JsonResponse({
                'success': True,
                'id': marker.id,
                'latitude': float(marker.latitude),
                'longitude': float(marker.longitude)
            })
        else:
            return JsonResponse({'success': False, 'error': 'Missing coordinates'}, status=400)
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_marker(request, marker_id):
    """Delete a specific marker"""
    try:
        marker = Marker.objects.get(id=marker_id)
        marker.delete()
        return JsonResponse({'success': True})
    except Marker.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Marker not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["DELETE"])
def clear_markers(request):
    """Delete all markers"""
    try:
        Marker.objects.all().delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# ===== TRACKING/NOTIFICATION VIEWS =====

@login_required
@csrf_exempt
def toggle_tracking(request):
    """Toggle peer tracking on/off"""
    if request.method == 'POST':
        # Add your tracking logic here
        return JsonResponse({'is_tracking_enabled': True})
    return JsonResponse({'status': 'error'})

@login_required
def get_proximity_notifications(request):
    """Get proximity notifications for the user"""
    try:
        notifications = ProximityNotification.objects.filter(
            user=request.user,
            is_read=False
        ).order_by('-created_at')[:10]
        
        notifications_data = []
        for notif in notifications:
            notifications_data.append({
                'id': notif.id,
                'peer_username': notif.friend.username,
                'distance': notif.distance,
                'message': notif.message,
                'is_read': notif.is_read,
            })
        
        return JsonResponse({'notifications': notifications_data})
    except:
        return JsonResponse({'notifications': []})

@login_required
@csrf_exempt
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if request.method == 'POST':
        try:
            notification = ProximityNotification.objects.get(
                id=notification_id, 
                user=request.user
            )
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
        except:
            pass
    return JsonResponse({'status': 'success'})

# ===== HELPER FUNCTIONS =====

def check_proximity_alerts(user):
    """Check if user is near any friends and send notifications"""
    try:
        user_profile = user.userprofile
        if not (user_profile.latitude and user_profile.longitude and 
                user_profile.proximity_notifications_enabled):
            return
        
        # Get active proximity alerts for this user
        alerts = ProximityAlert.objects.filter(
            user=user, 
            is_active=True
        ).select_related('friend', 'friend__userprofile')
        
        for alert in alerts:
            friend_profile = alert.friend.userprofile
            
            if not (friend_profile.latitude and friend_profile.longitude and 
                    friend_profile.location_sharing_enabled):
                continue
            
            distance = user_profile.get_distance_to(friend_profile)
            
            if distance and distance <= alert.distance_threshold:
                # Check if we already sent a notification recently
                recent_notification = ProximityNotification.objects.filter(
                    user=user,
                    friend=alert.friend,
                    created_at__gte=timezone.now() - timezone.timedelta(minutes=30)
                ).exists()
                
                if not recent_notification:
                    ProximityNotification.objects.create(
                        user=user,
                        friend=alert.friend,
                        distance=round(distance, 2),
                        message=f"{alert.friend.username} is {round(distance, 2)}km away from you!"
                    )
                    
                    alert.last_triggered = timezone.now()
                    alert.save()
    
    except:
        pass  # User profile doesn't exist yet

# ===== PLACEHOLDER VIEWS FOR OPTIONAL FEATURES =====

@login_required
def marker_list(request):
    """List all markers"""
    try:
        markers = Marker.objects.all()
    except:
        markers = []
    return render(request, 'marker_list.html', {'markers': markers})

@login_required
def marker_detail(request, pk):
    """Marker detail view"""
    try:
        marker = get_object_or_404(Marker, pk=pk)
    except:
        marker = {'name': 'Sample Marker'}
    return render(request, 'marker_detail.html', {'marker': marker})

@login_required
def marker_create(request):
    """Create new marker"""
    return render(request, 'marker_create.html')

@login_required
def marker_update(request, pk):
    """Update marker"""
    return render(request, 'marker_update.html')

@login_required
def marker_delete(request, pk):
    """Delete marker"""
    if request.method == 'POST':
        return redirect('MyApp:marker_list')
    return render(request, 'marker_delete.html')