from PyQt5 import QtWidgets
from Vista.vista_historial import Ui_Form

class ControladorHistorial(QtWidgets.QWidget):
    def __init__(self, modelo):
        super().__init__()
        self.modelo = modelo  # instancia de DatabaseManager
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Conectar botones
        self.ui.btnVer.clicked.connect(self.cargar_registros)
        self.ui.btnEliminar.clicked.connect(self.eliminar_todo)
        self.ui.btnvolverhistorial.clicked.connect(self.close)

        # Cargar registros automáticamente al abrir
        self.cargar_registros()

    def cargar_registros(self):
        eventos = self.modelo.obtener_eventos()  # Lista de diccionarios
        registros = []

        for idx, evento in enumerate(eventos, start=1):
            registros.append([
                idx,
                evento.get("usuario", ""),
                evento.get("fecha", "").strftime("%Y-%m-%d %H:%M:%S") if evento.get("fecha") else "",
                evento.get("tipo", ""),
                evento.get("ruta", "")
            ])

        headers = ["ID", "Usuario", "Fecha", "Actividad", "Ruta"]

        # Limpiar y cargar tabla
        self.ui.tableRegistros.clear()
        self.ui.tableRegistros.setRowCount(len(registros))
        self.ui.tableRegistros.setColumnCount(len(headers))
        self.ui.tableRegistros.setHorizontalHeaderLabels(headers)

        for row_idx, fila in enumerate(registros):
            for col_idx, valor in enumerate(fila):
                self.ui.tableRegistros.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(str(valor)))

    def eliminar_todo(self):
        # Eliminar todos los eventos en MongoDB
        self.modelo.db["eventos"].delete_many({})
        self.cargar_registros()  # refrescar tabla
