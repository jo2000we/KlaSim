from django.urls import path
from . import views

urlpatterns = [
    path('setup/', views.setup_view, name='setup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/test_key/', views.test_api_key_view, name='test_key'),
    path('settings/', views.settings_view, name='settings'),
    path('settings/sessions/', views.sessions_view, name='sessions'),
    path('settings/sessions/cleanup/', views.cleanup_sessions_view, name='cleanup_sessions'),
    path('settings/sessions/<str:session_id>/download/', views.download_session_zip, name='download_session_zip'),
]
