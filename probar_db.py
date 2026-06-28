from pymongo import MongoClient

MONGO_URI = "mongodb+srv://ramt090618mmcmrra1_db_user:tere123456@cluster0.kaznpfp.mongodb.net/recoleccion_basura?retryWrites=true&w=majority&appName=Cluster0"

cliente = MongoClient(MONGO_URI)

db = cliente["recoleccion_basura"]

coleccion = db["prueba"]

dato = {
    "mensaje": "hola mundo"
}

resultado = coleccion.insert_one(dato)

print("ID insertado:", resultado.inserted_id)