# ── IMPORTS ────────────────────────────────────────────────────────────────
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.core.mail import EmailMessage
from django.contrib.auth.hashers import make_password, check_password

from datetime import timedelta
import random

from .models import (
    Usuario,
    RecuperacionPassword,
    Paciente,
    PlanCuidado,
    ActividadCuidado
)

from functools import wraps


# ── DECORADORES ─────────────────────────────────────────────────────────────
def solo_cuidador(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login')
        if request.session.get('usuario_rol') != 1:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── AUTH (LOGIN / REGISTRO / DASHBOARD) ─────────────────────────────────────
def login_view(request):
    if request.method == "POST":
        correo = request.POST.get('correo')
        password = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(correo=correo)

            if check_password(password, usuario.password):
                request.session['usuario_id'] = usuario.id_usuario
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_rol'] = usuario.id_rol
                return redirect('dashboard')
            else:
                messages.error(request, "Correo o contraseña incorrectos")

        except Usuario.DoesNotExist:
            messages.error(request, "Correo o contraseña incorrectos")

    return render(request, 'login.html')


def dashboard(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    nombre = request.session.get('usuario_nombre')
    rol = request.session.get('usuario_rol')

    if rol == 1:
        return render(request, 'dashboard_cuidador.html', {'nombre': nombre})
    elif rol == 2:
        return redirect('dashboard_familiar')

    return render(request, 'dashboard_cuidador.html', {'nombre': nombre})


def registro(request):
    if request.method == "POST":
        nombre = request.POST.get('nombre', '').strip()
        correo = request.POST.get('correo', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        password = request.POST.get('password')
        confirmar = request.POST.get('confirmar_password')
        rol = request.POST.get('id_rol')

        if not nombre or not correo or not password or not rol:
            return render(request, 'registro.html', {'error': 'Campos obligatorios'})

        if password != confirmar:
            return render(request, 'registro.html', {'error': 'Las contraseñas no coinciden'})

        if len(password) < 6:
            return render(request, 'registro.html', {'error': 'Mínimo 6 caracteres'})

        if Usuario.objects.filter(correo=correo).exists():
            return render(request, 'registro.html', {'error': 'Correo ya registrado'})

        Usuario.objects.create(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            password=make_password(password),
            id_rol=rol
        )

        messages.success(request, 'Cuenta creada')
        return redirect('login')

    return render(request, 'registro.html')


# ── DASHBOARD FAMILIAR ──────────────────────────────────────────────────────
def dashboard_familiar(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.session.get('usuario_rol') != 2:
        return redirect('dashboard')

    pacientes = Paciente.objects.filter(estado=True)
    planes = PlanCuidado.objects.filter(estado=True)

    return render(request, 'dashboard_familiar.html', {
        'nombre': request.session.get('usuario_nombre'),
        'pacientes': pacientes,
        'planes_activos': planes
    })


# ── RECUPERACIÓN DE CONTRASEÑA ──────────────────────────────────────────────
def recuperar_password(request):
    if request.method == "POST":
        correo = request.POST.get("correo")

        try:
            usuario = Usuario.objects.get(correo=correo)

            codigo = str(random.randint(100000, 999999))

            RecuperacionPassword.objects.create(
                id_usuario=usuario,
                codigo_recuperacion=codigo,
                fecha_expiracion=timezone.now() + timedelta(minutes=10),
                utilizado=False
            )

            msg = EmailMessage(
                subject='Código de recuperación',
                body=f"Tu código es: {codigo}",
                to=[correo]
            )
            msg.send()

            request.session['recuperacion_usuario'] = usuario.id_usuario
            return redirect('verificar_codigo')

        except Usuario.DoesNotExist:
            return render(request, 'recuperar_password.html', {
                'error': 'Correo no registrado'
            })

    return render(request, 'recuperar_password.html')


def verificar_codigo(request):
    if request.method == "POST":
        codigo = request.POST.get('codigo')
        user_id = request.session.get('recuperacion_usuario')

        try:
            rec = RecuperacionPassword.objects.get(
                id_usuario_id=user_id,
                codigo_recuperacion=codigo,
                utilizado=False
            )

            if rec.fecha_expiracion < timezone.now():
                return render(request, 'verificar_codigo.html', {'error': 'Código expirado'})

            rec.utilizado = True
            rec.save()

            return redirect('reset_password')

        except RecuperacionPassword.DoesNotExist:
            return render(request, 'verificar_codigo.html', {'error': 'Código inválido'})

    return render(request, 'verificar_codigo.html')


def reset_password(request):
    user_id = request.session.get('recuperacion_usuario')

    if request.method == "POST":
        nueva = request.POST.get('nueva_password')
        confirmar = request.POST.get('confirmar_password')

        if nueva != confirmar:
            return render(request, 'reset_password.html', {'error': 'No coinciden'})

        usuario = Usuario.objects.get(id_usuario=user_id)
        usuario.password = make_password(nueva)
        usuario.save()

        del request.session['recuperacion_usuario']
        return redirect('login')

    return render(request, 'reset_password.html')


# ── PACIENTES ───────────────────────────────────────────────────────────────
@solo_cuidador
def lista_pacientes(request):
    pacientes = Paciente.objects.filter(id_cuidador_id=request.session['usuario_id'])
    return render(request, 'pacientes/lista_pacientes.html', {'pacientes': pacientes})


@solo_cuidador
def agregar_paciente(request):
    if request.method == 'POST':
        Paciente.objects.create(
            nombre=request.POST.get('nombre'),
            fecha_nacimiento=request.POST.get('fecha_nacimiento'),
            estado=True,
            id_cuidador_id=request.session['usuario_id']
        )
        return redirect('lista_pacientes')

    return render(request, 'pacientes/agregar_paciente.html')


# ── PLANES ──────────────────────────────────────────────────────────────────
@solo_cuidador
def lista_planes(request):
    planes = PlanCuidado.objects.all()
    return render(request, 'planes/lista_planes.html', {'planes': planes})


# ── ACTIVIDADES ─────────────────────────────────────────────────────────────
def lista_actividades(request):
    actividades = ActividadCuidado.objects.all()
    return render(request, 'actividades/lista_actividades.html', {
        'actividades': actividades
    })


def ver_actividad(request, id):
    actividad = get_object_or_404(ActividadCuidado, id_actividad=id)
    return render(request, 'actividades/ver_actividad.html', {
        'actividad': actividad
    })