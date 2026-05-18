from django.core.management.base import BaseCommand
from django.utils import timezone
from usuarios.models import ActividadCuidado, RegistroDiario, Notificacion


class Command(BaseCommand):
    help = 'Crea notificaciones para actividades sin registro en el día'

    def handle(self, *args, **kwargs):
        hoy = timezone.localdate()

        actividades_sin_registro = ActividadCuidado.objects.filter(
            id_plan__estado=True
        ).exclude(
            registrodiario__fecha=hoy
        )

        notificaciones_creadas = 0

        for actividad in actividades_sin_registro:
            cuidador = actividad.id_plan.id_paciente.id_cuidador
            paciente = actividad.id_plan.id_paciente

            ya_notificado = Notificacion.objects.filter(
                id_usuario=cuidador,
                mensaje__contains=actividad.nombre_actividad,
                fecha_envio__date=hoy
            ).exists()

            if not ya_notificado:
                Notificacion.objects.create(
                    id_usuario=cuidador,
                    mensaje=f"La actividad '{actividad.nombre_actividad}' del paciente {paciente.nombre} no fue registrada hoy."
                )
                notificaciones_creadas += 1

        self.stdout.write(f'{notificaciones_creadas} notificaciones creadas para el {hoy}')
