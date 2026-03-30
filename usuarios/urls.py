from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro, name='registro'),
    path('recuperar-password/', views.recuperar_password, name='recuperar_password'),
    path('verificar-codigo/', views.verificar_codigo, name='verificar_codigo'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Pacientes
    path('pacientes/', views.lista_pacientes, name='lista_pacientes'),
    path('pacientes/agregar/', views.agregar_paciente, name='agregar_paciente'),
    path('pacientes/<int:id_paciente>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:id_paciente>/editar/', views.editar_paciente, name='editar_paciente'),
    path('pacientes/<int:id_paciente>/desactivar/', views.desactivar_paciente, name='desactivar_paciente'),
]