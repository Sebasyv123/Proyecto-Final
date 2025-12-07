from PyQt5 import QtCore, QtGui, QtWidgets
import cv2
import os
from Modelo.database_manager import DatabaseManager

class ControladorLogin:
    def __init__(self, ventana_login, modelo):
        self.ventana_login = ventana_login
        self.ui = ventana_login.ui
        self.modelo = modelo

        self.ui.lblmensaje.setVisible(False)

        # Conectar botones
        self.ui.btnIngresar.clicked.connect(self.login)
        self.ui.btnSalir.clicked.connect(self.ventana_login.close)

    def login(self):
        usuario = self.ui.lnputUsuario.text()
        contrasena = self.ui.InputContrasena.text()

        if self.modelo.validar_usuario(usuario, contrasena):
            self.ui.lblmensaje.setVisible(False)
        
            # Crear sesión en la base de datos
            self.db_historial = DatabaseManager()
            self.sesion_id = self.db_historial.crear_sesion(usuario)
        
            self.usuario_actual = usuario
            self.ventana_login.close()
            # Abrimos primero captura
            self.abrir_captura(usuario)

        else:
            self.ui.lblmensaje.setText("Usuario o contraseña incorrecta")
            self.ui.lblmensaje.setStyleSheet("color: red; font-weight: bold;")
            self.ui.lblmensaje.setVisible(True)


    #Actualizar stream de cáramara
    def actualizar_stream(self):
        #Se obtiene un frame de la cámara
        ret, frame = self.cap.read()
        if not ret:
            return

        #Se convierte a RGB para que Qt lo pueda mostrar
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        #Se crea un QImage a partir del frame
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QtGui.QImage(frame_rgb.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)

        #Se convierte a QPixmap
        pix = QtGui.QPixmap.fromImage(qimg)

        #Se escala la imagen al tamaño del label
        pix = pix.scaled(self.ui_captura.lblStream.width(),
                         self.ui_captura.lblStream.height(),
                         QtCore.Qt.KeepAspectRatio)

        #Se muestra en el label del stream
        self.ui_captura.lblStream.setPixmap(pix)

        #Se guarda el frame actual
        self.frame_actual = frame

    #Abrir vista de captura
    def abrir_captura(self, usuario):
        #Se importa y crea la vista de captura
        from Vista.Captura import Ui_Dialog
        self.ventana_captura = QtWidgets.QDialog()
        self.ui_captura = Ui_Dialog()
        self.ui_captura.setupUi(self.ventana_captura)

        #Se guarda el usuario que inició sesión
        self.usuario_actual = usuario

        #Se conectan los botones de la vista de captura
        self.ui_captura.btnCapturar.clicked.connect(self.capturar_imagen)
        self.ui_captura.btnNuevaCaptura.clicked.connect(self.nueva_captura)
        self.ui_captura.btnGuardartemporal.clicked.connect(self.guardar_temporal)

        #Se inicia la cámara
        self.cap = cv2.VideoCapture(0)

        #Se crea un timer para actualizar el video
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.actualizar_stream)
        self.timer.start(30)

        #Se muestra la ventana de captura
        self.ventana_captura.show()
        #Se conecta el cierre de la ventana con la función que apaga la cámara
        self.ventana_captura.finished.connect(self.cerrar_camara)

    #Capturar imagen
    def capturar_imagen(self):
        #Se verifica si existe un frame disponible
        if hasattr(self, "frame_actual"):
            #Se almacena la imagen capturada en memoria
            self.ultima_imagen = self.frame_actual.copy()

            #Se convierte la imagen a escala de grises
            gris = cv2.cvtColor(self.ultima_imagen, cv2.COLOR_BGR2GRAY)

            #Se convierte a QImage para poder mostrarla
            h, w = gris.shape
            qimg = QtGui.QImage(gris.data, w, h, w, QtGui.QImage.Format_Grayscale8)

            #Se crea un pixmap ajustado al label
            pix = QtGui.QPixmap.fromImage(qimg).scaled(
                self.ui_captura.lblImagenCapturada.width(),
                self.ui_captura.lblImagenCapturada.height(),
                QtCore.Qt.KeepAspectRatio)

            #Se muestra la imagen capturada
            self.ui_captura.lblImagenCapturada.setPixmap(pix)

            #Se actualiza el estado en pantalla
            self.ui_captura.lblestadodecamara.setText("Imagen capturada")

    #Reiniciar captura
    def reiniciar_captura(self):
        #Se borra la imagen almacenada
        self.ultima_imagen = None

        #Se limpia el label de la captura
        self.ui_captura.lblImagenCapturada.clear()

        #Se muestra un estado informativo
        self.ui_captura.lblestadodecamara.setText("Listo para nueva captura")

    #Nueva captura
    def nueva_captura(self):
        #Se limpia la imagen mostrada
        self.ui_captura.lblImagenCapturada.clear()

        #Se informa que puede capturar otra
        self.ui_captura.lblestadodecamara.setText("Listo para nueva captura")

        #Se elimina la imagen almacenada si existe
        if hasattr(self, "ultima_imagen"):
            del self.ultima_imagen
            
    #Se cierra la camara para que no siga prendida luego de salir de la ventana       
    def cerrar_camara(self):
        #Se detiene el timer si existe
        if hasattr(self, "timer"):
            self.timer.stop()
    
        #Se libera la cámara si existe
        if hasattr(self, "cap"):
            self.cap.release()

    #Guardar imagen temporal
    def guardar_temporal(self):
        #Se verifica que haya una imagen capturada
        if not hasattr(self, "ultima_imagen"):
            self.ui_captura.lblestadodecamara.setText("Primero capture la imagen")
            return

        #Se obtiene el nombre ingresado por el usuario
        nombre = self.ui_captura.linenombreimagen.text().strip()

        #Se valida que el nombre no esté vacío
        if nombre == "":
            self.ui_captura.lblestadodecamara.setText("Debe ingresar un nombre")
            return

        #Se crea la carpeta del usuario si no existe
        carpeta = os.path.join("Usuarios", self.usuario_actual)
        os.makedirs(carpeta, exist_ok=True)

        #Se forma la ruta final del archivo
        ruta = os.path.join(carpeta, f"{nombre}.png")

        #Se convierte la imagen a escala de grises y se guarda
        gris = cv2.cvtColor(self.ultima_imagen, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(ruta, gris)

        #Se muestra un mensaje de confirmación
        self.ui_captura.lblestadodecamara.setText(f"Imagen guardada: {ruta}")

        #Se detiene el timer y se apaga la cámara
        self.timer.stop()
        self.cap.release()
        self.cerrar_camara()

        #Se cierra la ventana de captura
        self.ventana_captura.close()

        #Se abre el dashboard
        self.abrir_dashboard()
    


    #Abrir dashboard
    def abrir_dashboard(self):
        from Controlador.controlador_dashboard import ControladorDashboard
    
        self.ventana_dashboard = QtWidgets.QMainWindow()
        self.ctrl_dashboard = ControladorDashboard(
            self.ventana_dashboard,
            usuario=self.usuario_actual,
            db_historial=self.db_historial,
            sesion_id=self.sesion_id
        )
        self.ventana_dashboard.show()