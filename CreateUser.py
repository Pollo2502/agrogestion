import os
import django
from tkinter import *
from tkinter import messagebox
from django.contrib.auth.hashers import make_password

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrogestion.settings')
django.setup()

from usuarios.models import User

def registrar_usuario():
    nombre = entry_nombre.get()
    password = entry_password.get()
    email = entry_email.get()
    telefono = entry_telefono.get()

    if not nombre or not password:
        messagebox.showerror("Error", "Nombre y contraseña son obligatorios.")
        return

    if User.objects.filter(nombre=nombre).exists():
        messagebox.showerror("Error", "El nombre de usuario ya existe.")
        return

    if email and User.objects.filter(email=email).exists():
        messagebox.showerror("Error", "El email ya está registrado.")
        return

    hashed_password = make_password(password)
    user = User(
        nombre=nombre,
        password=hashed_password,
        email=email if email else None,
        telefono=telefono if telefono else None
    )
    user.save()
    messagebox.showinfo("Éxito", "Usuario registrado correctamente.")
    entry_nombre.delete(0, END)
    entry_password.delete(0, END)
    entry_email.delete(0, END)
    entry_telefono.delete(0, END)

# Interfaz Tkinter
root = Tk()
root.title("Registro de Usuario Admin")
root.geometry("350x300")
root.resizable(False, False)

Label(root, text="Registro de Usuario", font=("Arial", 16)).pack(pady=10)

frame = Frame(root)
frame.pack(pady=10)

Label(frame, text="Nombre:").grid(row=0, column=0, sticky=E, pady=5)
entry_nombre = Entry(frame, width=25)
entry_nombre.grid(row=0, column=1, pady=5)

Label(frame, text="Contraseña:").grid(row=1, column=0, sticky=E, pady=5)
entry_password = Entry(frame, show="*", width=25)
entry_password.grid(row=1, column=1, pady=5)

Label(frame, text="Email:").grid(row=2, column=0, sticky=E, pady=5)
entry_email = Entry(frame, width=25)
entry_email.grid(row=2, column=1, pady=5)

Label(frame, text="Teléfono:").grid(row=3, column=0, sticky=E, pady=5)
entry_telefono = Entry(frame, width=25)
entry_telefono.grid(row=3, column=1, pady=5)

Button(root, text="Registrar", command=registrar_usuario, width=15, bg="#4CAF50", fg="white").pack(pady=15)

root.mainloop()