
# views.py - Working version without model dependencies

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.db import connection
import json

from django.http import JsonResponse
from .models import Marker

def markers_in_bounds(request):
    try:
        south = float(request.GET.get("south"))
        north = float(request.GET.get("north"))
        west  = float(request.GET.get("west"))
        east  = float(request.GET.get("east"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Provide south,north,west,east as numbers."}, status=400)

    qs = Marker.objects.filter(
        latitude__gte=south, latitude__lte=north,
        longitude__gte=west, longitude__lte=east,
    ).values("id", "latitude", "longitude", "title", "description", "created_at")

    return JsonResponse({"markers": list(qs)})


# ===== AUTHENTICATION VIEWS =====

# @require_http_methods(["GET"])
# def get_markers(request):
#     """API endpoint to fetch markers from database"""
#     north = float(request.GET.get('north', 90))
#     south = float(request.GET.get('south', -90))
#     east = float(request.GET.get('east', 180))
#     west = float(request.GET.get('west', -180))
    
#     with connection.cursor() as cursor:
#         cursor.execute("""
#             SELECT id, latitude, longitude, title, category
#             FROM myapp_markers
#             WHERE latitude BETWEEN %s AND %s
#               AND longitude BETWEEN %s AND %s
#             LIMIT 5000
#         """, [south, north, west, east])
        
#         columns = [col[0] for col in cursor.description]
#         markers = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
#     return JsonResponse({'markers': markers})

def home(request):
    """Home page - returns API status"""
    return JsonResponse({'message': 'Map API is running', 'status': 'ok'})

def register_view(request):
    """Handle user registration with auto-login"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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
    """Main dashboard - simplified without models"""
    context = {
        'user_profile': {'location_sharing_enabled': False},
        'friend_profiles': [],
        'pending_requests': [],
    }
    return render(request, 'MyApp/dashboard.html', context)

def map_view(request):
    """Display the map with clustering"""
    return render(request, 'map.html', {
        'is_tracking_enabled': False,
    })

@login_required
def notifications(request):
    """Display user notifications - simplified"""
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
    
    return render(request, 'MyApp/user_search.html', {
        'users': users,
        'query': query
    })

@login_required
def send_friend_request(request, user_id):
    """Send a friend request - placeholder"""
    messages.info(request, "Friend request feature coming soon!")
    return redirect('MyApp:user_search')

@login_required
def handle_friend_request(request, friendship_id, action):
    """Handle friend request - placeholder"""
    messages.info(request, "Friend request feature coming soon!")
    return redirect('MyApp:dashboard')

# ===== LOCATION MANAGEMENT VIEWS =====

@csrf_exempt
@require_POST
def update_location(request):
    """API endpoint to update user's current location"""
    try:
        data = json.loads(request.body)
        latitude = float(data.get('latitude'))
        longitude = float(data.get('longitude'))
        return JsonResponse({'status': 'success', 'message': 'Location updated'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def toggle_location_sharing(request):
    """Toggle location sharing on/off"""
    return JsonResponse({'status': 'success'})

# ===== MAP API ENDPOINTS =====

@csrf_exempt
@require_http_methods(["POST"])
def add_marker(request):
    try:
        data = json.loads(request.body)
        lat = float(data.get("latitude"))
        lng = float(data.get("longitude"))
        title = (data.get("title") or "Location Point")[:200]
        description = data.get("description") or ""

        m = Marker.objects.create(
            latitude=lat,
            longitude=lng,
            title=title,
            description=description,
        )

        return JsonResponse({
            "success": True,
            "id": m.id,
            "latitude": m.latitude,
            "longitude": m.longitude
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=400)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_marker(request, marker_id):
    deleted, _ = Marker.objects.filter(id=marker_id).delete()
    return JsonResponse({"success": bool(deleted)})

@csrf_exempt
@require_http_methods(["DELETE"])
def clear_markers(request):
    Marker.objects.all().delete()
    return JsonResponse({"success": True})

# ===== TRACKING/NOTIFICATION VIEWS =====

@login_required
@csrf_exempt
def toggle_tracking(request):
    """Toggle peer tracking on/off"""
    if request.method == 'POST':
        return JsonResponse({'is_tracking_enabled': True})
    return JsonResponse({'status': 'error'})

@login_required
def get_proximity_notifications(request):
    """Get proximity notifications for the user"""
    return JsonResponse({'notifications': []})

@login_required
@csrf_exempt
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    if request.method == 'POST':
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'success'})

# ===== PLACEHOLDER VIEWS FOR OPTIONAL FEATURES =====

@login_required
def marker_list(request):
    """List all markers using raw SQL"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, latitude, longitude, title FROM myapp_markers LIMIT 100")
        columns = [col[0] for col in cursor.description]
        markers = [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    return render(request, 'marker_list.html', {'markers': markers})

@login_required
def marker_detail(request, pk):
    """Marker detail view"""
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM myapp_markers WHERE id = %s", [pk])
        columns = [col[0] for col in cursor.description]
        row = cursor.fetchone()
        marker = dict(zip(columns, row)) if row else None
    
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
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM myapp_markers WHERE id = %s", [pk])
        return redirect('MyApp:marker_list')
    return render(request, 'marker_delete.html')
