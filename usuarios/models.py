from django.db import models


class Usuario(models.Model):

    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.CharField(max_length=150, null=True, blank=True)
    id_rol = models.IntegerField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.nombre


class RecuperacionPassword(models.Model):

    id_recuperacion = models.AutoField(primary_key=True)

    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuario',
        null=True,
        blank=True
    )

    codigo_recuperacion = models.CharField(max_length=255)
    fecha_expiracion = models.DateTimeField()
    utilizado = models.BooleanField(default=False)

    class Meta:
        db_table = 'recuperacion_contraseña'

    def __str__(self):
        return f"Recuperacion usuario {self.id_usuario_id}"

class Paciente(models.Model):

    id_paciente = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField()
    diagnostico = models.TextField(null=True, blank=True)
    estado = models.BooleanField(default=True)

    id_cuidador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_cuidador'
    )

    class Meta:
        db_table = 'pacientes'

    def __str__(self):
        return self.nombre