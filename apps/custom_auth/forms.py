from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Field, Column, Row, Layout
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.urls import reverse


class UsuarioCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'usuario-form'
        self.helper.form_method = 'post'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False
        self.helper.form_show_labels = True

        # Customización de Placeholders y Clases de Tailwind / DaisyUI
        self.fields['username'].widget.attrs.update({
            'placeholder': 'ej. jdoe',
            'class': 'input input-xs border-base-300 focus:border-primary w-full h-8 text-xs',
            'autocomplete': 'username',
        })
        self.fields['username'].label = "Nombre de usuario"
        self.fields['username'].help_text = None  # Se remueve el texto largo por defecto para limpiar la UI

        self.fields['password1'].widget.attrs.update({
            'placeholder': '••••••••',
            'class': 'input input-xs border-base-300 focus:border-primary w-full h-8 text-xs pr-8',
            'autocomplete': 'new-password',
        })
        self.fields['password1'].label = "Contraseña"
        self.fields['password1'].help_text = None

        self.fields['password2'].widget.attrs.update({
            'placeholder': '••••••••',
            'class': 'input input-xs border-base-300 focus:border-primary w-full h-8 text-xs',
            'autocomplete': 'new-password',
        })
        self.fields['password2'].label = "Confirmar contraseña"
        self.fields['password2'].help_text = None

        # Estructura del Layout con Crispy Forms
        self.helper.layout = Layout(
            # Campo Username
            Row(
                Column(
                    Field('username', css_class='w-full'),
                    css_class='col-span-12'
                ),
                css_class='grid grid-cols-12 gap-3 mb-3'
            ),

            # Fila con las dos contraseñas lado a lado (2 columnas en sm+)
            Row(
                Column(
                    Field('password1', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-6'
                ),
                Column(
                    Field('password2', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-6'
                ),
                css_class='grid grid-cols-12 gap-3 mb-3'
            ),

            # Requisitos de contraseña compactos en badge/pills
            HTML("""
                <div class="p-2.5 rounded-lg bg-base-200/50 border border-base-200 text-[11px] text-base-content/70 space-y-1 mb-4">
                    <span class="font-bold text-base-content/80 block uppercase tracking-wider text-[10px]">Requisitos de contraseña:</span>
                    <ul class="grid grid-cols-1 sm:grid-cols-2 gap-x-2 gap-y-0.5 list-disc list-inside text-base-content/60">
                        <li>Mínimo 8 caracteres</li>
                        <li>No ser similar a tu información personal</li>
                        <li>No ser una contraseña común</li>
                        <li>No ser enteramente numérica</li>
                    </ul>
                </div>
            """),
        )


class UsuarioChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'usuario-form'
        self.helper.form_method = 'post'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False

        input_classes = 'input input-xs border-base-300 focus:border-primary w-full h-8 text-xs'

        self.fields['username'].widget.attrs.update({'class': input_classes})
        self.fields['first_name'].widget.attrs.update({'class': input_classes, 'placeholder': 'Nombre(s)'})
        self.fields['last_name'].widget.attrs.update({'class': input_classes, 'placeholder': 'Apellidos'})
        self.fields['email'].widget.attrs.update({'class': input_classes, 'placeholder': 'correo@empresa.com'})

        # Clases para los campos de fecha y tiempo
        self.fields['date_joined'].widget.attrs.update({'class': input_classes})
        self.fields['last_login'].widget.attrs.update({'class': input_classes})

        self.fields['password'].widget = forms.HiddenInput()

        # Asignar IDs para fácil enganche con el script Dual Listbox
        self.fields['groups'].widget.attrs.update({
            'id': 'id_groups_dual',
            'class': 'w-full text-xs'
        })
        self.fields['user_permissions'].widget.attrs.update({
            'id': 'id_permissions_dual',
            'class': 'w-full text-xs'
        })

        password_url = reverse(
            'admin:password_change') if not self.instance.pk else f"/admin/auth/user/{self.instance.pk}/password/"

        self.helper.layout = Layout(

            # --- SECCIÓN 1: DATOS PERSONALES Y CREDENCIALES ---
            Row(
                Column(
                    Field('username', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-4'
                ),
                Column(
                    Field('first_name', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-4'
                ),
                Column(
                    Field('last_name', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-4'
                ),
                css_class='grid grid-cols-12 gap-3 mb-3'
            ),

            Row(
                Column(
                    Field('email', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-8'
                ),
                Column(
                    HTML(f"""
                        <div class="form-control">
                            <label class="label p-0 mb-1">
                                <span class="label-text text-xs font-semibold text-base-content/80">Seguridad</span>
                            </label>
                            <a href="{password_url}" 
                               class="btn btn-outline btn-xs h-8 min-h-0 w-full justify-between font-normal text-xs border-base-300 hover:bg-base-200 hover:text-base-content">
                                <span class="flex items-center gap-1.5">
                                    <span class="icon-[tabler--key] text-primary text-sm"></span>
                                    <span>Cambiar Contraseña</span>
                                </span>
                                <span class="icon-[tabler--chevron-right] text-xs opacity-50"></span>
                            </a>
                        </div>
                    """),
                    css_class='col-span-12 sm:col-span-4'
                ),
                css_class='grid grid-cols-12 gap-3 mb-4'
            ),

            # --- SECCIÓN 2: AUDITORÍA Y FECHAS DE ACCESO ---
            HTML("""
                <div class="text-[11px] font-bold text-primary uppercase tracking-wider border-b border-base-200 pb-1 mb-3 flex items-center gap-1">
                    <span class="icon-[tabler--calendar-time] size-3.5"></span>
                    <span>Registro y Actividad</span>
                </div>
            """),

            Row(
                Column(
                    Field('date_joined', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-6'
                ),
                Column(
                    Field('last_login', css_class='w-full'),
                    css_class='col-span-12 sm:col-span-6'
                ),
                css_class='grid grid-cols-12 gap-3 mb-4'
            ),

            # --- SECCIÓN 3: ESTADO DEL USUARIO Y FLAGS ---
            HTML("""
                <div class="text-[11px] font-bold text-primary uppercase tracking-wider border-b border-base-200 pb-1 mb-3 flex items-center gap-1">
                    <span class="icon-[tabler--shield-check] size-3.5"></span>
                    <span>Estado y Permisos de Acceso</span>
                </div>
            """),

            Row(
                Column(
                    Field('is_active', css_class='checkbox checkbox-xs checkbox-primary mr-1.5'),
                    css_class='col-span-12 sm:col-span-4 flex items-center'
                ),
                Column(
                    Field('is_staff', css_class='checkbox checkbox-xs checkbox-primary mr-1.5'),
                    css_class='col-span-12 sm:col-span-4 flex items-center'
                ),
                Column(
                    Field('is_superuser', css_class='checkbox checkbox-xs checkbox-primary mr-1.5'),
                    css_class='col-span-12 sm:col-span-4 flex items-center'
                ),
                css_class='grid grid-cols-12 gap-3 p-3 rounded-lg bg-base-200/40 border border-base-200 mb-4'
            ),

            # --- SECCIÓN 4: GRUPOS Y PERMISOS INDIVIDUALES (DUAL LISTBOX) ---
            Row(
                Column(
                    Field('groups', css_class='w-full'),
                    css_class='col-span-12 mb-4'
                ),
                Column(
                    Field('user_permissions', css_class='w-full'),
                    css_class='col-span-12 mb-4'
                ),
                css_class='grid grid-cols-12 gap-3'
            ),
        )
