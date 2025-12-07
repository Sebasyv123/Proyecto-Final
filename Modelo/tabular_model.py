import pandas as pd

class ModeloTabular:
    def __init__(self):
        self.df = None

    def cargar_csv(self, ruta):
        #Carga el CSV como un dataframe de pandas
        try:
            self.df = pd.read_csv(ruta)
            return self.df
        except Exception as e:
            print(f"Error al cargar CSV: {e}")
            return None

    def obtener_columnas(self):
        #Devuelve una lista de columnas
        if self.df is not None:
            return self.df.columns.tolist()
        return []

    def obtener_columna_datos(self, nombre_columna):
        #Devuelve la información de una columna específica para graficar
        if self.df is not None and nombre_columna in self.df.columns:
            return self.df[nombre_columna]
        return None