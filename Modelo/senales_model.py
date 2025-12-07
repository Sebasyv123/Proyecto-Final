import os
import numpy as np
import pandas as pd
from scipy.io import loadmat

class ModeloSenales:
    def __init__(self):
        self.senal = None
        self.fs = 250  # Frecuencia de muestreo (ajustar si es diferente)
        self.nombre_archivo = ""

    def cargar_senal(self, ruta):
        """
        Carga el archivo .mat. Si es 3D (Canales x Tiempo x Trials),
        calcula el PROMEDIO de los trials para obtener una señal limpia 2D.
        """
        try:
            self.nombre_archivo = os.path.basename(ruta)
            print(f"--- INTENTANDO CARGAR: {self.nombre_archivo} ---")
            
            try:
                data = loadmat(ruta)
            except NotImplementedError:
                print("ERROR CRÍTICO: El archivo es MATLAB v7.3 (HDF5). Guardelo como 'v7' en Matlab o use h5py.")
                return None
            except Exception as e:
                print(f"Error de lectura Scipy: {e}")
                return None

            # Buscar la variable que no sea interna (las que empiezan con __)
            keys = [k for k in data.keys() if not k.startswith('__')]
            if not keys:
                print("El archivo no tiene variables válidas.")
                return None
            
            # Tomamos la primera variable encontrada
            raw_senal = data[keys[0]]
            print(f"Variable cargada: '{keys[0]}'. Forma original: {raw_senal.shape}")

            # --- CORRECCIÓN DE FORMA (SHAPE FIX) ---
            # 1. Eliminar dimensiones vacías (ej: (1, 2000, 1) -> (2000,))
            self.senal = np.squeeze(raw_senal)

            # 2. Si quedó 1D (solo un canal), convertir a 2D (1, N)
            if self.senal.ndim == 1:
                self.senal = self.senal.reshape(1, -1)

            # 3. Si es 3D (ej: Canales x Tiempo x Trials), PROMEDIAR los trials
            elif self.senal.ndim > 2:
                print(f"Señal 3D detectada {self.senal.shape}. Promediando todos los trials (ERP)...")
                # axis=2 suele ser los 'Trials' en formato (Canales, Puntos, Trials)
                self.senal = np.mean(self.senal, axis=2) 

            # 4. Asegurar orientación (Canales, Puntos). Asumimos que hay más Puntos que Canales.
            if self.senal.shape[0] > self.senal.shape[1]:
                print("Transponiendo matriz para que sea (Canales x Tiempo)...")
                self.senal = self.senal.T

            print(f"FORMA FINAL PROCESADA: {self.senal.shape}")
            return self.senal

        except Exception as e:
            print(f"Error inesperado al cargar: {e}")
            return None

    def obtener_num_canales(self):
        if self.senal is not None:
            return self.senal.shape[0]
        return 0

    def obtener_datos_canal(self, canal_idx):
        if self.senal is not None and 0 <= canal_idx < self.senal.shape[0]:
            return self.senal[canal_idx, :]
        return None

    def calcular_fft_canal(self, canal_idx):
        if self.senal is None:
            return None, None
            
        y = self.senal[canal_idx, :]
        N = len(y)
        
        # Calcular FFT
        freqs = np.fft.rfftfreq(N, d=1/self.fs)
        magnitud = np.abs(np.fft.rfft(y))
        
        return freqs, magnitud

    def calcular_fft_todos(self):
        """
        Calcula la frecuencia dominante para TODOS los canales.
        """
        if self.senal is None:
            return None

        resultados = []
        num_canales = self.senal.shape[0]

        for canal in range(num_canales):
            freqs, magnitudes = self.calcular_fft_canal(canal)
            
            if freqs is None or len(freqs) == 0:
                continue

            # Evitar componente DC (índice 0)
            if len(magnitudes) > 1:
                idx_max = np.argmax(magnitudes[1:]) + 1 
                
                # PROTECCIÓN CONTRA INDEX ERROR
                if idx_max < len(freqs):
                    frecuencia_dom = freqs[idx_max]
                    magnitud_max = magnitudes[idx_max]
                else:
                    frecuencia_dom = 0
                    magnitud_max = 0
            else:
                frecuencia_dom = 0
                magnitud_max = 0

            resultados.append([canal, round(frecuencia_dom, 2), round(magnitud_max, 2)])

        df = pd.DataFrame(resultados, columns=["Canal", "Frecuencia Dom (Hz)", "Magnitud"])
        return df

    def guardar_fft_csv(self, df):
        if df is not None:
            folder = "resultados"
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            base_name = os.path.splitext(self.nombre_archivo)[0]
            # Limpiar nombre de archivo
            base_name = "".join([c for c in base_name if c.isalnum() or c in (' ', '-', '_')]).strip()
            
            nombre_csv = f"{folder}/FFT_Analisis_{base_name}.csv"
            df.to_csv(nombre_csv, index=False)
            return nombre_csv
        return None

    def calcular_estadisticas_canal(self, canal_idx):
        data = self.obtener_datos_canal(canal_idx)
        if data is not None:
            return np.std(data), np.mean(data)
        return 0, 0