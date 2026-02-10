def es_frescopack(user):
    if not hasattr(user, "contacto"):
        return False

    return (
            user.contacto.empresa
            and user.contacto.empresa.nombre_corto == "Frescopack"
    )
