import xml.etree.ElementTree as ET
import os

class ModeloUsuarios:
    def __init__(self, ruta_xml):
        # Ruta del archivo XML donde están almacenados los usuarios
        self.ruta = ruta_xml
        
        # Lista que almacenará diccionarios con los usuarios cargados
        self.usuarios = []
        
        # Llama al método que lee el archivo XML
        self.cargar_usuarios()

    def cargar_usuarios(self):
        # Verifica que el archivo exista
        if not os.path.exists(self.ruta):
            print(f"Archivo no encontrado: {self.ruta}")
            return
        
        # Carga y parsea el XML
        tree = ET.parse(self.ruta)
        root = tree.getroot()  # Nodo raíz <users>
        
        # Recorre cada nodo <user> dentro de <users>
        for u in root.findall("user"):
            # Obtiene el texto de los nodos hijo <usuario> y <contrasena>
            usuario = u.find("usuario").text.strip()
            contrasena = u.find("contrasena").text.strip()
            
            # Almacena el usuario como un diccionario
            self.usuarios.append({"usuario": usuario, "contrasena": contrasena})
            
    def validar_usuario(self, usuario, contrasena):
        # Limpia espacios extra por si el usuario los escribe accidentalmente
        usuario = usuario.strip()
        contrasena = contrasena.strip()
        
        # Busca coincidencia exacta usuario/contraseña dentro de los cargados
        for u in self.usuarios:
            if u["usuario"] == usuario and u["contrasena"] == contrasena:
                return True
        
        # Si ningún usuario coincide, retorna False
        return False


    

        