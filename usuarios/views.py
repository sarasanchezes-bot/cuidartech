from django.shortcuts import render, redirect
from .models import Usuario, RecuperacionPassword
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import random


# ── LOGIN ──────────────────────────────────────────────────────────────────────
def login_view(request):

    if request.method == "POST":

        correo = request.POST.get('correo')
        password = request.POST.get('password')

        try:
            usuario = Usuario.objects.get(correo=correo, password=password)
            request.session['usuario_id'] = usuario.id_usuario
            request.session['usuario_nombre'] = usuario.nombre
            return redirect('dashboard')

        except Usuario.DoesNotExist:
            messages.error(request, "Correo o contraseña incorrectos")

    return render(request, 'login.html')


# ── RECUPERAR CONTRASEÑA ───────────────────────────────────────────────────────
def recuperar_password(request):

    if request.method == "POST":

        correo = request.POST.get("correo")

        try:
            usuario = Usuario.objects.get(correo=correo)

            codigo = str(random.randint(100000, 999999))
            fecha_expiracion = timezone.now() + timedelta(minutes=10)

            RecuperacionPassword.objects.create(
                id_usuario=usuario,
                codigo_recuperacion=codigo,
                fecha_expiracion=fecha_expiracion,
                utilizado=False
            )

            send_mail(
                'Código de recuperación - CuidarTech',
                f'Tu código de recuperación es: {codigo}\n\nEste código expira en 10 minutos.',
                None,   # usa DEFAULT_FROM_EMAIL del settings
                [correo],
                fail_silently=False
            )

            request.session['recuperacion_usuario'] = usuario.id_usuario
            return redirect('verificar_codigo')

        except Usuario.DoesNotExist:
            return render(request, 'recuperar_password.html', {
                'error': 'No existe ninguna cuenta con ese correo.'
            })

    return render(request, 'recuperar_password.html')


# ── VERIFICAR CÓDIGO ───────────────────────────────────────────────────────────
def verificar_codigo(request):

    if request.method == "POST":

        codigo = request.POST.get('codigo', '').strip()
        usuario_id = request.session.get('recuperacion_usuario')

        if not usuario_id:
            return redirect('recuperar_password')

        try:
            recuperacion = RecuperacionPassword.objects.get(
                id_usuario_id=usuario_id,
                codigo_recuperacion=codigo,
                utilizado=False
            )

            from django.utils.timezone import is_naive, make_aware

            ahora = timezone.now()
            expiracion = recuperacion.fecha_expiracion
# Si la fecha guardada no tiene zona horaria, le agregamos UTC
            if is_naive(expiracion):
                 from django.utils.timezone import utc
                 expiracion = make_aware(expiracion, utc)
            
            if expiracion <= ahora:
                return render(request, 'verificar_codigo.html', {
                    'error': 'El código ha expirado. Solicita uno nuevo.'
                })

            recuperacion.utilizado = True
            recuperacion.save()

            return redirect('reset_password')

        except RecuperacionPassword.DoesNotExist:
            return render(request, 'verificar_codigo.html', {
                'error': 'Código incorrecto. Verifica e intenta de nuevo.'
            })

    return render(request, 'verificar_codigo.html')


# ── RESET CONTRASEÑA ───────────────────────────────────────────────────────────
def reset_password(request):

    usuario_id = request.session.get('recuperacion_usuario')

    if not usuario_id:
        return redirect('recuperar_password')

    if request.method == "POST":

        nueva_password = request.POST.get('nueva_password', '')
        confirmar_password = request.POST.get('confirmar_password', '')

        if nueva_password != confirmar_password:
            return render(request, 'reset_password.html', {
                'error': 'Las contraseñas no coinciden.'
            })

        if len(nueva_password) < 6:
            return render(request, 'reset_password.html', {
                'error': 'La contraseña debe tener al menos 6 caracteres.'
            })

        try:
            usuario = Usuario.objects.get(id_usuario=usuario_id)
            usuario.password = nueva_password
            usuario.save()

            # Limpiar sesión de recuperación
            del request.session['recuperacion_usuario']

            messages.success(request, 'Contraseña actualizada correctamente. Ya puedes iniciar sesión.')
            return redirect('login')

        except Usuario.DoesNotExist:
            return redirect('recuperar_password')

    return render(request, 'reset_password.html')


# ── DASHBOARD ──────────────────────────────────────────────────────────────────
def dashboard(request):

    if 'usuario_id' not in request.session:
        return redirect('login')

    nombre = request.session.get('usuario_nombre', 'Usuario')
    return render(request, 'dashboard.html', {'nombre': nombre})