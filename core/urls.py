from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('session-history/', views.session_history, name='session_history'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('api/save-timer-settings/', views.save_timer_settings, name='save_timer_settings'),
    path('api/save-session/', views.save_session, name='save_session'),
    path('api/get-user-stats/', views.get_user_stats, name='get_user_stats'),
    path('api/save-workspace-settings/', views.save_workspace_settings, name='save_workspace_settings'),
    path('view-pdf/', views.view_pdf, name='view_pdf'),
    path('api/upload-pdf/', views.upload_pdf, name='upload_pdf'),
    path('api/remove-pdf/', views.remove_pdf, name='remove_pdf'),
]