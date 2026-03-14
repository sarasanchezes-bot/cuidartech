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
        db_column='id_usuario'
    )

    codigo_recuperacion = models.CharField(max_length=255)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    utilizado = models.BooleanField(default=False)

    class Meta:
        db_table = 'recuperacion_contraseña'

    def __str__(self):
        return f"Recuperacion usuario {self.id_usuario_id}"