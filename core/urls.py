from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('api/save-timer-settings/', views.save_timer_settings, name='save_timer_settings'),
    path('api/save-session/', views.save_session, name='save_session'),
    path('api/get-user-stats/', views.get_user_stats, name='get_user_stats'),
]