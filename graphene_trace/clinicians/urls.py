from django.urls import path
from . import views

urlpatterns = [
    path('patients/', views.patient_list, name='patient_list'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patient/<int:patient_id>/history/', views.patient_history, name='patient_history'),
    path('patient/<int:patient_id>/comments/', views.patient_comments, name='patient_comments'),
    path('api/patient/<int:patient_id>/live-grid/', views.patient_live_grid_json, name='clinician_patient_live_grid'),
]