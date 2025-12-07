from PyQt5 import QtWidgets
from Vista.dashboard import Ui_MainWindow
# Importamos tus controladores (asegúrate de que los nombres de archivo coincidan)
from Controlador.controlador_imagenes import ControladorImagenes
from Controlador.controlador_senales import ControladorSenales
from Controlador.controlador_csv import ControladorCSV
from Controlador.controlador_historial import ControladorHistorial


class ControladorDashboard:
    def __init__(self, ventana_dashboard):
        self.ventana = ventana_dashboard
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self.ventana)

        # Conectar botones del menú a sus funciones
        self.ui.btnImagenes.clicked.connect(self.abrir_imagenes)
        self.ui.btnSenales.clicked.connect(self.abrir_senales)
        self.ui.btnCSV.clicked.connect(self.abrir_csv)
        self.ui.btnHistorial.clicked.connect(self.abrir_historial)
        self.ui.btnCerrarSesion.clicked.connect(self.cerrar_sesion)

        # --- VARIABLES PARA LOS CONTROLADORES ---
        self.ctrl_imagenes = None
        self.ctrl_senales = None
        self.ctrl_csv = None
        self.ctrl_historial = None

    def abrir_imagenes(self):
        self.ventana_img = QtWidgets.QMainWindow()
        self.ctrl_imagenes = ControladorImagenes(self.ventana_img, self.ventana) 
        self.ventana_img.show()
        self.ventana.hide()

    def abrir_senales(self):
        self.ventana_senales = QtWidgets.QWidget() 
        self.ctrl_senales = ControladorSenales(self.ventana_senales, self.ventana)
        self.ventana_senales.show()
        self.ventana.hide()

    def abrir_csv(self):
        self.ventana_csv = QtWidgets.QDialog()
        self.ctrl_csv = ControladorCSV(self.ventana_csv, self.ventana)
        self.ventana_csv.show()
        self.ventana.hide()

    def abrir_historial(self):
        self.ventana_historial = QtWidgets.QWidget()
        self.ctrl_historial = ControladorHistorial(self.ventana_historial, self.ventana)
        self.ventana_historial.show()
        self.ventana.hide()

    def cerrar_sesion(self):
        self.ventana.close()
        print("Sesión cerrada")