# ============================================================
# MODELO DE IMÁGENES MÉDICAS

import os
import csv
import pydicom
import numpy as np
import cv2
import nibabel as nib


class ModeloImagenes:
    """
    Modelo encargado de cargar, procesar y extraer información de:
    - Imágenes médicas (DICOM, NIFTI).
    - Imágenes convencionales (JPG/PNG).

    También soporta:
    - Conversión a escala Hounsfield (HU) para tomografías.
    - Obtención de cortes axiales, sagitales y coronales.
    - Procesamiento básico con OpenCV.
    """

    def __init__(self):
        self.imagen = None
        self.metadata = {}
        self.tipo = None  # dicom / nii / convencional

    # --------------------------------------------------------
    # Cargar imágenes de cualquier tipo
    # --------------------------------------------------------
    def cargar_imagen(self, ruta: str):
        """Carga DICOM, NIFTI o imágenes convencionales."""

        if not os.path.exists(ruta):
            raise FileNotFoundError(f"No existe el archivo: {ruta}")

        ext = ruta.lower()

        if ext.endswith(".dcm"):
            return self._cargar_dicom(ruta)

        elif ext.endswith((".nii", ".nii.gz")):
            return self._cargar_nifti(ruta)

        elif ext.endswith((".png", ".jpg", ".jpeg")):
            return self._cargar_imagen_convencional(ruta)

        else:
            raise ValueError("Formato de imagen no soportado.")

    # --------------------------------------------------------
    # Carga y procesamiento DICOM
    # --------------------------------------------------------
    def _cargar_dicom(self, ruta):
        """Carga un archivo DICOM y lo convierte a HU si aplica."""

        ds = pydicom.dcmread(ruta)
        self.metadata = self._extraer_metadata_dicom(ds)
        self.tipo = "dicom"

        if not hasattr(ds, "pixel_array"):
            raise ValueError("El archivo DICOM no contiene datos de imagen.")

        # Conversión a HU
        self.imagen = self._convertir_hounsfield(ds)

        return self.imagen, self.metadata

    def _extraer_metadata_dicom(self, ds):
        """Extrae metadatos básicos de un archivo DICOM."""

        tags = {
            "PatientID": "ID Paciente",
            "PatientName": "Nombre",
            "StudyDate": "Fecha",
            "Modality": "Modalidad",
            "StudyDescription": "Descripción"
        }

        return {nombre: str(getattr(ds, key, "No disponible"))
                for key, nombre in tags.items()}

    def _convertir_hounsfield(self, ds):
        """Convierte una imagen DICOM a unidades Hounsfield (HU)."""

        img = ds.pixel_array.astype(np.int16)
        slope = getattr(ds, "RescaleSlope", 1)
        intercept = getattr(ds, "RescaleIntercept", 0)

        return img * slope + intercept

    # --------------------------------------------------------
    # Carga NIFTI
    # --------------------------------------------------------
    def _cargar_nifti(self, ruta):
        """Carga un archivo NIFTI (.nii o .nii.gz)."""

        nii = nib.load(ruta)
        self.imagen = nii.get_fdata()
        self.metadata = {"tipo": "NIFTI"}
        self.tipo = "nii"

        return self.imagen, self.metadata

    # --------------------------------------------------------
    # Carga JPG/PNG
    # --------------------------------------------------------
    def _cargar_imagen_convencional(self, ruta):
        """Carga imágenes JPG/PNG en escala de grises."""

        img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError("No se pudo cargar la imagen JPG/PNG.")

        self.imagen = img
        self.metadata = {"tipo": "imagen convencional"}
        self.tipo = "convencional"

        return self.imagen, self.metadata

    # --------------------------------------------------------
    # Cortes 3D
    # --------------------------------------------------------
    def _validar_3d(self):
        if self.imagen is None or self.imagen.ndim != 3:
            raise ValueError("La imagen cargada no es una imagen 3D.")

    def obtener_corte_axial(self, index):
        self._validar_3d()
        return self.imagen[index, :, :]

    def obtener_corte_sagital(self, index):
        self._validar_3d()
        return self.imagen[:, :, index]

    def obtener_corte_coronal(self, index):
        self._validar_3d()
        return self.imagen[:, index, :]

    # --------------------------------------------------------
    # Procesamiento OpenCV
    # --------------------------------------------------------
    def normalizar(self):
        """Normaliza la imagen al rango 0-255."""

        if self.imagen is None:
            raise ValueError("Debe cargar una imagen primero.")

        img = self.imagen.astype(np.float32)
        img_norm = (img - img.min()) / (img.max() - img.min())
        self.imagen = (img_norm * 255).astype(np.uint8)
        return self.imagen

    def filtrar_gauss(self, ksize=5):
        if self.imagen is None:
            raise ValueError("Debe cargar una imagen primero.")

        self.imagen = cv2.GaussianBlur(self.imagen, (ksize, ksize), 0)
        return self.imagen

    def binarizar(self, umbral=128):
        if self.imagen is None:
            raise ValueError("Debe cargar una imagen primero.")

        _, bin_img = cv2.threshold(self.imagen, umbral, 255, cv2.THRESH_BINARY)
        self.imagen = bin_img
        return bin_img

    def detectar_bordes(self):
        if self.imagen is None:
            raise ValueError("Debe cargar una imagen primero.")

        self.imagen = cv2.Canny(self.imagen, 50, 150)
        return self.imagen

    # --------------------------------------------------------
    # Guardar metadata en CSV
    # --------------------------------------------------------
    def guardar_metadata_csv(self, ruta_csv):
        """Guarda metadatos de la imagen en un archivo CSV."""

        os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)

        with open(ruta_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Campo", "Valor"])
            for k, v in self.metadata.items():
                writer.writerow([k, v])


