import random
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
 
    # Si ya está autenticado, lo mandamos al menú
    if request.user.is_authenticated:
        return redirect('menu_principal')
 
    # leer el cookie para recordar al usuario por 30 dias
    email_recordado = request.COOKIES.get('recordar_email', '')
    # FIX: leer trusted_users (antes era 'recordar_usuario' que no se usaba)
    usuario_recordado = request.COOKIES.get('trusted_users', '').split(',')
 
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email      = form.cleaned_data['email']
            password   = form.cleaned_data['password']
            recordarme = form.cleaned_data['recordarme']
 
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                form.add_error(None, "Este correo no está registrado. ¿Quieres crear una cuenta?")
            except User.MultipleObjectsReturned:
                form.add_error(None, "Correo o contraseña inválidos.")
            else:
                user_auth = authenticate(
                    request,
                    username=user.username,
                    password=password
                )
                if user_auth is None:
                    form.add_error(None, "Correo o contraseña inválidos.")
                else:
                    # FIX: comparar contra usuario_recordado (lista), no contra recordarme (bool)
                    verificado = str(user_auth.id) in usuario_recordado
 
                    if verificado:
                        login(request, user_auth)
                        response = redirect('menu_principal')
 
                    else:
                        # Generar y enviar código 2FA
                        code = f"{random.randint(0, 999999):06d}"
                        request.session['2fa_user_id'] = user_auth.id
                        request.session['2fa_code']    = code
                        request.session['2fa_expires'] = (
                            timezone.now() + timedelta(minutes=5)
                        ).isoformat()
                        request.session['recordarme']  = recordarme
 
                        try:
                            send_mail(
                                subject="Código de verificación - Panadería Jumbo",
                                message=f"Tu código de verificación es: {code}",
                                from_email=None,
                                recipient_list=[user_auth.email],
                            )
                        except Exception as e:
                            print("Error al enviar correo:", e)
 
                        messages.info(request, "Te hemos enviado un código de verificación a tu correo.")
                        response = redirect('two_factor_view')
 
                    # Guardar cookie del email si marcó recordarme
                    if recordarme:
                        response.set_cookie('recordar_email', email, max_age=30*24*60*60)
                    else:
                        response.delete_cookie('recordar_email')
 
                    return response
    else:
        # Pre-rellenar email si hay cookie
        form = LoginForm(initial={'email': email_recordado, 'recordarme': bool(email_recordado)})
 
    return render(request, 'accounts/login.html', {'form': form})
 
 
def two_factor_view(request):
    """
    Paso 2: usuario ingresa el código recibido por correo.
    Si es correcto y no ha expirado → login final.
    """
 
    user_id     = request.session.get('2fa_user_id')
    stored_code = request.session.get('2fa_code')
    expires_str = request.session.get('2fa_expires')
 
    # Si no hay datos en sesión, lo mandamos a login
    if not user_id or not stored_code or not expires_str:
        messages.warning(request, "Sesión de verificación no encontrada. Vuelve a iniciar sesión.")
        return redirect('login')
 
    expires_at = timezone.datetime.fromisoformat(expires_str)
 
    if request.method == 'POST':
        form = TwoFactorForm(request.POST)
        if form.is_valid():
            code_ingresado = form.cleaned_data['code'].strip()
 
            if timezone.now() > expires_at:
                messages.error(request, "El código ha expirado. Vuelve a iniciar sesión.")
                request.session.pop('2fa_user_id', None)
                request.session.pop('2fa_code', None)
                request.session.pop('2fa_expires', None)
                return redirect('login')
 
            if code_ingresado != stored_code:
                messages.error(request, "Código incorrecto.")
            else:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    messages.error(request, "Usuario no encontrado. Vuelve a iniciar sesión.")
                    return redirect('login')
 
                login(request, user)
 
                # Limpiar sesión de 2FA
                request.session.pop('2fa_user_id', None)
                request.session.pop('2fa_code', None)
                request.session.pop('2fa_expires', None)
 
                messages.success(request, "Verificación exitosa.")
                response = redirect('menu_principal')
 
                # Recordarme: guardar cookie de dispositivo de confianza
                if request.session.get('recordarme', False):
                    # FIX: usar el mismo nombre 'trusted_users' que lee login_view
                    usuario_recordado = request.COOKIES.get('trusted_users', '').split(',')
                    usuario_recordado = [t for t in usuario_recordado if t]
                    if str(user.id) not in usuario_recordado:
                        usuario_recordado.append(str(user.id))
                    response.set_cookie('trusted_users', ','.join(usuario_recordado), max_age=30*24*60*60)
                    response.set_cookie('recordar_email', user.email, max_age=30*24*60*60)
                    request.session.pop('recordarme', None)
 
                return response
    else:
        form = TwoFactorForm()
 
    return render(request, 'accounts/doble-factor.html', {'form': form})
 
 
def logout_view(request):
    logout(request)
    return redirect('login')
 
 
@login_required
def menu_principal(request):
    """
    Pantalla protegida que se verá DESPUÉS del 2FA.
    """
    return render(request, 'accounts/menu.html')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('menu_principal')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            email    = form.cleaned_data['email']
            password = form.cleaned_data['password1']

            # Crear usuario usando el email como username también
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
            messages.success(request, "Cuenta creada exitosamente. Ya puedes iniciar sesión.")
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})