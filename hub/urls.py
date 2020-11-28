from django.urls import path
from .views import MainView, CategoryView, RepositoryView, DetailView

urlpatterns = [
    path('', MainView.as_view()),
    path('categories', CategoryView.as_view()),
    path('exporter', RepositoryView.as_view()),
    path('exporters/<int:exporter_id>', DetailView.as_view()),
]
