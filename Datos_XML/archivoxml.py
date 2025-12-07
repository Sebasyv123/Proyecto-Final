import xml.etree.ElementTree as ET
from xml.dom import minidom

# Crear la estructura del XML
root = ET.Element("users")

usuarios = [
    {"id":"1001", "usuario":"sofiae", "nombre":"Sofia Estrada", "correo":"s.estrada@udea.edu.co", "telefono":"3205007161", "contrasena":"Sofia10"},
    {"id":"1002", "usuario":"macelas", "nombre":"Maria Acelas", "correo":"maria.acelas@udea.edu.co", "telefono":"3135098762", "contrasena":"M.134"},
    {"id":"1003", "usuario":"yepess", "nombre":"Sebastián Yepes", "correo":"yeps@udea.edu.co", "telefono":"3233398012", "contrasena":"passw0rd"}
]

for u in usuarios:
    user = ET.SubElement(root, "user")
    for key, value in u.items():
        child = ET.SubElement(user, key)
        child.text = value

# Pretty print
xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

# Guardar el archivo
with open("usuarios.xml", "w", encoding="utf-8") as f:
    f.write(xml_str)

print("Archivo usuarios.xml creado correctamente")