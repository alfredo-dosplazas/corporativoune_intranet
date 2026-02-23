import re
import socket
from datetime import datetime, time
from time import sleep
from zoneinfo import ZoneInfo

import pytz
import requests
from django.db import models
from django.db.models import ForeignKey
from django.utils import timezone

from apps.asistencias.utils import minutos_a_hora


class Politica(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyPolicy',
    )

    code = models.CharField(
        max_length=20,
        db_column='Code',
    )

    description = models.CharField(
        max_length=50,
        db_column='Description',
    )

    def __str__(self):
        return self.description

    class Meta:
        db_table = 'dbo.catPolicy'


class Reloj(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyTerminal',
    )

    terminal = models.PositiveIntegerField(
        unique=True,
        db_column='terminal',
    )

    descripcion = models.TextField(
        db_column='Descrip',
    )

    ip = models.GenericIPAddressField(
        db_column='ipdir',
    )

    puerto = models.PositiveIntegerField(
        db_column='ipidport',
    )

    # =========================================================
    # MÉTODO PRINCIPAL
    # =========================================================
    def descargar_transacciones_raw(self, start, end, max_paginas=1000):

        if str(self.puerto) == '8090':
            return self._descargar_json(start, end, max_paginas)

        elif str(self.puerto) == '9922':
            return self._descargar_tcp(start, end)

        return []

    # =========================================================
    # JSON (PUERTO 8090)
    # =========================================================
    def _descargar_json(self, start, end, max_paginas):

        todos = []
        index = 0
        length = 1000
        mexico = ZoneInfo("America/Mexico_City")

        while True:
            params = {
                "pass": "123",
                "personId": "-1",
                "startTime": start,
                "endTime": end,
                "length": length,
                "model": -1,
                "order": 1,
                "index": index,
            }

            r = requests.get(
                f'http://{self.ip}:{self.puerto}/newFindRecords',
                params=params,
                timeout=30
            )
            r.raise_for_status()

            data = r.json()
            records = data.get("data", {}).get("records", [])

            if not records:
                break

            for t in records:
                ts = datetime.fromtimestamp(
                    t.get("time", 0) / 1000,
                    tz=mexico
                )

                todos.append({
                    "terminal": self.terminal,
                    "badge": str(t.get("personId")).zfill(5),
                    "datetime": ts,
                    "source": 3,
                })

            index += 1

            if index >= max_paginas:
                break

            sleep(0.2)

        return todos

    # =========================================================
    # TCP (PUERTO 9922)
    # =========================================================
    def _descargar_tcp(self, start, end):

        mexico = ZoneInfo("America/Mexico_City")
        todos = []

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(30)

        try:
            s.connect((self.ip, int(self.puerto)))
            cmd = f'GetRecord(start_time="{start}" end_time="{end}")'
            s.sendall(cmd.encode())

            data = b""
            while True:
                chunk = s.recv(8192)
                if not chunk:
                    break
                data += chunk
            text = data.decode(errors="replace")

        except Exception as e:
            print(f"Error TCP reloj {self.terminal}:", e)
            return []

        finally:
            s.close()

        # Parsear respuesta
        for line in text.splitlines():

            if "time=" not in line:
                continue

            matches = re.findall(r'(\w+)="([^"]*)"', line)
            record = {}

            for k, v in matches:
                if k == "id":
                    k = "badge"
                if k == "time":
                    k = "timestamp"
                record[k] = v

            try:
                ts = datetime.strptime(
                    record["timestamp"],
                    "%Y-%m-%d %H:%M:%S"
                )

                if timezone.is_naive(ts):
                    ts = ts.replace(tzinfo=mexico)

            except Exception:
                continue

            todos.append({
                "terminal": self.terminal,
                "badge": str(record.get("badge")).zfill(5),
                "datetime": ts,
                "source": 3,
            })

        return todos

    # =========================================================

    def __str__(self):
        return self.descripcion

    class Meta:
        managed = False
        db_table = 'dbo.catCLOCKS'


class Clasificacion(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyClassification',
    )

    nombre = models.CharField(
        max_length=100,
        db_column='Name',
    )
    descripcion = models.TextField(
        db_column='Description',
    )

    def __str__(self):
        return self.nombre

    class Meta:
        managed = False
        db_table = 'dbo.catClassification'


class DetClasificacion(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyDetClassification',
    )

    clasificacion = models.ForeignKey(
        Clasificacion,
        on_delete=models.DO_NOTHING,
        db_column='KeyClassification',
        db_default=1
    )

    codigo = models.CharField(max_length=100, db_column='Code')
    descripcion = models.TextField(db_column='Description')

    def __str__(self):
        return f'{self.codigo} | {self.descripcion}'

    class Meta:
        managed = False
        db_table = 'dbo.detClassification'
        verbose_name_plural = 'Clasificaciones'
        verbose_name = 'Clasificacion'


class DiaFestivo(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyHoliday',
    )
    fecha = models.DateField(
        db_column='HolDate',
    )
    descripcion = models.TextField(
        db_column='Description',
    )
    esta_publicado = models.BooleanField(
        default=False,
        db_column='IsPosted',
    )
    lock_user = models.PositiveIntegerField(
        default=0,
        blank=True,
        db_column='LockUser',
    )
    lock_for_delete = models.PositiveIntegerField(
        default=0,
        blank=True,
        db_column='LockForDelete',
    )

    def __str__(self):
        return f'{self.descripcion} | {self.fecha}'

    class Meta:
        managed = False
        db_table = 'dbo.CatHolidays'
        verbose_name = 'Día Festivo'


