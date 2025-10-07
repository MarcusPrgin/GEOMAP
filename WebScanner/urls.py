from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect

def home(request):
    if request.user.is_authenticated:
        return redirect('MyApp:dashboard')
    else:
        return render(request, "home.html")

def map_view(request):
    return render(request, "map.html")  # Adjust template name as needed

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('map/', map_view, name='map_view'),  # Add this line
    path('myapp/', include('MyApp.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]