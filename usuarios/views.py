from django.shortcuts import render, redirect
from .models import Usuario, RecuperacionPassword, Paciente
from django.contrib import messages
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from .models import Usuario, RecuperacionPassword, Paciente, PlanCuidado
import random
from django.contrib.auth.hashers import make_password, check_password

# ── LOGIN ──────────────────────────────────────────────────────────────────────
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

# ── DASHBOARD FAMILIAR ─────────────────────────────────────────────────────────
def dashboard_familiar(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
    if request.session.get('usuario_rol') != 2:
        return redirect('dashboard')

    usuario_id = request.session.get('usuario_id')
    nombre = request.session.get('usuario_nombre', 'Usuario')

    # Obtener pacientes activos que tenga asignados como familiar
    # Por ahora mostramos todos los pacientes activos del sistema
    # (cuando se implemente la relación familiar-paciente se filtrará)
    pacientes = Paciente.objects.filter(estado=True)

    # Tomar el primer paciente para mostrar en el panel principal
    paciente_principal = pacientes.first()

    # Planes activos asociados
    planes_activos = PlanCuidado.objects.filter(
        id_paciente__estado=True,
        estado=True
    ).select_related('id_paciente')

    context = {
        'nombre': nombre,
        'pacientes': pacientes,
        'paciente_principal': paciente_principal,
        'planes_activos': planes_activos,
        'total_pacientes': pacientes.count(),
        'total_planes': planes_activos.count(),
    }
    return render(request, 'dashboard_familiar.html', context)


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

            texto_html = f'''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background:#f5f7fb;padding:40px 0;">
        <tr>
            <td align="center">
                <table width="500" cellpadding="0" cellspacing="0" style="background:white;border-radius:16px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.08);">
                    <tr>
                        <td style="background:linear-gradient(135deg,#7ab6e8,#f39ab0);padding:35px;text-align:center;">
                            <h1 style="color:white;margin:0;font-size:26px;">❤ CuidarTech</h1>
                            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;font-size:14px;">Sistema de gestión de cuidados</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:40px 35px;">
                            <p style="color:#333;font-size:16px;margin:0 0 10px 0;">Hola, <strong>{usuario.nombre}</strong></p>
                            <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 25px 0;">
                                Recibimos una solicitud para restablecer la contraseña de tu cuenta en CuidarTech. Usa el siguiente código para continuar:
                            </p>
                            <div style="background:#f5f7fb;border-radius:12px;padding:25px;text-align:center;margin:0 0 25px 0;">
                                <p style="color:#888;font-size:13px;margin:0 0 10px 0;text-transform:uppercase;letter-spacing:1px;">Tu código de verificación</p>
                                <span style="font-size:42px;font-weight:bold;letter-spacing:10px;color:#333;">{codigo}</span>
                                <p style="color:#e74c3c;font-size:13px;margin:15px 0 0 0;">⏱ Este código expira en <strong>10 minutos</strong></p>
                            </div>
                            <p style="color:#888;font-size:13px;line-height:1.6;margin:0;">
                                Si no solicitaste este cambio puedes ignorar este mensaje. Tu cuenta permanece segura.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background:#f9f9f9;padding:20px 35px;border-top:1px solid #eee;text-align:center;">
                            <p style="color:#aaa;font-size:12px;margin:0;">© 2026 CuidarTech · Este es un correo automático, por favor no respondas.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''

            from django.core.mail import EmailMessage
            msg = EmailMessage(
                subject='Código de recuperación - CuidarTech',
                body=texto_html,
                from_email=None,
                to=[correo]
            )
            msg.content_subtype = "html"
            msg.send()

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
            usuario.password = make_password(nueva_password)
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
    id_rol = request.session.get('usuario_rol')

    if id_rol == 1:
        return render(request, 'dashboard_cuidador.html', {'nombre': nombre})
    elif id_rol == 2:
        return redirect('dashboard_familiar')
    else:
        return render(request, 'dashboard_cuidador.html', {'nombre': nombre})

# ── REGISTRO ───────────────────────────────────────────────────────────────────
def registro(request):

    if request.method == "POST":

        nombre = request.POST.get('nombre', '').strip()
        correo = request.POST.get('correo', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        password = request.POST.get('password', '')
        confirmar_password = request.POST.get('confirmar_password', '')
        id_rol = request.POST.get('id_rol')

        # Validaciones
        if not nombre or not correo or not password or not id_rol:
            return render(request, 'registro.html', {
                'error': 'Todos los campos obligatorios deben completarse.'
            })

        if password != confirmar_password:
            return render(request, 'registro.html', {
                'error': 'Las contraseñas no coinciden.'
            })

        if len(password) < 6:
            return render(request, 'registro.html', {
                'error': 'La contraseña debe tener al menos 6 caracteres.'
            })

        if Usuario.objects.filter(correo=correo).exists():
            return render(request, 'registro.html', {
                'error': 'Ya existe una cuenta con ese correo.'
            })

        # Crear usuario
        Usuario.objects.create(
            nombre=nombre,
            correo=correo,
            telefono=telefono,
            password=make_password(password),
            id_rol=id_rol
        )

        messages.success(request, 'Cuenta creada correctamente. Ya puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'registro.html')

# ── DECORADOR: solo cuidadores ─────────────────────────────────────────────────
def solo_cuidador(view_func):
    def wrapper(request, *args, **kwargs):
        if 'usuario_id' not in request.session:
            return redirect('login')
        if request.session.get('usuario_rol') != 1:
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── LISTA PACIENTES ────────────────────────────────────────────────────────────
@solo_cuidador
def lista_pacientes(request):
    usuario_id = request.session.get('usuario_id')
    pacientes = Paciente.objects.filter(id_cuidador_id=usuario_id)
    return render(request, 'pacientes/lista_pacientes.html', {
        'pacientes': pacientes
    })


# ── AGREGAR PACIENTE ───────────────────────────────────────────────────────────
@solo_cuidador
def agregar_paciente(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        fecha_nacimiento = request.POST.get('fecha_nacimiento')
        diagnostico = request.POST.get('diagnostico', '').strip()
        usuario_id = request.session.get('usuario_id')

        if not nombre or not fecha_nacimiento:
            return render(request, 'pacientes/agregar_paciente.html', {
                'error': 'Nombre y fecha de nacimiento son obligatorios.'
            })

        Paciente.objects.create(
            nombre=nombre,
            fecha_nacimiento=fecha_nacimiento,
            diagnostico=diagnostico,
            estado=True,
            id_cuidador_id=usuario_id
        )

        messages.success(request, 'Paciente registrado correctamente.')
        return redirect('lista_pacientes')

    return render(request, 'pacientes/agregar_paciente.html')


# ── DETALLE PACIENTE ───────────────────────────────────────────────────────────
@solo_cuidador
def detalle_paciente(request, id_paciente):
    try:
        paciente = Paciente.objects.get(
            id_paciente=id_paciente,
            id_cuidador_id=request.session.get('usuario_id')
        )
    except Paciente.DoesNotExist:
        return redirect('lista_pacientes')

    return render(request, 'pacientes/detalle_paciente.html', {
        'paciente': paciente
    })


# ── EDITAR PACIENTE ────────────────────────────────────────────────────────────
@solo_cuidador
def editar_paciente(request, id_paciente):
    try:
        paciente = Paciente.objects.get(
            id_paciente=id_paciente,
            id_cuidador_id=request.session.get('usuario_id')
        )
    except Paciente.DoesNotExist:
        return redirect('lista_pacientes')

    if request.method == 'POST':
        paciente.nombre = request.POST.get('nombre', '').strip()
        paciente.fecha_nacimiento = request.POST.get('fecha_nacimiento')
        paciente.diagnostico = request.POST.get('diagnostico', '').strip()

        if not paciente.nombre or not paciente.fecha_nacimiento:
            return render(request, 'pacientes/editar_paciente.html', {
                'paciente': paciente,
                'error': 'Nombre y fecha de nacimiento son obligatorios.'
            })

        paciente.save()
        messages.success(request, 'Paciente actualizado correctamente.')
        return redirect('lista_pacientes')

    return render(request, 'pacientes/editar_paciente.html', {
        'paciente': paciente
    })


# ── DESACTIVAR PACIENTE ────────────────────────────────────────────────────────
@solo_cuidador
def desactivar_paciente(request, id_paciente):
    try:
        paciente = Paciente.objects.get(
            id_paciente=id_paciente,
            id_cuidador_id=request.session.get('usuario_id')
        )
        paciente.estado = False
        paciente.save()
        messages.success(request, f'Paciente {paciente.nombre} desactivado.')
    except Paciente.DoesNotExist:
        pass

    return redirect('lista_pacientes')

# ── PLANES DE CUIDADO ──────────────────────────────────────────────────────────

# ── LISTA PLANES ───────────────────────────────────────────────────────────────
@solo_cuidador
def lista_planes(request):
    usuario_id = request.session.get('usuario_id')
    pacientes = Paciente.objects.filter(id_cuidador_id=usuario_id, estado=True)
    planes = PlanCuidado.objects.filter(id_paciente__id_cuidador_id=usuario_id)
    return render(request, 'planes/lista_planes.html', {
        'planes': planes,
        'pacientes': pacientes
    })


# ── CREAR PLAN ─────────────────────────────────────────────────────────────────
@solo_cuidador
def crear_plan(request):
    usuario_id = request.session.get('usuario_id')
    pacientes = Paciente.objects.filter(id_cuidador_id=usuario_id, estado=True)

    if request.method == 'POST':
        id_paciente = request.POST.get('id_paciente')
        descripcion = request.POST.get('descripcion', '').strip()

        if not id_paciente or not descripcion:
            return render(request, 'planes/crear_plan.html', {
                'pacientes': pacientes,
                'error': 'Todos los campos son obligatorios.'
            })

        PlanCuidado.objects.create(
            id_paciente_id=id_paciente,
            descripcion=descripcion,
            estado=True
        )

        messages.success(request, 'Plan de cuidado creado correctamente.')
        return redirect('lista_planes')

    return render(request, 'planes/crear_plan.html', {
        'pacientes': pacientes
    })


# ── DETALLE PLAN ───────────────────────────────────────────────────────────────
@solo_cuidador
def detalle_plan(request, id_plan):
    try:
        plan = PlanCuidado.objects.get(
            id_plan=id_plan,
            id_paciente__id_cuidador_id=request.session.get('usuario_id')
        )
    except PlanCuidado.DoesNotExist:
        return redirect('lista_planes')

    return render(request, 'planes/detalle_plan.html', {
        'plan': plan
    })


# ── EDITAR PLAN ────────────────────────────────────────────────────────────────
@solo_cuidador
def editar_plan(request, id_plan):
    try:
        plan = PlanCuidado.objects.get(
            id_plan=id_plan,
            id_paciente__id_cuidador_id=request.session.get('usuario_id')
        )
    except PlanCuidado.DoesNotExist:
        return redirect('lista_planes')

    usuario_id = request.session.get('usuario_id')
    pacientes = Paciente.objects.filter(id_cuidador_id=usuario_id, estado=True)

    if request.method == 'POST':
        descripcion = request.POST.get('descripcion', '').strip()

        if not descripcion:
            return render(request, 'planes/editar_plan.html', {
                'plan': plan,
                'pacientes': pacientes,
                'error': 'La descripción es obligatoria.'
            })

        plan.descripcion = descripcion
        plan.save()

        messages.success(request, 'Plan actualizado correctamente.')
        return redirect('lista_planes')

    return render(request, 'planes/editar_plan.html', {
        'plan': plan,
        'pacientes': pacientes
    })


# ── DESACTIVAR PLAN ────────────────────────────────────────────────────────────
@solo_cuidador
def desactivar_plan(request, id_plan):
    try:
        plan = PlanCuidado.objects.get(
            id_plan=id_plan,
            id_paciente__id_cuidador_id=request.session.get('usuario_id')
        )
        plan.estado = False
        plan.save()
        messages.success(request, 'Plan desactivado correctamente.')
    except PlanCuidado.DoesNotExist:
        pass

    return redirect('lista_planes')

# ── Home────────────────────────────────────────────────────────────
def home(request):
    return render(request, 'home.html')

# LISTAR ACTIVIDADES
def lista_actividades(request):
    actividades = ActividadCuidado.objects.all()
    return render(request, 'actividades/lista_actividades.html', {
        'actividades': actividades
    })


# CREAR ACTIVIDAD
def crear_actividad(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')

        if not nombre:
            return render(request, 'actividades/crear_actividad.html', {
                'error': 'El nombre es obligatorio'
            })

        ActividadCuidado.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            estado=True
        )

        messages.success(request, 'Actividad creada correctamente')
        return redirect('/actividades/')

    return render(request, 'actividades/crear_actividad.html')


# VER DETALLE ACTIVIDAD
def ver_actividad(request, id):
    actividad = get_object_or_404(ActividadCuidado, id=id)
    return render(request, 'actividades/ver_actividad.html', {
        'actividad': actividad
    })


# EDITAR ACTIVIDAD
def editar_actividad(request, id):
    actividad = get_object_or_404(ActividadCuidado, id=id)

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')

        if not nombre:
            return render(request, 'actividades/editar_actividad.html', {
                'actividad': actividad,
                'error': 'El nombre es obligatorio'
            })

        actividad.nombre = nombre
        actividad.descripcion = descripcion
        actividad.save()

        messages.success(request, 'Actividad actualizada correctamente')
        return redirect('/actividades/')

    return render(request, 'actividades/editar_actividad.html', {
        'actividad': actividad
    })
