# accounts/forms.py
from django import forms

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Ingrese su correo"
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "********"
        })
    )
    recordarme = forms.BooleanField(
        required=False,
        label="Recordarme por 30 días"
    )


class TwoFactorForm(forms.Form):
    code = forms.CharField(
        label="Código de verificación",
        max_length=6,
        widget=forms.TextInput(attrs={
            "class": "form-control text-center",
            "placeholder": "000000"
        })
    )

class RegisterForm(forms.Form):
    email = forms.EmailField(
        label="Correo electrónico",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "Ingrese su correo"
        })
    )
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Crea una contraseña"
        })
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Repite la contraseña"
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def clean_email(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email