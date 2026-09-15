from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('staff/invite/', views.staff_invite, name='staff_invite'),
    path('staff/invitations/', views.staff_invitations, name='staff_invitations'),
    path('staff/onboard/<str:token>/', views.staff_onboard, name='staff_onboard'),
    path('staff/<int:user_id>/roles/', views.staff_roles_manage, name='staff_roles_manage'),
    path('staff/roles/<int:pk>/remove/', views.staff_role_remove, name='staff_role_remove'),
]
