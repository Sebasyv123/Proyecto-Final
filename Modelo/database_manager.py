from pymongo import MongoClient
from datetime import datetime

class DatabaseManager:
    """
    Gestor de base de datos MongoDB para historial por sesión.
    - Un registro por login
    - Lista de acciones realizadas (Imagen, CSV, Señal)
    - Carpeta fija 'Resultados'
    - Fecha y hora de login
    """
    def __init__(self):
        self.uri = "mongodb+srv://msjs8933_db_user:C30PXM0gjBKbASzb@cluster0.hy12ifc.mongodb.net/?appName=Cluster0"
        self.db_name = "Biomodal_MSJS"
        self.client = MongoClient(self.uri)
        self.db = self.client[self.db_name]

    def crear_sesion(self, usuario):
        """
        Crea un registro único de sesión cuando el usuario hace login.
        Devuelve el _id del registro para agregar acciones después.
        """
        sesion = {
            "usuario": usuario,
            "fecha_hora_login": datetime.now(),  # Aquí se registra la fecha al ingresar
            "acciones": [],                       # Lista de botones presionados
            "ruta": "Resultados"
        }
        result = self.db["eventos"].insert_one(sesion)
        return result.inserted_id

    def agregar_accion(self, id_sesion, accion):
        """
        Agrega un botón presionado a la lista de acciones de la sesión
        Sin fecha/hora
        """
        self.db["eventos"].update_one(
            {"_id": id_sesion},
            {"$push": {"acciones": accion}}
        )

    def obtener_eventos(self):
        return list(self.db["eventos"].find())

    
