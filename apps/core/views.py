from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
import os

def service_worker(request):
    sw_path = os.path.join(settings.BASE_DIR, 'static', 'service-worker.js')
    with open(sw_path, 'r') as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')

def offline_view(request):
    return render(request, 'offline.html')
