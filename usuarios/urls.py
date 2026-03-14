from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro, name='registro'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('dashboard/', views.dashboard, name='dashboard'),
]