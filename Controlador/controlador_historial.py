from PyQt5 import QtWidgets
from Vista.vista_historial import Ui_Form

class ControladorHistorial(QtWidgets.QWidget):
    def __init__(self, modelo, ventana_dashboard):
        super().__init__()
        self.modelo = modelo                # DatabaseManager
        self.ventana_dashboard = ventana_dashboard
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Conectar botones
        self.ui.btnVer.clicked.connect(self.cargar_registros)
        self.ui.btnEliminar.clicked.connect(self.eliminar_todo)
        self.ui.btnvolverhistorial.clicked.connect(self.volver_al_dashboard)

        # Cargar registros al abrir
        self.cargar_registros()

    def cargar_registros(self):
        eventos = self.modelo.obtener_eventos()
        registros = []
    
        for idx, evento in enumerate(eventos, start=1):
            fecha = evento.get("fecha_hora_login")  # tu campo de fecha real
            acciones_lista = evento.get("acciones", [])  # lista de botones presionados
    
            # Convertir todos los elementos a string por seguridad
            acciones_str = ", ".join(
                a if isinstance(a, str) else str(a) for a in acciones_lista
            )
    
            registros.append([
                idx,
                evento.get("usuario", ""),
                fecha.strftime("%Y-%m-%d %H:%M:%S") if fecha else "",
                acciones_str,
                evento.get("ruta", "")
            ])
    
        headers = ["ID", "Usuario", "Fecha", "Actividad", "Ruta"]
        self.ui.tableRegistros.setRowCount(len(registros))
        self.ui.tableRegistros.setColumnCount(len(headers))
        self.ui.tableRegistros.setHorizontalHeaderLabels(headers)
    
        for row_idx, fila in enumerate(registros):
            for col_idx, valor in enumerate(fila):
                self.ui.tableRegistros.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(valor)))


    def eliminar_todo(self):
        self.modelo.db["eventos"].delete_many({})
        self.cargar_registros()

    def volver_al_dashboard(self):
        self.close()                       # Cierra la ventana de historial
        self.ventana_dashboard.show() 
