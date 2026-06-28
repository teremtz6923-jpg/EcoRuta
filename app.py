import os
from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "clave_secreta_para_sesiones_municipales"

# CONFIGURACIÓN PARA SUBIR IMÁGENES
CARPETA_UPLOADS = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = CARPETA_UPLOADS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

# LÍNEA MÁGICA: Crea la carpeta "static/uploads" automáticamente si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ==========================
# CONEXIÓN MONGODB
# ==========================
MONGO_URI = "mongodb+srv://ramt090618mmcmrra1_db_user:tere123456@cluster0.6jerf17.mongodb.net/?appName=Cluster0"
cliente = MongoClient(MONGO_URI)
db = cliente["recoleccion_basura"]

# ==========================
# COLECCIONES
# ==========================
usuarios = db["usuarios"]
camiones = db["camiones"]
conductores = db["conductores"]
rutas = db["rutas"]
reportes = db["reportes"]
fallas = db["fallas"]

# ==========================
# LOGIN
# ==========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"].strip()
        password = request.form["password"].strip()

        if usuario == "admin" and password == "1234":
            session["user"] = "Administrador"
            session["rol"] = "admin"
            return redirect(url_for("admin"))

        elif usuario == "usuario" and password == "1234":
            session["user"] = "Ciudadano"
            session["rol"] = "usuario"
            return redirect(url_for("usuario"))

        else:
            conductor_encontrado = conductores.find_one({"nombre": usuario})
            if conductor_encontrado and password == "1234":
                session["user"] = conductor_encontrado["nombre"]
                session["rol"] = "recolector"
                return redirect(url_for("recolector"))

    return render_template("login.html")

# ==========================
# PANEL ADMINISTRADOR
# ==========================
@app.route("/admin")
def admin():
    # 1. Obtener las listas completas para las tablas (lo que ya tenías)
    lista_reportes = list(reportes.find())
    lista_fallas = list(fallas.find())
    
    # 2. CONTADORES AUTOMÁTICOS PARA EL DASHBOARD
    reportes_pendientes = reportes.count_documents({"estado": "Pendiente"})
    camiones_activos = camiones.count_documents({"estado": "Activo"})
    camiones_mantenimiento = camiones.count_documents({"estado": "Mantenimiento"})
    total_fallas = fallas.count_documents({}) # Cuenta todas las fallas reportadas por los choferes
    
    # 3. Enviar los datos y los nuevos contadores al HTML
    return render_template(
        "admin.html", 
        reportes=lista_reportes, 
        fallas=lista_fallas,
        pendientes=reportes_pendientes,
        activos=camiones_activos,
        mantenimiento=camiones_mantenimiento,
        total_fallas=total_fallas
    )

# ==========================
# PANEL USUARIO Y REPORTES
# ==========================
@app.route("/usuario", methods=["GET", "POST"])
def usuario():
    lista_reportes = list(reportes.find())
    ruta_encontrada = None
    busqueda_realizada = False
    
    if request.method == "POST" and "colonia_buscar" in request.form:
        busqueda_realizada = True
        colonia_buscar = request.form["colonia_buscar"].strip()
        ruta_encontrada = rutas.find_one({"colonia": {"$regex": colonia_buscar, "$options": "i"}})

    return render_template(
        "usuario.html",
        reportes=lista_reportes,
        ruta_encontrada=ruta_encontrada,
        busqueda_realizada=busqueda_realizada
    )

@app.route("/agregar_reporte", methods=["POST"])
def agregar_reporte():
    # 1. Procesar la foto si el usuario subió una
    nombre_foto = None
    if 'foto' in request.files:
        foto = request.files['foto']
        if foto.filename != '':
            # Limpiamos el nombre del archivo para evitar caracteres raros
            nombre_foto = secure_filename(foto.filename)
            # Guardamos la foto físicamente en static/uploads/
            foto.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_foto))

    # 2. Crear el reporte incluyendo la foto (si existe)
    nuevo_reporte = {
        "direccion": request.form["direccion"],
        "descripcion": request.form["descripcion"],
        "fecha": request.form["fecha"],  
        "estado": "Pendiente",
        "foto": nombre_foto  # <-- Se guarda el nombre de la imagen en la BD
    }
    
    reportes.insert_one(nuevo_reporte)
    return redirect(url_for("usuario"))

# ==========================
# PANEL RECOLECTOR
# ==========================
@app.route("/recolector")
def recolector():
    if "user" not in session or session["rol"] != "recolector":
        return redirect(url_for("login"))
        
    chofer_logueado = session["user"]
    lista_rutas = list(rutas.find({"conductor": chofer_logueado}))
    return render_template("recolector.html", rutas=lista_rutas)

@app.route("/completar_ruta/<string:id>")
def completar_ruta(id):
    rutas.update_one(
        {"_id": ObjectId(id.strip())},
        {"$set": {"estado": "Completada"}}
    )
    return redirect(url_for("recolector"))

@app.route("/reportar_falla", methods=["POST"])
def reportar_falla():
    if "user" not in session or session["rol"] != "recolector":
        return redirect(url_for("login"))
        
    nueva_falla = {
        "conductor": session["user"],
        "tipo_falla": request.form["tipo_falla"],
        "detalles": request.form["detalles"],
        "fecha": request.form["fecha_falla"],
        "estado": "Reportado"
    }
    
    fallas.insert_one(nueva_falla)
    return redirect(url_for("recolector"))

