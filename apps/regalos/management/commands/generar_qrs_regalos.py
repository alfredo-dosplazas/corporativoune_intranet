import os
import zipfile
from io import BytesIO
from pathlib import Path

from django.core.management.base import BaseCommand
import qrcode
from PIL import Image, ImageDraw, ImageFont

from apps.regalos.models import Regalo


class Command(BaseCommand):
    help = 'Genera tarjetas sorpresa con QR y Número de Boleto/Premio en un ZIP en la carpeta Downloads'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            default='http://192.168.1.100:8000',
            help='Dominio o IP de la red local / intranet'
        )

    def handle(self, *args, **options):
        domain = options['domain'].rstrip('/')

        # Ruta destino a Downloads del sistema
        downloads_dir = Path.home() / "Downloads"
        downloads_dir.mkdir(parents=True, exist_ok=True)

        zip_filename = downloads_dir / "etiquetas_sorpresa_navidad.zip"

        regalos = Regalo.objects.all().order_by('numero')
        if not regalos.exists():
            self.stdout.write(self.style.WARNING("No hay regalos registrados en la base de datos."))
            return

        self.stdout.write(self.style.SUCCESS(f"Generando {regalos.count()} etiquetas de sorpresa..."))

        with zipfile.ZipFile(zip_filename, 'w') as zip_file:
            for regalo in regalos:
                # 1. URL de canje
                qr_url = f"{domain}/regalos/canjear/{regalo.codigo_qr}/"

                # 2. Generar código QR
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_M,
                    box_size=8,
                    border=1,
                )
                qr.add_data(qr_url)
                qr.make(fit=True)

                # Forzamos un tamaño fijo perfecto para el QR (ej. 210x210 px)
                qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                qr_img = qr_img.resize((210, 210), Image.Resampling.LANCZOS)

                # 3. Canvas/Tarjeta (Ancho: 700px, Alto: 250px)
                card_width, card_height = 700, 250
                card = Image.new('RGB', (card_width, card_height), color='white')
                draw = ImageDraw.Draw(card)

                # Posicionar QR con margen fijo a la izquierda (X=20, Y centrado)
                qr_margin_left = 20
                qr_y = (card_height - 210) // 2
                card.paste(qr_img, (qr_margin_left, qr_y))

                # Cálculo dinámico de X para el texto (QR finaliza en X=230, texto inicia en X=260)
                text_x = qr_margin_left + 210 + 30

                # Borde alrededor de la tarjeta
                draw.rectangle([0, 0, card_width - 1, card_height - 1], outline="#cbd5e1", width=3)

                # Cargar fuentes del sistema
                try:
                    font_number = ImageFont.truetype("arialbd.ttf", 52)  # Arial Bold
                    font_title = ImageFont.truetype("arial.ttf", 20)
                    font_subtitle = ImageFont.truetype("arial.ttf", 15)
                except IOError:
                    try:
                        font_number = ImageFont.truetype("arial.ttf", 48)
                        font_title = ImageFont.truetype("arial.ttf", 20)
                        font_subtitle = ImageFont.truetype("arial.ttf", 15)
                    except IOError:
                        font_number = ImageFont.load_default()
                        font_title = ImageFont.load_default()
                        font_subtitle = ImageFont.load_default()

                # 4. Dibujar información visible con X dinámica
                # Encabezado
                draw.text((text_x, 30), "GRAN RIFA NAVIDEÑA", fill="#dc2626", font=font_title)

                # Número de Boleto / Premio
                draw.text((text_x, 70), f"BOLETO #{regalo.numero:03d}", fill="#0f172a", font=font_number)

                # Indicación para el usuario
                draw.text((text_x, 155), "🎁 Premio Sorpresa", fill="#475569", font=font_title)
                draw.text((text_x, 190), "Escanea el código QR para revelar en pantalla", fill="#16a34a",
                          font=font_subtitle)

                # 5. Guardar en memoria e insertar en el ZIP
                img_buffer = BytesIO()
                card.save(img_buffer, format='PNG')

                filename_in_zip = f"boleto_{regalo.numero:03d}.png"
                zip_file.writestr(filename_in_zip, img_buffer.getvalue())

        self.stdout.write(
            self.style.SUCCESS(f"¡Éxito! Archivo ZIP guardado correctamente en:\n{zip_filename}")
        )