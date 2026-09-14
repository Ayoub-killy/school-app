from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/add/', views.assignment_create, name='assignment_create'),
    path('assignments/<int:pk>/edit/', views.assignment_update, name='assignment_update'),
    path('assignments/<int:pk>/delete/', views.assignment_delete, name='assignment_delete'),

    path('generate/', views.generate_timetable_view, name='generate'),
    path('view/', views.timetable_view, name='view'),
    path('view/pdf/', views.timetable_pdf, name='pdf'),
]
