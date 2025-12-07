from PyQt5 import QtWidgets
from Vista.dashboard import Ui_MainWindow
from Controlador.controlador_imagenes import ControladorImagenes
from Controlador.controlador_senales import ControladorSenales
from Controlador.controlador_csv import ControladorCSV
from Controlador.controlador_historial import ControladorHistorial

class ControladorDashboard:
    def __init__(self, ventana_dashboard, usuario, db_historial, sesion_id):
        self.ventana = ventana_dashboard
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.ventana)

        # Datos de sesión
        self.usuario_actual = usuario
        self.db_historial = db_historial
        self.sesion_id = sesion_id

        # Conectar botones
        self.ui.btnImagenes.clicked.connect(self.abrir_imagenes)
        self.ui.btnSenales.clicked.connect(self.abrir_senales)
        self.ui.btnCSV.clicked.connect(self.abrir_csv)
        self.ui.btnHistorial.clicked.connect(self.abrir_historial)
        self.ui.btnCerrarSesion.clicked.connect(self.cerrar_sesion)

        # Variables de controladores secundarios
        self.ctrl_imagenes = None
        self.ctrl_senales = None
        self.ctrl_csv = None
        self.ctrl_historial = None

    def abrir_imagenes(self):
        self.db_historial.agregar_accion(self.sesion_id, "Imagen")
        self.ventana_img = QtWidgets.QMainWindow()
        self.ctrl_imagenes = ControladorImagenes(self.ventana_img, self.ventana)
        self.ventana_img.show()
        self.ventana.hide()

    def abrir_senales(self):
        self.db_historial.agregar_accion(self.sesion_id, "Señal")
        self.ventana_senales = QtWidgets.QWidget()
        self.ctrl_senales = ControladorSenales(self.ventana_senales, self.ventana)
        self.ventana_senales.show()
        self.ventana.hide()

    def abrir_csv(self):
        self.db_historial.agregar_accion(self.sesion_id, "CSV")
        self.ventana_csv = QtWidgets.QDialog()
        self.ctrl_csv = ControladorCSV(self.ventana_csv, self.ventana)
        self.ventana_csv.show()
        self.ventana.hide()

    def abrir_historial(self):
        self.ctrl_historial = ControladorHistorial(
            modelo=self.db_historial,       # DatabaseManager
            ventana_dashboard=self.ventana  # ventana del dashboard
        )
        self.ctrl_historial.show()
        self.ventana.hide()
    def cerrar_sesion(self):
        self.ventana.close()
        print("Sesión cerrada")
