import datetime
from django.db import models
from django.db.models.fields.files import ImageFieldFile


def serialize_value(value):
    # None
    if value is None:
        return None

    # Tipos simples
    if isinstance(value, (str, int, float, bool)):
        return value

    # Fechas
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()

    # Archivos / imágenes
    if isinstance(value, ImageFieldFile):
        try:
            if value:
                return value.url
            else:
                return None
        except Exception:
            return None

    # FK → solo ID
    if isinstance(value, models.Model):
        return f"({value.pk}) | {value}"

    # Último recurso
    return str(value)


def model_to_dict_simple(instance):
    data = {}

    for field in instance._meta.concrete_fields:
        field_name = field.name

        try:
            value = getattr(instance, field_name)
            data[field_name] = serialize_value(value)

        except Exception as e:
            data[field_name] = f"<<ERROR: {e}>>"

    return data
