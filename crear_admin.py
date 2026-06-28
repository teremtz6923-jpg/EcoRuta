from conexion import db

usuarios = db["usuarios"]

admin = {
    "nombre": "Administrador",
    "usuario": "admin",
    "password": "1234",
    "rol": "admin"
}

recolector = {
    "nombre": "Juan",
    "usuario": "recolector",
    "password": "1234",
    "rol": "recolector"
}

usuario = {
    "nombre": "Carlos",
    "usuario": "usuario",
    "password": "1234",
    "rol": "usuario"
}

usuarios.insert_one(admin)
usuarios.insert_one(recolector)
usuarios.insert_one(usuario)

print("Usuarios creados correctamente")