# ==========================
# CRUD CAMIONES
# ==========================
@app.route("/camiones")
def mostrar_camiones():
    lista_camiones = list(camiones.find())
    return render_template("camiones.html", camiones=lista_camiones)

@app.route("/agregar_camion", methods=["POST"])
def agregar_camion():
    nuevo_camion = {
        "placa": request.form["placa"],
        "modelo": request.form["modelo"],
        "marca": request.form["marca"],
        "capacidad": request.form["capacidad"],
        "estado": request.form["estado"],
        "ruta": request.form["ruta"]
    }
    camiones.insert_one(nuevo_camion)
    return redirect(url_for("mostrar_camiones"))

@app.route("/eliminar_camion/<id>")
def eliminar_camion(id):
    camiones.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("mostrar_camiones"))

@app.route("/editar_camion/<id>")
def editar_camion(id):
    camion = camiones.find_one({"_id": ObjectId(id)})
    return render_template("editar_camion.html", camion=camion)

@app.route("/actualizar_camion/<id>", methods=["POST"])
def actualizar_camion(id):
    camiones.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "placa": request.form["placa"],
            "modelo": request.form["modelo"],
            "marca": request.form["marca"],
            "capacidad": request.form["capacidad"],
            "estado": request.form["estado"],
            "ruta": request.form["ruta"]
        }}
    )
    return redirect(url_for("mostrar_camiones"))

# ==========================
# CRUD CONDUCTORES
# ==========================
@app.route("/conductores")
def mostrar_conductores():
    lista_conductores = list(conductores.find())
    return render_template("conductores.html", conductores=lista_conductores)

@app.route("/agregar_conductor", methods=["POST"])
def agregar_conductor():
    nuevo_conductor = {
        "nombre": request.form["nombre"],
        "edad": request.form["edad"],
        "telefono": request.form["telefono"],
        "licencia": request.form["licencia"],
        "turno": request.form["turno"],
        "ruta": request.form["ruta"],
        "estado": request.form["estado"]
    }
    conductores.insert_one(nuevo_conductor)
    return redirect(url_for("mostrar_conductores"))

@app.route("/eliminar_conductor/<id>")
def eliminar_conductor(id):
    conductores.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("mostrar_conductores"))

@app.route("/editar_conductor/<id>")
def editar_conductor(id):
    conductor = conductores.find_one({"_id": ObjectId(id)})
    return render_template("editar_conductor.html", conductor=conductor)

@app.route("/actualizar_conductor/<id>", methods=["POST"])
def actualizar_conductor(id):
    conductores.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "nombre": request.form["nombre"],
            "edad": request.form["edad"],
            "telefono": request.form["telefono"],
            "licencia": request.form["licencia"],
            "turno": request.form["turno"],
            "ruta": request.form["ruta"],
            "estado": request.form["estado"]
        }}
    )
    return redirect(url_for("mostrar_conductores"))

# ==========================
# CRUD RUTAS
# ==========================
@app.route("/rutas")
def mostrar_rutas():
    lista_rutas = list(rutas.find())
    return render_template("rutas.html", rutas=lista_rutas)

@app.route("/agregar_ruta", methods=["POST"])
def agregar_ruta():
    nueva_ruta = {
        "nombre": request.form["nombre"],
        "colonia": request.form["colonia"],
        "horario": request.form["horario"],
        "camion": request.form["camion"],
        "conductor": request.form["conductor"],
        "estado": request.form["estado"]
    }
    rutas.insert_one(nueva_ruta)
    return redirect(url_for("mostrar_rutas"))

@app.route("/eliminar_ruta/<id>")
def eliminar_ruta(id):
    rutas.delete_one({"_id": ObjectId(id)})
    return redirect(url_for("mostrar_rutas"))

@app.route("/editar_ruta/<id>")
def editar_ruta(id):
    ruta = rutas.find_one({"_id": ObjectId(id)})
    return render_template("editar_ruta.html", ruta=ruta)

@app.route("/actualizar_ruta/<id>", methods=["POST"])
def actualizar_ruta(id):
    rutas.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "nombre": request.form["nombre"],
            "colonia": request.form["colonia"],
            "horario": request.form["horario"],
            "camion": request.form["camion"],
            "conductor": request.form["conductor"],
            "estado": request.form["estado"]
        }}
    )
    return redirect(url_for("mostrar_rutas"))
@app.route("/solucionar_reporte/<string:id>")  # <-- Aquí le agregamos string: antes de id
def solucionar_reporte(id):
    # Si la sesión no es de administrador, lo regresa al login
    if "user" not in session or session["rol"] != "admin":
        return redirect(url_for("login"))
    
    from bson.objectid import ObjectId
    
    # Buscamos en tu colección de reportes y actualizamos el estado
    # Nota: Si tu variable de la colección se llama de otra forma (ej. db.reportes), cámbiala aquí:
    reportes.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"estado": "Solucionado"}}
    )
    
    # Regresa al panel de administración con los cambios aplicados
    return redirect(url_for("admin"))

# ==========================
# EJECUTAR
# ==========================
if __name__ == "__main__":
    app.run(debug=True)