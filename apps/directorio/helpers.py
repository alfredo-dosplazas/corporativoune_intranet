def puede_editar_contacto(user, contacto):
    if not user.contacto:
        return False

    return (
            user.has_perm("directorio.change_contacto")
            and user.contacto.sede_administrativa == contacto.sede_administrativa
    )
