from django.contrib import admin
from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve
from loans import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/chat/", views.chat),
    path("api/ocr/upload/", views.ocr_upload),
    re_path(r"^media/(?P<path>.*)$", views.protected_media),
]
