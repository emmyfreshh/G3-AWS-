from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('create_user/', views.create_user, name='create_user'),
    path('user_list/', views.user_list, name='user_list'),
    path('delete_user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('reset_password/<int:user_id>/', views.reset_password, name='reset_password'),
    path('assign_clinician/<int:user_id>/', views.assign_clinician, name='assign_clinician'),
    path('upload_csv/', views.upload_csv, name='upload_csv'),
]