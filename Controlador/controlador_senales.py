from PyQt5 import QtWidgets, QtCore
from Vista.senalesbiomedicas import Ui_Senales_biomedicas 
from Modelo.senales_model import ModeloSenales 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np

class ControladorSenales:
    def __init__(self, ventana_senales, ventana_dashboard=None):
        self.ventana = ventana_senales
        self.dashboard = ventana_dashboard # Para volver al menú principal
        self.ui = Ui_Senales_biomedicas()
        self.ui.setupUi(self.ventana)
        
        # Inicializar Modelo
        self.model = ModeloSenales()

        # Inicializar figuras de Matplotlib
        self.iniciar_graficas()

        # Conexiones
        self.ui.btnCargarSenal.clicked.connect(self.cargar_senal)
        self.ui.btnGraficarSenal.clicked.connect(self.graficar_senal)
        self.ui.btngraficarhistograma.clicked.connect(self.graficar_histograma)
        self.ui.btnCerrarsenales.clicked.connect(self.volver_menu)
        

    def iniciar_graficas(self):
        # Layout para gráfica de Señal/Espectro (Arriba)
        self.figura_senal, self.ax_senal = plt.subplots()
        self.canvas_senal = FigureCanvas(self.figura_senal)
        layout_senal = QtWidgets.QVBoxLayout(self.ui.framegraficasenal)
        layout_senal.addWidget(self.canvas_senal)

        # Layout para Histograma (Abajo)
        self.figura_hist, self.ax_hist = plt.subplots()
        self.canvas_hist = FigureCanvas(self.figura_hist)
        layout_hist = QtWidgets.QVBoxLayout(self.ui.framehistograma)
        layout_hist.addWidget(self.canvas_hist)

    def cargar_senal(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ventana, "Cargar .mat", "", "Archivos MAT (*.mat)"
        )
        
        if ruta:
            # Actualizar etiqueta
            self.ui.lblarchivocargadosenal.setText(ruta.split("/")[-1])
            
            # Cargar datos mediante el Modelo
            datos = self.model.cargar_senal(ruta)
            
            if datos is not None:
                self.ui.lblestadoproceso.setText("Archivo cargado.")
                # Actualizar rango del SpinBox basado en número de canales
                num_canales = self.model.obtener_num_canales()
                self.ui.spinBoxsenales.setMinimum(0)
                # Máximo es cantidad-1 (ejemplo: si hay 3 canales → 0,1,2)
                self.ui.spinBoxsenales.setMaximum(max(0, num_canales - 1))
                self.ui.spinBoxsenales.setValue(0)
                
                # --- PROCESAR TABLA AUTOMÁTICAMENTE ---
                # Mostrar tabla y guardar CSV
                self.procesar_fft_tabla()
                
            else:
                self.ui.lblestadoproceso.setText("Error al leer el archivo .mat")

    def graficar_senal(self):
        # Graficar el espectro de frecuencia del canal seleccionado
        idx_canal = self.ui.spinBoxsenales.value()
        
        # Obtener datos FFT para graficar el espectro
        freqs, magnitud = self.model.calcular_fft_canal(idx_canal)
        
        if freqs is not None:
            self.ax_senal.clear()
            self.ax_senal.plot(freqs, magnitud, color='blue')
            self.ax_senal.set_title(f"Espectro de Frecuencia - Canal {idx_canal}")
            self.ax_senal.set_xlabel("Frecuencia (Hz)")
            self.ax_senal.set_ylabel("Magnitud")
            self.ax_senal.grid(True)
            self.canvas_senal.draw()
            self.ui.lblestadoproceso.setText(f"Espectro del Canal {idx_canal} graficado.")
        else:
            self.ui.lblestadoproceso.setText("Cargue una señal primero.")

    def procesar_fft_tabla(self):
        # Calcular la FFT para todos los canales, actualizar la tabla y guarda CSV 
        df = self.model.calcular_fft_todos()
        
        if df is not None:
            # 1. Mostrar en QTableWidget
            self.ui.tablesenal.setRowCount(df.shape[0])
            self.ui.tablesenal.setColumnCount(df.shape[1])
            self.ui.tablesenal.setHorizontalHeaderLabels(df.columns)

            for i in range(df.shape[0]):
                for j in range(df.shape[1]):
                    self.ui.tablesenal.setItem(i, j, QtWidgets.QTableWidgetItem(str(df.iloc[i, j])))
            
            # Ajustar columnas al ancho de la tabla
            self.ui.tablesenal.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

            # 2. Guardar CSV automáticamente 
            ruta_csv = self.model.guardar_fft_csv(df)
            self.ui.lblestadoproceso.setText(f"CSV guardado: {ruta_csv}")

    def graficar_histograma(self):
        # Histograma y Desviación Estándar
        
        idx_canal = self.ui.spinBoxsenales.value()
        
        data_canal = self.model.obtener_datos_canal(idx_canal)
        std_val, mean_val = self.model.calcular_estadisticas_canal(idx_canal)

        if data_canal is not None:
            self.ax_hist.clear()
            # Graficar histograma de los datos
            self.ax_hist.hist(data_canal, bins=30, color='green', alpha=0.7, edgecolor='black')
            
            # Mostrar la desviación estándar en el título
            self.ax_hist.set_title(f"Histograma Canal {idx_canal} | Desv. Est: {std_val:.2f}")
            self.ax_hist.set_ylabel("Frecuencia")
            self.ax_hist.set_xlabel("Amplitud de señal")
            self.canvas_hist.draw()
            self.ui.lblestadoproceso.setText(f"Histograma generado. Std: {std_val:.2f}")
        
    def volver_menu(self):
        self.ventana.close()
        if self.dashboard:
            self.dashboard.show()
