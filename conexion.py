from pymongo import MongoClient

MONGO_URI = "mongodb+srv://ramt090618mmcmrra1_db_user:tere123456@cluster0.kaznpfp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

cliente = MongoClient(MONGO_URI)

# LISTAR BASES
print(cliente.list_database_names())

db = cliente["recoleccion_basura"]