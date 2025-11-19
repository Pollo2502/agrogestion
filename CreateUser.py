import os
import sys
import argparse
import django
from getpass import getpass
from django.contrib.auth.hashers import make_password

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrogestion.settings')
django.setup()

from usuarios.models import User

def registrar_usuario_cli(nombre, password, email=None, telefono=None):
    """
    Registra un usuario usando parámetros (útil para CLI).
    Devuelve (True, mensaje) o (False, mensaje)
    """
    if not nombre or not password:
        return False, "Nombre y contraseña son obligatorios."

    if User.objects.filter(nombre=nombre).exists():
        return False, "El nombre de usuario ya existe."

    if email and User.objects.filter(email=email).exists():
        return False, "El email ya está registrado."

    try:
        hashed_password = make_password(password)
        user = User(
            nombre=nombre,
            password=hashed_password,
            email=email if email else None,
            telefono=telefono if telefono else None
        )
        user.save()
        return True, "Usuario registrado correctamente."
    except Exception as e:
        return False, f"Error al guardar usuario: {e}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Registrar usuario en Django (CLI).")
    parser.add_argument('--nombre', '-u', help='Nombre de usuario')
    parser.add_argument('--password', '-p', help='Contraseña')
    parser.add_argument('--email', '-e', help='Email (opcional)')
    parser.add_argument('--telefono', '-t', help='Teléfono (opcional)')
    args = parser.parse_args()

    nombre = args.nombre
    password = args.password
    email = args.email
    telefono = args.telefono

    try:
        if not nombre:
            nombre = input("Nombre de usuario: ").strip()
        if not password:
            password = getpass("Contraseña: ")
            if not password:
                # permitir reintento simple
                password = getpass("Contraseña (nuevamente): ")
        if email is None:
            email = input("Email (opcional): ").strip() or None
        if telefono is None:
            telefono = input("Teléfono (opcional): ").strip() or None
    except KeyboardInterrupt:
        print("\nOperación cancelada.")
        sys.exit(2)

    ok, msg = registrar_usuario_cli(nombre, password, email, telefono)
    if ok:
        print(msg)
        sys.exit(0)
    else:
        print("Error:", msg)
        sys.exit(1)