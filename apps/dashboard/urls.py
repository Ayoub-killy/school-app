from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.home, name='home'),
    path('hub/academic/', views.academic_hub, name='academic_hub'),
    path('hub/library/', views.library_hub, name='library_hub'),
    path('hub/staff/', views.staff_hub, name='staff_hub'),
    path('hub/resources/', views.resources_hub, name='resources_hub'),
]