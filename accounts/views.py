import random
import threading
from datetime import timedelta

from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages

from .forms import LoginForm, TwoFactorForm, RegisterForm


User = get_user_model()


def login_view(request):
    """
    Paso 1: usuario ingresa CORREO + CONTRASEÑA.
    Si son correctos se genera código 2FA y se envía por correo.
    """

    # Si ya está autenticado, se va directamente al menú
    if request.user.is_authenticated:
        return redirect('menu_principal')

    # Leer cookie para recordar el email
    email_recordado = request.COOKIES.get('recordar_email', '')

    # Leer dispositivos o usuarios recordados
    usuario_recordado = request.COOKIES.get(
        'trusted_users',
        ''
    ).split(',')

    if request.method == 'POST':

        form = LoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            recordarme = form.cleaned_data['recordarme']

            try:
                user = User.objects.get(email=email)

            except User.DoesNotExist:
                form.add_error(
                    None,
                    "Este correo no está registrado. ¿Quieres crear una cuenta?"
                )

            except User.MultipleObjectsReturned:
                form.add_error(
                    None,
                    "Correo o contraseña inválidos."
                )

            else:

                user_auth = authenticate(
                    request,
                    username=user.username,
                    password=password
                )

                if user_auth is None:

                    form.add_error(
                        None,
                        "Correo o contraseña inválidos."
                    )

                else:

                    # Verificar si este usuario está marcado como confiable
                    verificado = str(user_auth.id) in usuario_recordado

                    # ==========================================
                    # USUARIO / DISPOSITIVO CONFIABLE
                    # ==========================================

                    if verificado:

                        login(request, user_auth)

                        # Mantener sesión por 30 días
                        request.session.set_expiry(
                            60 * 60 * 24 * 30
                        )

                        response = redirect('menu_principal')

                    # ==========================================
                    # USUARIO NUEVO PIDE 2FA
                    # ==========================================

                    else:

                        # Generar código de 6 dígitos
                        code = f"{random.randint(0, 999999):06d}"

                        # Guardar datos temporales del 2FA
                        request.session['2fa_user_id'] = user_auth.id
                        request.session['2fa_code'] = code

                        request.session['2fa_expires'] = (
                            timezone.now() + timedelta(minutes=5)
                        ).isoformat()

                        request.session['recordarme'] = recordarme

                        def enviar_correo_async(email, code):

                            try:

                                print("=" * 50)
                                print("CORREO 2FA")
                                print(f"Destinatario: {email}")
                                print(f"Código: {code}")
                                print("=" * 50)

                                resultado = send_mail(
                                    subject="Código de verificación - Panadería Jumbo",
                                    message=f"Tu código de verificación es: {code}",
                                    from_email=None,
                                    recipient_list=[email],
                                    fail_silently=False,
                                )

                                print(
                                    f"Resultado envío: {resultado}"
                                )

                            except Exception as e:

                                print(
                                    "Error al enviar correo:",
                                    e
                                )

                        # Enviar correo sin bloquear la respuesta
                        thread = threading.Thread(
                            target=enviar_correo_async,
                            args=(user_auth.email, code)
                        )

                        thread.start()

                        messages.info(
                            request,
                            "Te hemos enviado un código de verificación a tu correo."
                        )

                        response = redirect('two_factor_view')

                    # ==========================================
                    # RECORDAR EMAIL
                    # ==========================================

                    if recordarme:

                        response.set_cookie(
                            'recordar_email',
                            email,
                            max_age=30 * 24 * 60 * 60
                        )

                    else:

                        response.delete_cookie(
                            'recordar_email'
                        )

                    return response

    else:

        # Pre-rellenar email si existe cookie
        form = LoginForm(
            initial={
                'email': email_recordado,
                'recordarme': bool(email_recordado)
            }
        )

    return render(
        request,
        'accounts/login.html',
        {'form': form}
    )


