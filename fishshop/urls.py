from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

# Trang ẩn - chỉ superuser mới vào được
@user_passes_test(lambda u: u.is_superuser)
def admin_history(request):
    logs = LogEntry.objects.all().order_by('-action_time')[:200]
    return render(request, 'admin/admin_history.html', {'logs': logs})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin-secret-history-x9k2/', admin_history, name='admin-history'),  # ← link ẩn
    path('', include('store.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)