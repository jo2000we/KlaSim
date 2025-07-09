from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/context/', views.upload_context, name='upload_context'),
    path('upload/exam/', views.upload_exam, name='upload_exam'),
    path('delete/context/<int:pk>/', views.delete_context, name='delete_context'),
    path('delete/exam/<int:pk>/', views.delete_exam, name='delete_exam'),
]
