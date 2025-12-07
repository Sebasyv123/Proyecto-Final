import sys
import os
from PyQt5 import QtWidgets
from Vista.Login import Ui_LoginWindow
from Modelo.autenticacion import ModeloUsuarios
from Controlador.controlador_login import ControladorLogin

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    ventana_login = QtWidgets.QMainWindow()
    ui_login = Ui_LoginWindow()
    ui_login.setupUi(ventana_login)
    ventana_login.ui = ui_login  

    ruta_xml = os.path.join(os.path.dirname(__file__), "Datos_XML", "usuarios.xml")
    modelo = ModeloUsuarios(ruta_xml)

    controlador = ControladorLogin(ventana_login, modelo)

    ventana_login.show()

    sys.exit(app.exec_())