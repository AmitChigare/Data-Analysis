from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("home/", views.home, name="home"),
    path("line_graph_method/", views.line_graph_method, name="line_graph_method"),
    path("stacked_bar_method/", views.stacked_bar_method, name="stacked_bar_method"),
    path(
        "files/<str:month1>/<str:month2>/<str:field>/<str:field2>/",
        views.display_files,
        name="display_files",
    ),
    path(
        "lines/<str:month1>/<str:month2>/<str:field2>/",
        views.line_graph,
        name="line_graph",
    ),
]
