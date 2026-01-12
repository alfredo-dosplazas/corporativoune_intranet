from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.contrib.auth.forms import AuthenticationForm


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'login-form'
        self.helper.attrs = {'novalidate': 'novalidate'}

        self.helper.add_input(Submit('submit', 'Iniciar Sesión', css_class='btn btn-primary'))
