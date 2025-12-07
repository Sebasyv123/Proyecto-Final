# ============================================================
# BASE DE DATOS - MONGODB
# ============================================================

from pymongo import MongoClient
from datetime import datetime


class DatabaseManager:
    """
    Gestor de base de datos MongoDB.
    Registra actividad del usuario:
    - usuario
    - tipo de análisis
    - ruta de salida
    - fecha y hora
    """

    def __init__(self, uri="mongodb+srv://pinodbUser:juliymeli123@cluster0.fmovcjt.mongodb.net/?appName=Cluster0", db_name="Biomodal_MSJS"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]

    def registrar_evento(self, usuario, tipo, ruta):
        evento = {
            "usuario": usuario,
            "tipo": tipo,
            "ruta": ruta,
            "fecha": datetime.now()
        }
        self.db["eventos"].insert_one(evento)

    def obtener_eventos(self):
        return list(self.db["eventos"].find()) 
    

   
    
