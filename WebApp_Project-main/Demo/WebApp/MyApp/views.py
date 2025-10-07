from django.shortcuts import render
from .models import TodoItem

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Task
from datetime import timedelta

from django.shortcuts import render

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Marker
import json

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Marker


from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import Marker

def map_view(request):
    """Display the map with existing markers"""
    markers = Marker.objects.all()
    markers_data = []
    
    for marker in markers:
        markers_data.append({
            'id': marker.id,
            'title': marker.title,
            'description': marker.description or '',
            'latitude': float(marker.latitude),
            'longitude': float(marker.longitude),
        })
    
    context = {
        'markers': markers_data,
    }
    return render(request, 'map.html', context)

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
                title=title,
                description=description,
                latitude=latitude,
                longitude=longitude
            )
            return JsonResponse({
                'success': True,
                'id': marker.id,
                'title': marker.title,
                'description': marker.description,
                'latitude': float(marker.latitude),
                'longitude': float(marker.longitude)
            })
        else:
            return JsonResponse({'success': False, 'error': 'Missing coordinates'}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
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


def map_view(request):
    """Display the map with existing markers"""
    markers = Marker.objects.all()
    markers_data = []
    
    for marker in markers:
        markers_data.append({
            'id': marker.id,
            'latitude': float(marker.latitude),
            'longitude': float(marker.longitude),
        })
    
    context = {
        'markers': markers_data,
    }
    return render(request, 'map.html', context)

@csrf_exempt
@require_http_methods(["POST"])
def add_marker(request):
    """Add a new marker to the database"""
    try:
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is not None and longitude is not None:
            marker = Marker.objects.create(
                latitude=latitude,
                longitude=longitude
            )
            return JsonResponse({
                'success': True,
                'id': marker.id,
                'latitude': float(marker.latitude),
                'longitude': float(marker.longitude)
            })
        else:
            return JsonResponse({'success': False, 'error': 'Missing coordinates'}, status=400)
    
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
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
    

def home(request):
    return render(request, "home.html")

def todos(request):
    items = TodoItem.objects.all()
    return render(request, "todos.html", {"todos":items})

#---------------------------------------------------------------

def calendar_view(request):
    return render(request, "calendar.html")

def task_events(request):
    tasks = Task.objects.filter(user=request.user)
    events = []
    for task in tasks:
        if task.is_snoozed and task.snoozed_until and task.snoozed_until > timezone.now():
            continue  # skip snoozed tasks
        events.append({
            "id": task.id,
            "title": task.title,
            "start": task.start_time.isoformat(),
            "end": task.end_time.isoformat(),
        })
    return JsonResponse(events, safe=False)


@csrf_exempt
def create_task(request):
    global task
    if request.method == "POST":
        data = request.POST
        task = Task.objects.create(
            user=request.user,
            title=data["title"],
            start_time=data["start"],
            end_time=data["end"],
            reminder_time=data.get("reminder")
        )
        return JsonResponse({"status": "created"})

@csrf_exempt
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.delete()
    return JsonResponse({"status": "deleted"})

@csrf_exempt
def snooze_task(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    task.is_snoozed = True
    task.snoozed_until = timezone.now() + timedelta(hours=1)
    task.save()
    return JsonResponse({"status": "snoozed"})