class Empleado(models.Model):
    SEX_CHOICES = [
        ('F', 'Femenino'),
        ('M', 'Masculino'),
    ]

    STATUS_VAL_CHOICES = [
        (0, 'Inactivo'),
        (1, 'Activo'),
    ]

    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyEmployee',
    )

    number = models.CharField(
        max_length=100,
        db_column='Number',
    )

    status_val = models.PositiveIntegerField(
        db_column='StatusVal',
        choices=STATUS_VAL_CHOICES,
    )

    badge = models.CharField(
        max_length=128,
        db_column='Badge',
        unique=True,
        db_index=True,
    )

    name1 = models.CharField(
        max_length=100,
        db_column='Name1',
    )

    name2 = models.CharField(
        max_length=100,
        db_column='Name2',
    )

    last_name1 = models.CharField(
        max_length=100,
        db_column='LastName1',
    )

    last_name2 = models.CharField(
        max_length=100,
        db_column='LastName2',
    )

    sex = models.CharField(
        max_length=100,
        db_column='Sex',
        choices=SEX_CHOICES,
    )

    hire_date = models.DateField(
        db_column='HireDate',
    )

    @property
    def full_name(self):
        return " ".join([self.name1, self.name2, self.last_name1, self.last_name2])

    def __str__(self):
        return self.full_name

    class Meta:
        managed = False
        db_table = 'dbo.catEmployee'
        ordering = ['name1', 'name2', 'last_name1', 'last_name2']


class TransaccionReloj(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyTransaction',
    )

    empleado = models.ForeignKey(
        Empleado,
        to_field='badge',
        db_column='Badge',
        on_delete=models.DO_NOTHING,
        related_name='transacciones'
    )

    date = models.CharField(
        max_length=255,
        db_column='PunchDate',
    )

    time_str = models.CharField(
        max_length=255,
        db_column='PTimeStr',
    )

    terminal_id = models.ForeignKey(
        Reloj,
        on_delete=models.DO_NOTHING,
        to_field='terminal',
        db_column='TerminalID',
    )

    @property
    def fecha(self):
        fecha = self.date
        try:
            fecha = datetime.strptime(self.date, "%Y%m%d").date()
        except ValueError:
            pass
        return fecha

    @property
    def hora(self):
        hora = self.time_str
        try:
            hora = datetime.strptime(self.time_str, "%H%M%S").time()
        except ValueError:
            pass
        return hora

    @property
    def fecha_hora(self):
        fecha_hora = f"{self.fecha} {self.time_str}"
        try:
            if type(self.fecha) == datetime and type(self.hora) == datetime:
                fecha_hora = datetime.combine(self.fecha, self.hora)
        except ValueError:
            pass
        return fecha_hora

    class Meta:
        managed = False
        db_table = 'dbo.detPunchesIni'


class RegistroAsistencia(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyPunch',
    )

    transaction = models.PositiveIntegerField(
        db_column='KeyTrans',
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.DO_NOTHING,
        to_field='badge',
        db_column='Badge',
        related_name='asistencias',
        blank=True,
        null=True,
    )

    terminal = models.ForeignKey(
        Reloj,
        on_delete=models.DO_NOTHING,
        to_field='terminal',
        db_column='TerminalID',
        blank=True,
        null=True,
    )

    belong_date = models.DateField(
        db_column='BelongDate',
    )

    punch_time = models.DateTimeField(
        db_column='PunchTime'
    )

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)

        if instance.punch_time and timezone.is_aware(instance.punch_time):
            mexico = ZoneInfo("America/Mexico_City")

            # Quitar UTC mal asignado
            naive = timezone.make_naive(instance.punch_time, ZoneInfo("UTC"))

            # Marcarlo como México
            local_dt = naive.replace(tzinfo=mexico)

            # Convertirlo correctamente a UTC real
            instance.punch_time = local_dt.astimezone(ZoneInfo("UTC"))

        return instance

    @property
    def reloj(self):
        return Reloj.objects.filter(terminal=self.terminal).first()

    class Meta:
        managed = False
        db_table = 'dbo.detPunches'
        ordering = [
            '-belong_date',
            '-punch_time'
        ]


class ControlDiarioAsistencia(models.Model):
    key = models.BigAutoField(
        primary_key=True,
        db_column='KeyPunchDay',
    )

    empleado = models.ForeignKey(
        Empleado,
        on_delete=models.DO_NOTHING,
        to_field='key',
        db_column='KeyEmployee',
        related_name='control_diario_asistencias',
        blank=True,
        null=True,
    )

    record_date = models.DateField(
        db_column="RecordDate",
    )

    politica = ForeignKey(
        Politica,
        on_delete=models.DO_NOTHING,
        to_field='key',
        db_column='KeyAssgPolicy',
        blank=True,
        null=True,
    )

    first_in = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        db_column='FirstIN'
    )

    last_ot = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        db_column='LastOT'
    )

    @property
    def hora_entrada(self):
        return minutos_a_hora(self.first_in)

    @property
    def hora_salida(self):
        return minutos_a_hora(self.last_ot)

    class Meta:
        managed = False
        db_table = 'dbo.detPUNCHMaster'
        ordering = [
            '-record_date'
        ]


class ExcepcionAsistencia(models.Model):
    control_asistencia = models.ForeignKey(
        ControlDiarioAsistencia,
        on_delete=models.DO_NOTHING,
        to_field='key',
        db_column='KeyPunchDay',
        primary_key=True,
    )

    comentario = models.TextField(
        db_column='Comment'
    )

    class Meta:
        managed = False
        db_table = 'dbo.detPunchDayExcep'
