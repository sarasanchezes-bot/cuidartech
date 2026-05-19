from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore
from django.utils import timezone
from datetime import datetime, timedelta

def verificar_actividades():
    from .models import ActividadCuidado, RegistroDiario, Notificacion
    
    ahora = timezone.now()
    hoy = ahora.date()
    hora_actual = ahora.time()
    
    # Buscar actividades cuya hora programada ya pasó hoy
    # y que no tienen registro diario
    actividades = ActividadCuidado.objects.filter(
        id_plan__estado=True,
        id_plan__id_paciente__estado=True,
    ).select_related('id_plan__id_paciente__id_cuidador')

    for actividad in actividades:
        # Verificar si ya fue registrada hoy
        ya_registrada = RegistroDiario.objects.filter(
            id_actividad=actividad,
            fecha=hoy
        ).exists()

        if not ya_registrada and actividad.hora_programada < hora_actual:
            cuidador = actividad.id_plan.id_paciente.id_cuidador
            mensaje = f"La actividad '{actividad.nombre_actividad}' del paciente {actividad.id_plan.id_paciente.nombre} no ha sido registrada."
            
            # Evitar duplicar notificaciones
            ya_notificado = Notificacion.objects.filter(
                id_usuario=cuidador,
                mensaje=mensaje,
                fecha_envio__date=hoy
            ).exists()

            if not ya_notificado:
                Notificacion.objects.create(
                    id_usuario=cuidador,
                    mensaje=mensaje,
                    estado='no_leida'
        )
    
    # Enviar correo al cuidador
            from django.core.mail import send_mail
            send_mail(
                subject='Actividad pendiente - CuidarTech',
                message=f"Hola {cuidador.nombre},\n\n{mensaje}\n\nIngresa al sistema para registrarla.\n\nEquipo CuidarTech",
                from_email=None,
                recipient_list=[cuidador.correo],
                fail_silently=True,
        )

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
    scheduler.start()