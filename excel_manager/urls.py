from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.upload_file, name="upload_file"),
    path(
        "files/<str:month1>/<str:month2>/<str:field>/",
        views.display_files,
        name="display_files",
    ),
]
