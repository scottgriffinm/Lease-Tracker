from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/units/', views.units_api, name='units_api'),
    path('people/', views.people, name='people'),
    path('people/<int:tenant_id>/', views.person_detail, name='person_detail'),
    path('units/<int:unit_id>/', views.unit_detail, name='unit_detail'),
]