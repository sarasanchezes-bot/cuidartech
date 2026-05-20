from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
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

    # Planes de cuidado
    path('planes/', views.lista_planes, name='lista_planes'),
    path('planes/crear/', views.crear_plan, name='crear_plan'),
    path('planes/<int:id_plan>/', views.detalle_plan, name='detalle_plan'),
    path('planes/<int:id_plan>/editar/', views.editar_plan, name='editar_plan'),
    path('planes/<int:id_plan>/desactivar/', views.desactivar_plan, name='desactivar_plan'),

    # Dashboard familiar
    path('dashboard/familiar/', views.dashboard_familiar, name='dashboard_familiar'),

    # Home
    path('home/', views.home, name='home_alt'),

    # Actividades
    path('actividades/', views.lista_actividades, name='lista_actividades'),
    path('actividades/crear/', views.crear_actividad, name='crear_actividad'),
    path('actividades/<int:id_actividad>/', views.ver_actividad, name='ver_actividad'),
    path('actividades/<int:id_actividad>/editar/', views.editar_actividad, name='editar_actividad'),
    path('actividades/<int:id_actividad>/eliminar/', views.eliminar_actividad, name='eliminar_actividad'),

    # Registro Diario
    path('registros/hoy/', views.registros_hoy, name='registros_hoy'),
    path('registros/<int:id_actividad>/registrar/', views.registrar_actividad, name='registrar_actividad'),
    path('registros/historial/', views.historial_registros, name='historial_registros'),
    path('registros/<int:id_registro>/', views.detalle_registro, name='detalle_registro'),

    #Cerrar sesión
    path('logout/', views.logout_view, name='logout'),

    #Perfil
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    #notificaciones
    path('notificaciones/', views.lista_notificaciones, name='lista_notificaciones'),
    path('notificaciones/<int:id_notificacion>/marcar-leida/', views.marcar_leida, name='marcar_leida'),

    #vista para que el cuidador pueda asignar familiares a sus pacientes
    path('pacientes/<int:id_paciente>/familiares/', views.gestionar_familiares, name='gestionar_familiares'),
    path('pacientes/<int:id_paciente>/familiares/quitar/<int:id_familiar>/', views.quitar_familiar, name='quitar_familiar'),
    path('planes/<int:id_plan>/historial/', views.historial_plan, name='historial_plan'),
]