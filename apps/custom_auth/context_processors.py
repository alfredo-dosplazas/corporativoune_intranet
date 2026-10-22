from django.contrib.auth import get_user_model

User = get_user_model()

def impersonation_status(request):
    admin_id = request.session.get('impersonator_id')
    is_impersonating = admin_id is not None

    admin_user = None
    if is_impersonating:
        # Opcional: Obtener el objeto del admin para mostrar su nombre si lo deseas
        admin_user = User.objects.filter(pk=admin_id).first()

    return {
        'is_impersonating': is_impersonating,
        'impersonator_user': admin_user,
    }