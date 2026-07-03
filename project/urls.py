from django.contrib import admin
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

admin.site.site_header = "Wasla Admin"
admin.site.site_title = "Wasla Admin Portal"
admin.site.index_title = "Welcome to Wasla Admin Portal"


def health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
