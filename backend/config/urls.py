from django.contrib import admin
from django.urls import path, include, re_path
from django.http import HttpResponse, JsonResponse
from django.conf import settings

def spa(request):
    index = settings.FRONTEND_DIST / 'index.html'
    if not index.is_file():
        return HttpResponse('Frontend build missing. Run npm run build in frontend.', status=503)
    return HttpResponse(index.read_bytes(), content_type='text/html')

urlpatterns = [
    path('healthz', lambda request: JsonResponse({'ok': True})),
    path('admin/', admin.site.urls),
    path('api/', include('store.urls')),
    path('api/owner/', include('owner.urls')),
    re_path(r'^(?!static/|ws/).*$', spa),
]
