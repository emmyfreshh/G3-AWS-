from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add_pressure_data/', views.add_pressure_data, name='add_pressure_data'),
    path('pressure-data/', views.pressure_data, name='pressure_data'),
    path('live-graph-json/', views.live_graph_json, name='live_graph_json'),
    path('comments/', views.comments, name='comments'),
    path('notifications/', views.notifications, name='notifications'),
    path('live-map/', views.live_map, name='live_map'),
    path('api/live-grid/', views.live_grid_json, name='live_grid_json'),
]