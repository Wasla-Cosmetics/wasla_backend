from django.contrib import admin
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

admin.site.site_header = _("Wasla Admin")
admin.site.site_title = _("Wasla Admin Portal")
admin.site.index_title = _("Welcome to Wasla Admin Portal")


def health_check(request):
    return HttpResponse("OK")


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/auth/", include("apps.authentication.urls")),
    path("api/store/", include("apps.store.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
