from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/units/', views.units_api, name='units_api'),
    path('api/tenants/', views.tenants_api, name='tenants_api'),
    path('properties/', views.properties, name='properties'),
    path('people/', views.people, name='people'),
    path('people/<int:tenant_id>/', views.person_detail, name='person_detail'),
    path('units/<int:unit_id>/', views.unit_detail, name='unit_detail'),
    path('applications/<int:application_id>/', views.application_detail, name='application_detail'),
    path('applications/<int:application_id>/update_status/', views.update_application_status, name='update_application_status'),
]