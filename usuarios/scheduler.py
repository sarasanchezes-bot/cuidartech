from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from django.core.mail import send_mail
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
                # Notificar al cuidador
                Notificacion.objects.create(
                    id_usuario=cuidador,
                    mensaje=mensaje,
                    estado='no_leida'
                )
                send_mail(
                    subject='Actividad pendiente - CuidarTech',
                    message=f"Hola {cuidador.nombre},\n\n{mensaje}\n\nIngresa al sistema para registrarla.\n\nEquipo CuidarTech",
                    from_email=None,
                    recipient_list=[cuidador.correo],
                    fail_silently=True,
                )

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
                    send_mail(
                        subject='Actividad pendiente - CuidarTech',
                        message=f"Hola {fp.id_familiar.nombre},\n\n{mensaje}\n\nComunícate con el cuidador para más información.\n\nEquipo CuidarTech",
                        from_email=None,
                        recipient_list=[fp.id_familiar.correo],
                        fail_silently=True,
                    )


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