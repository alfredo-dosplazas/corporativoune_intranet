from crispy_forms.helper import FormHelper
from django import forms

from apps.regalos.models import Regalo


class RegaloForm(forms.ModelForm):
    class Meta:
        model = Regalo
        fields = [
            'numero',
            'nombre',
            'imagen',
        ]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_id = 'regalo-form'
        self.helper.attrs = {'novalidate': 'novalidate'}
        self.helper.include_media = False