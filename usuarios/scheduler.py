from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from django.core.mail import EmailMessage
from datetime import datetime
import subprocess
import os
from django.conf import settings


def verificar_actividades():
    from .models import ActividadCuidado, RegistroDiario, Notificacion, FamiliarPaciente

    ahora = timezone.now()
    hoy = ahora.date()
    hora_actual = ahora.time()

    actividades = ActividadCuidado.objects.filter(
        id_plan__estado=True,
        id_plan__id_paciente__estado=True,
    ).select_related('id_plan__id_paciente__id_cuidador')

    for actividad in actividades:
        ya_registrada = RegistroDiario.objects.filter(
            id_actividad=actividad,
            fecha=hoy
        ).exists()

        if not ya_registrada and actividad.hora_programada < hora_actual:
            cuidador = actividad.id_plan.id_paciente.id_cuidador
            mensaje = f"La actividad '{actividad.nombre_actividad}' del paciente {actividad.id_plan.id_paciente.nombre} no ha sido registrada."

            ya_notificado = Notificacion.objects.filter(
                id_usuario=cuidador,
                mensaje=mensaje,
                fecha_envio__date=hoy
            ).exists()

            if not ya_notificado:
                # Notificar al cuidador en el sistema
                Notificacion.objects.create(
                    id_usuario=cuidador,
                    mensaje=mensaje,
                    estado='no_leida'
                )

                # Correoal cuidador
                correo_cuidador = EmailMessage(
                    subject='Actividad sin registrar - CuidarTech',
                    body=f'''
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
                            <h1 style="color:white;margin:0;font-size:24px;">CuidarTech</h1>
                            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;font-size:13px;">Sistema de acompañamiento y trazabilidad del cuidado</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:35px;">
                            <p style="color:#333;font-size:16px;margin:0 0 10px 0;">Hola, <strong>{cuidador.nombre}</strong></p>
                            <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 20px 0;">
                                Te informamos que la siguiente actividad aún no ha sido registrada en el sistema:
                            </p>
                            <div style="background:#fff8f0;border-left:4px solid #f39ab0;border-radius:8px;padding:20px;margin-bottom:20px;">
                                <p style="color:#333;font-size:15px;margin:0;"><strong>{actividad.nombre_actividad}</strong></p>
                                <p style="color:#777;font-size:13px;margin:8px 0 0 0;">Paciente: {actividad.id_plan.id_paciente.nombre}</p>
                                <p style="color:#777;font-size:13px;margin:4px 0 0 0;">Hora programada: {actividad.hora_programada}</p>
                            </div>
                            <p style="color:#555;font-size:14px;line-height:1.6;margin:0 0 25px 0;">
                                Por favor ingresa al sistema y registra el estado de esta actividad para mantener la trazabilidad del cuidado.
                            </p>
                            <div style="text-align:center;">
                                <a href="http://127.0.0.1:8000/registros/hoy/" style="background:linear-gradient(90deg,#7ab6e8,#f39ab0);color:white;padding:12px 30px;border-radius:10px;text-decoration:none;font-size:15px;display:inline-block;">
                                    Ir al Registro Diario
                                </a>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td style="background:#f9f9f9;padding:20px 35px;border-top:1px solid #eee;text-align:center;">
                            <p style="color:#aaa;font-size:12px;margin:0;">© 2026 CuidarTech · Este es un mensaje automático, por favor no respondas a este correo.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
''',
                    from_email=None,
                    to=[cuidador.correo]
                )
                correo_cuidador.content_subtype = 'html'
                correo_cuidador.send(fail_silently=True)

                # Notificar a los familiares asignados
                familiares = FamiliarPaciente.objects.filter(
                    id_paciente=actividad.id_plan.id_paciente
                ).select_related('id_familiar')

                for fp in familiares:
                    Notificacion.objects.create(
                        id_usuario=fp.id_familiar,
                        mensaje=mensaje,
                        estado='no_leida'
                    )

                    correo_familiar = EmailMessage(
                        subject='Actualización sobre el cuidado de tu familiar - CuidarTech',
                        body=f'''
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
                            <h1 style="color:white;margin:0;font-size:24px;">CuidarTech</h1>
                            <p style="color:rgba(255,255,255,0.85);margin:8px 0 0 0;font-size:13px;">Sistema de acompañamiento y trazabilidad del cuidado</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:35px;">
                            <p style="color:#333;font-size:16px;margin:0 0 10px 0;">Hola, <strong>{fp.id_familiar.nombre}</strong></p>
                            <p style="color:#555;font-size:15px;line-height:1.6;margin:0 0 20px 0;">
                                Te informamos que una actividad programada para <strong>{actividad.id_plan.id_paciente.nombre}</strong> aún no ha sido registrada por el cuidador:
                            </p>
                            <div style="background:#fff8f0;border-left:4px solid #f39ab0;border-radius:8px;padding:20px;margin-bottom:20px;">
                                <p style="color:#333;font-size:15px;margin:0;"><strong>{actividad.nombre_actividad}</strong></p>
                                <p style="color:#777;font-size:13px;margin:8px 0 0 0;">Hora programada: {actividad.hora_programada}</p>
                            </div>
                            <p style="color:#555;font-size:14px;line-height:1.6;margin:0;">
                                Si tienes dudas sobre el estado del cuidado, puedes comunicarte directamente con el cuidador responsable o ingresar al sistema para más información.
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background:#f9f9f9;padding:20px 35px;border-top:1px solid #eee;text-align:center;">
                            <p style="color:#aaa;font-size:12px;margin:0;">© 2026 CuidarTech · Este es un mensaje automático, por favor no respondas a este correo.</p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
''',
                        from_email=None,
                        to=[fp.id_familiar.correo]
                    )
                    correo_familiar.content_subtype = 'html'
                    correo_familiar.send(fail_silently=True)


def hacer_backup():
    fecha = datetime.now().strftime('%Y%m%d_%H%M')
    nombre_archivo = f"backup_{fecha}.sql"
    ruta = os.path.join(settings.BASE_DIR, 'backups', nombre_archivo)

    os.makedirs(os.path.join(settings.BASE_DIR, 'backups'), exist_ok=True)

    db = settings.DATABASES['default']
    comando = [
        'pg_dump',
        '-h', db['HOST'],
        '-U', db['USER'],
        '-d', db['NAME'],
        '-f', ruta
    ]

    env = os.environ.copy()
    env['PGPASSWORD'] = db['PASSWORD']

    subprocess.run(comando, env=env)
    print(f"Backup generado: {nombre_archivo}")


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    scheduler.add_job(
        verificar_actividades,
        'interval',
        minutes=30,
        id='verificar_actividades',
        replace_existing=True
    )
    scheduler.add_job(
        hacer_backup,
        'cron',
        hour=3,
        minute=0,
        id='backup_diario',
        replace_existing=True
    )
    scheduler.start()