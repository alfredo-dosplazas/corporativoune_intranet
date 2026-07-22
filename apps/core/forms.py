from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Field, Layout, HTML
from django import forms
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Usuario o Correo Electrónico",
        widget=forms.TextInput(attrs={
            'placeholder': 'ej. usuario@empresa.com',
            'autofocus': True,
            'autocomplete': 'username',
            'class': 'input input-bordered w-full focus:input-primary'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'autocomplete': 'current-password',
            'id': 'id_password_input',  # ID explícito para referenciar con JS
            'class': 'input input-bordered w-full focus:input-primary join-item'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'space-y-4'
        self.helper.layout = Layout(
            'username',
            # Contenedor con botón toggle de contraseña
            HTML('''
                <div class="form-control">
                    <label class="label" for="id_password_input">
                        <span class="label-text font-medium">Contraseña</span>
                    </label>
                    <div class="join w-full">
                        <input type="password" name="password" id="id_password_input" 
                               placeholder="••••••••" autocomplete="current-password" 
                               class="input input-bordered w-full focus:input-primary join-item" required>
                        <button type="button" id="togglePasswordBtn" 
                                class="btn btn-bordered join-item border-base-300 bg-base-100 px-3 hover:bg-base-200" 
                                title="Mostrar / Ocultar contraseña">
                            <span id="eyeIcon" class="icon-[tabler--eye] size-5 text-base-content/70"></span>
                        </button>
                    </div>
                </div>
            '''),
            Submit('submit', 'Ingresar al Sistema', css_class='btn btn-primary w-full mt-2 font-bold shadow-md')
        )