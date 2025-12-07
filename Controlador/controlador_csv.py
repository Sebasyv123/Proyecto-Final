from PyQt5 import QtWidgets
from Vista.vista_CSV import Ui_Dialog
from Modelo.tabular_model import ModeloTabular
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
import os

class ControladorCSV:
    def __init__(self, ventana_csv, ventana_dashboard=None):
        self.ventana = ventana_csv
        self.dashboard = ventana_dashboard
        self.ui = Ui_Dialog()
        self.ui.setupUi(self.ventana)
        
        self.model = ModeloTabular()

        # Configuración de Matplotlib
        # Usamos un estilo más limpio para reportes académicos
        plt.style.use('seaborn-v0_8-whitegrid') 

        # Listas para manejar los 4 espacios
        self.figs = []
        self.axes = []
        self.canvases = []
        self.active_plots = [False, False, False, False] # Para saber cuáles tienen datos

        # Inicializar los 4 espacios
        self.setup_grafica(self.ui.label)
        self.setup_grafica(self.ui.label2)
        self.setup_grafica(self.ui.label3)
        self.setup_grafica(self.ui.label4)

        # Conexiones
        self.ui.btnCargarCSV.clicked.connect(self.cargar_csv)
        self.ui.btnGraficarCSV.clicked.connect(self.graficar_todo)
        self.ui.btnLimpiarGrafica.clicked.connect(self.limpiar)
        self.ui.btnExportarGrafica.clicked.connect(self.exportar_grafica)
        self.ui.btnvolverCSV.clicked.connect(self.volver_menu)

    def setup_grafica(self, label_container):
        # Ajustar fuente global pequeña para que quepa en el dashboard
        plt.rcParams.update({'font.size': 7})
        
        fig = plt.figure(dpi=80) 
        ax = fig.add_subplot(111)
        canvas = FigureCanvas(fig)
        
        self.figs.append(fig)
        self.axes.append(ax)
        self.canvases.append(canvas)

        label_container.setText("")
        layout = QtWidgets.QVBoxLayout(label_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(canvas)

    def cargar_csv(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ventana, "Cargar CSV", "", "CSV Files (*.csv)"
        )
        if ruta:
            df = self.model.cargar_csv(ruta)
            if df is not None:
                self.ui.lblrtaestadoCSV.setText("Archivo cargado. Seleccione variables.")
                columns = self.model.obtener_columnas()
                
                lists = [self.ui.listWidcolumnas, self.ui.listWidcolumnas2, 
                         self.ui.listWidcolumnas3, self.ui.listWidcolumnas4]
                
                for lst in lists:
                    lst.clear()
                    lst.addItems(columns)
                
                self.llenar_tabla(df)
            else:
                self.ui.lblrtaestadoCSV.setText("Error al leer el archivo")

    def llenar_tabla(self, df):
        self.ui.tablaCSV.clear()
        self.ui.tablaCSV.setRowCount(df.shape[0])
        self.ui.tablaCSV.setColumnCount(df.shape[1])
        self.ui.tablaCSV.setHorizontalHeaderLabels(df.columns)

        limit = min(df.shape[0], 100)
        for i in range(limit):
            for j in range(df.shape[1]):
                self.ui.tablaCSV.setItem(i, j, QtWidgets.QTableWidgetItem(str(df.iat[i, j])))

    def graficar_todo(self):
        # Configuraciones: (Widget de lista, Índice de gráfica)
        configs = [
            (self.ui.listWidcolumnas, 0),
            (self.ui.listWidcolumnas2, 1),
            (self.ui.listWidcolumnas3, 2),
            (self.ui.listWidcolumnas4, 3)
        ]

        contador_exitos = 0
        
        # Reiniciamos el estado de plots activos
        self.active_plots = [False] * 4

        for list_widget, idx in configs:
            exito = self._procesar_grafica_individual(list_widget, idx)
            if exito:
                contador_exitos += 1
                self.active_plots[idx] = True
            
        # Actualización CORRECTA del estado
        if contador_exitos > 0:
            self.ui.lblrtaestadoCSV.setText(f"Visualizando {contador_exitos} variable(s)")
            
            # Opcional: Si tienes el label de "Variable Seleccionada", límpialo o pon resumen
            # self.ui.lbl_variable.setText("Dashboard Múltiple")
        else:
            self.ui.lblrtaestadoCSV.setText("Seleccione al menos una variable en las listas")

    def _procesar_grafica_individual(self, list_widget, idx):
        ax = self.axes[idx]
        canvas = self.canvases[idx]
        fig = self.figs[idx]
        
        selected_items = list_widget.selectedItems()
        
        # Si no hay selección, limpiamos ese hueco y retornamos False
        if not selected_items:
            ax.clear()
            ax.axis('off') # Ocultamos los ejes vacíos para que se vea limpio
            canvas.draw()
            return False
            
        columna = selected_items[0].text()
        datos = self.model.obtener_columna_datos(columna)

        if datos is not None:
            ax.clear()
            ax.axis('on') # Reactivamos ejes por si estaban apagados
            try:
                # LÓGICA DE PROCESAMIENTO MEJORADA (Bio/Estadística)
                
                # Intentamos convertir a numérico
                datos_num = pd.to_numeric(datos, errors='coerce')
                es_numerico = datos_num.notna().mean() > 0.8 # Si más del 80% son números

                if es_numerico:
                    # --- CASO 1: VARIABLE NUMÉRICA (Ej. Edad, Glucosa) ---
                    # Usamos gráfico de línea o dispersión.
                    # Se asume que el eje X es el ID del paciente (índice)
                    ax.plot(datos_num, color='#1f77b4', linewidth=1.5, label='Valor')
                    # Relleno suave bajo la curva para darle "estética de reporte moderno"
                    ax.fill_between(range(len(datos_num)), datos_num, alpha=0.1, color='#1f77b4')
                    ax.set_ylabel("Valor")
                    ax.set_xlabel("Índice / ID Paciente")
                    
                else:
                    # --- CASO 2: VARIABLE CATEGÓRICA (Ej. Género, Diagnóstico) ---
                    # ERROR COMÚN: Usar plot() aquí.
                    # SOLUCIÓN CORRECTA: Usar Bar Chart de conteos (Frecuencia)
                    
                    conteos = datos.value_counts()
                    categorias = conteos.index.astype(str)
                    valores = conteos.values
                    
                    # Gráfico de Barras
                    barras = ax.bar(categorias, valores, color='#2ca02c', alpha=0.7)
                    ax.set_ylabel("Frecuencia (n)")
                    
                    # Añadir etiquetas de valor encima de las barras (útil para informes)
                    ax.bar_label(barras, padding=3, fontsize=6)

                # Estilos generales
                titulo = f"{columna}"
                ax.set_title(titulo, fontsize=9, fontweight='bold')
                ax.tick_params(axis='both', labelsize=7)
                ax.grid(True, linestyle='--', alpha=0.5, axis='y') # Solo grid horizontal suele ser más limpio
                
                fig.tight_layout()
                canvas.draw()
                return True
                
            except Exception as e:
                print(f"Error plot {idx}: {e}")
                return False
        return False

    def exportar_grafica(self):
        # Solicitamos carpeta
        carpeta = QtWidgets.QFileDialog.getExistingDirectory(
            self.ventana, "Seleccionar Carpeta para Exportar"
        )
        
        if not carpeta:
            return

        guardados = 0
        
        # Iteramos solo sobre las gráficas que marcamos como ACTIVAS
        for i, (fig, activo) in enumerate(zip(self.figs, self.active_plots)):
            if activo:
                try:
                    # Obtenemos el título del eje para el nombre del archivo
                    ax = fig.get_axes()[0]
                    titulo = ax.get_title()
                    
                    # Limpieza estricta del nombre de archivo
                    # Reemplaza espacios con _ y quita caracteres raros
                    nombre_limpio = "".join(c if c.isalnum() else "_" for c in titulo)
                    
                    # Evitamos sobreescritura si hay nombres iguales agregando índice
                    nombre_archivo = f"{nombre_limpio}_G{i+1}.png"
                    ruta_completa = os.path.join(carpeta, nombre_archivo)
                    
                    fig.savefig(ruta_completa, dpi=150, bbox_inches='tight')
                    guardados += 1
                except Exception as e:
                    print(f"Error exportando gráfica {i}: {e}")

        if guardados > 0:
            self.ui.lblrtaestadoCSV.setText(f"Éxito: {guardados} gráficas exportadas.")
        else:
            self.ui.lblrtaestadoCSV.setText("No había gráficas activas para exportar.")

    def limpiar(self):
        for ax in self.axes:
            ax.clear()
            ax.axis('off') # Ocultar ejes al limpiar
        for canvas in self.canvases:
            canvas.draw()
        
        self.active_plots = [False] * 4
        self.ui.lblrtaestadoCSV.setText("Área de trabajo limpia")
        
        # Limpiar selecciones visuales
        listas = [self.ui.listWidcolumnas, self.ui.listWidcolumnas2, 
                  self.ui.listWidcolumnas3, self.ui.listWidcolumnas4]
        for lst in listas:
            lst.clearSelection()

    def volver_menu(self):
        self.ventana.close()
        if self.dashboard:
            self.dashboard.show()