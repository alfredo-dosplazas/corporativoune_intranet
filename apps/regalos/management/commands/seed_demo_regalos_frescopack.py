import random
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

# Ajusta el import según el nombre real de tu app
from apps.regalos.models import CategoriaRegalo, Evento, Invitado, Regalo


CATEGORIAS_ANTIGUEDAD = [
    {"nombre": "0 - 1 Año (Nuevo Ingreso)", "color": "#3b82f6"},
    {"nombre": "1 - 3 Años", "color": "#10b981"},
    {"nombre": "3 - 5 Años", "color": "#f59e0b"},
    {"nombre": "5+ Años (Veteranos)", "color": "#8b5cf6"},
]

NOMBRES = [
    "Carlos", "María", "José", "Ana", "Luis", "Sofía", "Diego", "Valeria",
    "Miguel", "Fernanda", "Alejandro", "Camila", "Jorge", "Andrea", "Daniel", "Paola",
]

SEGUNDOS_NOMBRES = [
    None, None, "Alberto", "Guadalupe", "Enrique", "Isabel", "Eduardo", "Elena",
]

APELLIDOS_PATERNOS = [
    "Hernández", "García", "Martínez", "López", "González", "Pérez", "Rodríguez",
    "Sánchez", "Ramírez", "Flores", "Torres", "Rivera", "Gómez", "Díaz", "Reyes", "Morales",
]

APELLIDOS_MATERNOS = [
    "Cruz", "Ortiz", "Jiménez", "Mendoza", "Ruiz", "Vargas", "Castillo", "Romero",
    "Chávez", "Ramos", "Herrera", "Medina", "Aguilar", "Vázquez", "Castro", "Núñez",
]

REGALOS_BASE = [
    # (nombre, destacado)
    ("Pantalla Smart TV 55\" 4K", True),
    ("Motocicleta Urbana 150cc", True),
    ("Refrigerador Duplex Inverter", True),
    ("Laptop 15\" Core i5 / 16GB RAM", True),
    ("iPad 10ª Generación", True),
    ("Freidora de Aire Digital XL", False),
    ("Cafetera de Cápsulas / Espresso", False),
    ("Bocina Portátil Bluetooth", False),
    ("Audífonos Inalámbricos Cancelación de Ruido", False),
    ("Horno de Microondas", False),
    ("Licuadora de Alta Potencia", False),
    ("Smartwatch Deportivo", False),
    ("Kit de Herramientas Inalámbrico", False),
    ("Juego de Sartenes Antiadherentes", False),
    ("Voucher Supermercado $1,500 MXN", False),
    ("Voucher Cine y Alimentos $1,000 MXN", False),
    ("Termo Acero Inoxidable + Mochila", False),
    ("Barra de Sonido para TV", False),
]


class Command(BaseCommand):
    help = "Genera categorías por antigüedad, invitados y regalos de prueba para una demo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug",
            type=str,
            default="fiesta-fin-de-anio-frescopack-2026",
            help="Slug del evento objetivo",
        )
        parser.add_argument(
            "--invitados",
            type=int,
            default=40,
            help="Cantidad de invitados a crear (por defecto: 40)",
        )
        parser.add_argument(
            "--regalos",
            type=int,
            default=18,
            help="Cantidad de regalos a crear (por defecto: 18)",
        )
        parser.add_argument(
            "--limpiar",
            action="store_true",
            help="Elimina invitados, regalos y categorías previas del evento antes de generar",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        slug = options["slug"]
        total_invitados = options["invitados"]
        total_regalos = options["regalos"]
        limpiar = options["limpiar"]

        evento = Evento.objects.filter(slug=slug).first()
        if not evento:
            # Si no existe, lo crea como activo para facilitar la demo;
            # si prefieres que falle si no existe, reemplaza por CommandError.
            evento = Evento.objects.create(
                nombre="Fiesta de Fin de Año FrescoPack 2026",
                slug=slug,
                activo=True,
                fecha_evento=timezone.now() + timezone.timedelta(days=15),
            )
            self.stdout.write(self.style.WARNING(f"Evento no existía; se creó: {evento}"))

        if limpiar:
            Regalo.objects.filter(evento=evento).delete()
            Invitado.objects.filter(evento=evento).delete()
            CategoriaRegalo.objects.filter(evento=evento).delete()
            self.stdout.write(self.style.WARNING("Datos previos del evento eliminados."))

        # 1. Crear categorías por antigüedad
        categorias = []
        for cat_data in CATEGORIAS_ANTIGUEDAD:
            cat, _ = CategoriaRegalo.objects.get_or_create(
                evento=evento,
                nombre=cat_data["nombre"],
                defaults={"color": cat_data["color"]},
            )
            categorias.append(cat)

        # 2. Crear invitados repartidos entre categorías
        invitados_creados = 0
        intentos = 0
        max_intentos = total_invitados * 10

        while invitados_creados < total_invitados and intentos < max_intentos:
            intentos += 1
            primer_nombre = random.choice(NOMBRES)
            segundo_nombre = random.choice(SEGUNDOS_NOMBRES)
            primer_apellido = random.choice(APELLIDOS_PATERNOS)
            segundo_apellido = random.choice(APELLIDOS_MATERNOS)

            # Evita colisiones con unique_together=('evento', 'primer_nombre', 'segundo_nombre', 'primer_apellido', 'segundo_apellido')
            existe = Invitado.objects.filter(
                evento=evento,
                primer_nombre=primer_nombre,
                segundo_nombre=segundo_nombre,
                primer_apellido=primer_apellido,
                segundo_apellido=segundo_apellido,
            ).exists()
            if existe:
                continue

            # Reparto equilibrado por antigüedad
            categoria = categorias[invitados_creados % len(categorias)]

            Invitado.objects.create(
                evento=evento,
                categoria=categoria,
                primer_nombre=primer_nombre,
                segundo_nombre=segundo_nombre,
                primer_apellido=primer_apellido,
                segundo_apellido=segundo_apellido,
                asistio=False,
            )
            invitados_creados += 1

        # 3. Crear regalos con números consecutivos sin chocar con existentes
        ultimo_numero = (
            Regalo.objects.filter(evento=evento)
            .order_by("-numero")
            .values_list("numero", flat=True)
            .first()
            or 0
        )

        regalos_creados = 0
        for i in range(total_regalos):
            numero_boleto = ultimo_numero + i + 1
            base_nombre, destacado = REGALOS_BASE[i % len(REGALOS_BASE)]
            nombre_premio = (
                base_nombre
                if i < len(REGALOS_BASE)
                else f"{base_nombre} (Edición {i // len(REGALOS_BASE) + 1})"
            )
            categoria = categorias[i % len(categorias)]

            Regalo.objects.create(
                evento=evento,
                categoria=categoria,
                numero=numero_boleto,
                nombre=nombre_premio,
                destacado=destacado,
                canjeado=False,
            )
            regalos_creados += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Listo para '{evento.slug}': {len(categorias)} categorías, "
                f"{invitados_creados} invitados y {regalos_creados} regalos creados."
            )
        )