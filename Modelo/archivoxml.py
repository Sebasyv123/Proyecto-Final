# -*- coding: utf-8 -*-
"""
Created on Sun Nov 30 17:29:04 2025

@author: Sofia
"""

import xml.etree.ElementTree as ET

def generar_xml_usuarios(ruta="usuarios.xml"):
    # Crear elemento raíz
    root = ET.Element("usuarios")

    # Lista de usuarios a agregar
    usuarios = [
        {
            "id": "001",
            "nombre": "Sofía Estrada",
            "correo": "esofiafedimon@gmail.com",
            "telefono": "3205007161",
            "username": "sofia",
            "password": "sofia10",
            "rol": "Usuario"
        },
        {
            "id": "002",
            "nombre": "Maria Acelas",
            "correo": "maria.acelas@gmail.com",
            "telefono": "3019876543",
            "username": "mariam",
            "password": "password123",
            "rol": "Usuario"
        },
        {
            "id": "003",
            "nombre": "Sebastián Yepes",
            "correo": "s.yepes@gmail.com",
            "telefono": "3135243187",
            "username": "sebasyepes",
            "password": "admin123",
            "rol": "Administrador"
        }
    ]

    # Crear nodos en XML
    for u in usuarios:
        usuario = ET.SubElement(root, "usuario")

        ET.SubElement(usuario, "id").text = u["id"]
        ET.SubElement(usuario, "nombre").text = u["nombre"]
        ET.SubElement(usuario, "correo").text = u["correo"]
        ET.SubElement(usuario, "telefono").text = u["telefono"]
        ET.SubElement(usuario, "username").text = u["username"]
        ET.SubElement(usuario, "password").text = u["password"]
        ET.SubElement(usuario, "rol").text = u["rol"]

    # Crear árbol XML y guardarlo
    tree = ET.ElementTree(root)
    tree.write(ruta, encoding="utf-8", xml_declaration=True)

    print(f"Archivo XML generado correctamente en: {ruta}")


# Ejecutar la función
if __name__ == "__main__":
    generar_xml_usuarios()