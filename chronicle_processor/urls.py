from django.urls import path
from . import views

urlpatterns = [
    path('process-chronicle-research', views.process_chronicle_research, name='process_chronicle_research'),
]

