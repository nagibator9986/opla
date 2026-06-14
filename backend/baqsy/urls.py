from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/dashboard/", include("apps.dashboard.urls")),
    path("admin/", admin.site.urls),
    path("health/", health, name="health"),
    path("api/v1/", include("apps.core.api_urls")),
    # CKEditor 5 — загрузка картинок/ассетов из rich-редактора (staff-only).
    path("ckeditor5/", include("django_ckeditor_5.urls")),
]