def two_factor_view(request):
    """
    Paso 2: usuario ingresa el código recibido por correo.
    Si es correcto y no ha expirado → login final.
    """

    user_id = request.session.get('2fa_user_id')
    stored_code = request.session.get('2fa_code')
    expires_str = request.session.get('2fa_expires')

    # Si no existen datos de verificación
    if not user_id or not stored_code or not expires_str:

        messages.warning(
            request,
            "Sesión de verificación no encontrada. Vuelve a iniciar sesión."
        )

        return redirect('login')

    expires_at = timezone.datetime.fromisoformat(
        expires_str
    )

    if request.method == 'POST':

        form = TwoFactorForm(request.POST)

        if form.is_valid():

            code_ingresado = form.cleaned_data['code'].strip()

            # ==========================================
            # VERIFICAR EXPIRACIÓN
            # ==========================================

            if timezone.now() > expires_at:

                messages.error(
                    request,
                    "El código ha expirado. Vuelve a iniciar sesión."
                )

                request.session.pop(
                    '2fa_user_id',
                    None
                )

                request.session.pop(
                    '2fa_code',
                    None
                )

                request.session.pop(
                    '2fa_expires',
                    None
                )

                return redirect('login')

            # ==========================================
            # CÓDIGO INCORRECTO
            # ==========================================

            if code_ingresado != stored_code:

                messages.error(
                    request,
                    "Código incorrecto."
                )

            else:

                try:

                    user = User.objects.get(
                        id=user_id
                    )

                except User.DoesNotExist:

                    messages.error(
                        request,
                        "Usuario no encontrado. Vuelve a iniciar sesión."
                    )

                    return redirect('login')

                # ==========================================
                # LOGIN EXITOSO
                # ==========================================

                login(request, user)

                # Guardamos el valor ANTES de eliminarlo
                recordarme = request.session.get(
                    'recordarme',
                    False
                )

                # ==========================================
                # DURACIÓN DE LA SESIÓN
                # ==========================================

                if recordarme:

                    # Mantener sesión iniciada durante 30 días
                    request.session.set_expiry(
                        60 * 60 * 24 * 30
                    )

                else:

                    # La sesión termina al cerrar el navegador
                    request.session.set_expiry(0)

                # ==========================================
                # LIMPIAR DATOS TEMPORALES DEL 2FA
                # ==========================================

                request.session.pop(
                    '2fa_user_id',
                    None
                )

                request.session.pop(
                    '2fa_code',
                    None
                )

                request.session.pop(
                    '2fa_expires',
                    None
                )

                # Limpiar flag temporal
                request.session.pop(
                    'recordarme',
                    None
                )

                messages.success(
                    request,
                    "Verificación exitosa."
                )

                response = redirect(
                    'menu_principal'
                )

                # ==========================================
                # GUARDAR DISPOSITIVO CONFIABLE
                # ==========================================

                if recordarme:

                    usuario_recordado = request.COOKIES.get(
                        'trusted_users',
                        ''
                    ).split(',')

                    usuario_recordado = [
                        usuario
                        for usuario in usuario_recordado
                        if usuario
                    ]

                    if str(user.id) not in usuario_recordado:

                        usuario_recordado.append(
                            str(user.id)
                        )

                    response.set_cookie(
                        'trusted_users',
                        ','.join(usuario_recordado),
                        max_age=30 * 24 * 60 * 60,
                        secure=not request.is_secure() is False,
                        httponly=True,
                        samesite='Lax'
                    )

                    response.set_cookie(
                        'recordar_email',
                        user.email,
                        max_age=30 * 24 * 60 * 60,
                        secure=request.is_secure(),
                        samesite='Lax'
                    )

                return response

    else:

        form = TwoFactorForm()

    return render(
        request,
        'accounts/doble-factor.html',
        {'form': form}
    )


def logout_view(request):

    logout(request)

    return redirect('login')


@login_required
def menu_principal(request):
    """
    Pantalla protegida que se verá después del 2FA.
    """

    return render(
        request,
        'accounts/menu.html'
    )


def register_view(request):

    if request.user.is_authenticated:

        return redirect('menu_principal')

    if request.method == 'POST':

        form = RegisterForm(request.POST)

        if form.is_valid():

            User = get_user_model()

            email = form.cleaned_data['email']

            password = form.cleaned_data['password1']

            # Crear usuario usando el email como username
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )

            messages.success(
                request,
                "Cuenta creada exitosamente. Ya puedes iniciar sesión."
            )

            return redirect('login')

    else:

        form = RegisterForm()

    return render(
        request,
        'accounts/register.html',
        {'form': form}
    )