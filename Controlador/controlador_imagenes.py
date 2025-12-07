import csv 
import math
from datetime import datetime 
import unicodedata 
import numpy as np 
import cv2 
import nibabel as nib 
import pydicom
from PyQt5 import QtWidgets, QtGui, QtCore
import os

from Vista.vista_imagenes import Ui_Imagenes_mdicas
from Modelo.imagenes_model import ModeloImagenes


# Crea una carpeta llamada "resultados" en el proyecto si no existe. 
#Usada para guardar imágenes procesadas y archivos csv.
def ensure_results_folder():
    folder = os.path.join(os.getcwd(), "resultados")
    os.makedirs(folder, exist_ok=True)
    return folder


# Normaliza cualquier imagen numérica a rango uint8 (0-255)
# para poder visualizarla en QLabel o guardarla con cv2.
def normalize_to_uint8(img):
    if img is None:
        return None

    a = np.asarray(img, dtype=np.float32)

    # Si la imagen es constante, devolver una imagen negra.
    if np.nanmax(a) == np.nanmin(a):
        return np.zeros(a.shape, dtype=np.uint8)

    mn = np.nanmin(a)
    mx = np.nanmax(a)
    out = (a - mn) / (mx - mn)
    out = (out * 255.0).astype(np.uint8)
    return out


class ControladorImagenes:

    # Constructor: inicializa UI, modelo y estados internos.
    # Conecta botones y sliders.
    def __init__(self, ventana_imagenes, ventana_dashboard):
        self.ventana = ventana_imagenes
        self.dashboard = ventana_dashboard

        self.ui = Ui_Imagenes_mdicas()
        self.ui.setupUi(self.ventana)

        # Modelo que almacena imagen y cortes
        self.modelo = ModeloImagenes()

        # Variables de estado
        self.current_file = None
        self.current_tipo = None   # 'dicom', 'nii', 'convencional'
        self.imagen_procesada = None

        # Llenar combobox de opciones JPG/PNG
        try:
            self.ui.boxprocesamiento_jpgpng.clear()
            self.ui.boxprocesamiento_jpgpng.addItems([
                "Binarización",
                "Detección de bordes",
                "Filtración Gaussiana",
                "Normalizado",
                "Umbralización",
                "Dilatación"
            ])
        except Exception:
            pass

        # Conexión de botones
        self.ui.btnCargarImagenMedica.clicked.connect(self.cargar_imagen)
        self.ui.but_jpgpng.clicked.connect(self.aplicar_transformacion_jpgpng)
        self.ui.btnGuardarImagen.clicked.connect(self.guardar_imagen)
        self.ui.btnvolverimagenes.clicked.connect(self.volver_menu)

        # Conexión sliders para cortes 3D
        self.ui.Slideraxial.valueChanged.connect(self.actualizar_corte_axial)
        self.ui.Slidercoronal.valueChanged.connect(self.actualizar_corte_coronal)
        self.ui.Slidersagital.valueChanged.connect(self.actualizar_corte_sagital)

    # Carga una serie completa de archivos DICOM desde la carpeta
    # donde se encuentra el archivo seleccionado.
    # Devuelve volumen 3D y metadatos.
    def load_dicom_series_from_file(self, filepath):
        folder = os.path.dirname(filepath)
    
        # Buscar todos los .dcm de la carpeta
        files = [
            os.path.join(folder, f) for f in os.listdir(folder)
            if f.lower().endswith('.dcm')
        ]
    
        dicoms = []
        for f in files:
            try:
                ds = pydicom.dcmread(f, force=True)
                if hasattr(ds, 'PixelData'):
                    dicoms.append(ds)
            except:
                pass
    
        # Si solo hay uno, probablemente es un 2D → no es volumen
        if len(dicoms) <= 1:
            return None, {}
        
        # Ordenar por InstanceNumber para evitar cortes desorganizados
        dicoms_sorted = sorted(dicoms, key=lambda d: int(getattr(d, "InstanceNumber", 0)))
    
        slices = []
        for ds in dicoms_sorted:
            arr = ds.pixel_array.astype(np.float32)
    
            # Corregir MONOCHROME1 (invertido)
            if getattr(ds, 'PhotometricInterpretation', '').upper() == 'MONOCHROME1':
                arr = np.max(arr) - arr
    
            # Asegurar forma correcta
            try:
                arr = arr.reshape(ds.Rows, ds.Columns)
            except:
                pass
    
            slices.append(arr)
    
        # Crear volumen (Z, Y, X)
        vol = np.stack(slices, axis=0)
    
        # Obtener slope/intercept (pueden ser HU)
        first = dicoms_sorted[0]
        slope = float(getattr(first, 'RescaleSlope', 1.0))
        intercept = float(getattr(first, 'RescaleIntercept', 0.0))
    
        # Aplicar calibración
        if slope != 1.0 or intercept != 0.0:
            vol = vol * slope + intercept
    
        # Metadatos relevantes
        meta = {
            'PatientID': str(getattr(first, 'PatientID', 'N/A')),
            'PatientName': str(getattr(first, 'PatientName', 'N/A')),
            'StudyInstanceUID': str(getattr(first, 'StudyInstanceUID', 'N/A')),
            'StudyDescription': str(getattr(first, 'StudyDescription', 'N/A')),
            'StudyDate': str(getattr(first, 'StudyDate', 'N/A')),
            'Modality': str(getattr(first, 'Modality', 'N/A')),
            'RescaleSlope': slope,
            'RescaleIntercept': intercept
        }
    
        return vol, meta


    
    # Carga volumen NIfTI, lo transpone según convención deseada,
    # y genera metadatos básicos.
    
    def load_nifti_volume(self, ruta):
        nii = nib.load(ruta)
        data = nii.get_fdata()

        # Manejo de 3D y 4D
        if data.ndim == 3:
            vol = np.transpose(data, (2, 1, 0))
        elif data.ndim == 4:
            vol = np.transpose(data[:, :, :, 0], (2, 1, 0))
        else:
            raise ValueError("NIfTI con dimensiones no soportadas")

        meta = {
            'PatientID': 'N/A',
            'PatientName': 'N/A',
            'StudyInstanceUID': os.path.basename(ruta),
            'StudyDescription': str(getattr(nii, 'header', {}).get('descrip', '')),
            'StudyDate': 'N/A',
            'Modality': 'NIfTI'
        }

        return vol, meta

    
    # Normaliza opciones de texto (quita tildes, espacios, may/min)
    # para comparar fácilmente en procesos JPG/PNG
    def _normalize_option(self, s: str):
        if s is None:
            return ''

        s2 = s.strip().lower()
        s2 = ''.join(
            c for c in unicodedata.normalize('NFD', s2)
            if unicodedata.category(c) != 'Mn'
        )
        s2 = s2.replace(' ', '')
        return s2

    
    # Carga imágenes de cualquier tipo: DICOM, NIfTI y JPG/PNG.
    # Muestra datos y activa sliders para volúmenes.
    
    def cargar_imagen(self):
        ruta, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.ventana,
            "Abrir Imagen",
            "",
            "Archivos Médicos (*.dcm *.nii *.nii.gz *.jpg *.png);;Todos (*.*)"
        )
        if not ruta:
            return
        
        # Mostrar ruta en la UI
        self.ui.lblrtaArchivoC.setText(os.path.basename(ruta))
        self.ui.lblrtaArchivoC.setText(os.path.basename(ruta))

        self.current_file = ruta
        ext = os.path.splitext(ruta)[1].lower()

        try:
            # ---------- CARGAR DICOM ----------
            if ext == '.dcm':
                vol, meta = self.load_dicom_series_from_file(ruta)

                # Caso: solo 1 DICOM ---> no es volumen
                if vol is None:
                    QtWidgets.QMessageBox.information(
                        self.ventana,
                        "DICOM 2D",
                        "Archivo DICOM 2D detectado — no se muestra (se requieren series 3D)."
                    )
                    self.current_tipo = None
                    self.modelo.imagen = None
                    return

                self.modelo.imagen = vol
                self.modelo.metadata = meta
                self.current_tipo = 'dicom'

                # Rellenar metadatos en UI y CSV
                self._rellenar_metadatos(meta, ruta)

                # Configurar sliders y mostrar cortes
                self._setup_volume_sliders_and_display(vol)
                self.ui.lblrtaEstado.setText("Serie DICOM 3D cargada")
                return

            # ---------- CARGAR NIfTI ----------
            if ext in ('.nii', '.gz'):
                vol, meta = self.load_nifti_volume(ruta)
                self.modelo.imagen = vol
                self.modelo.metadata = meta
                self.current_tipo = 'nii'

                self._rellenar_metadatos(meta, ruta)
                self._setup_volume_sliders_and_display(vol)
                self.ui.lblrtaEstado.setText("NIfTI cargado")
                return

            # ---------- CARGAR JPG/PNG ----------
            if ext in ('.jpg', '.jpeg', '.png'):
                img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    raise ValueError("No se pudo leer la imagen (cv2 returned None)")

                self.modelo.imagen = img
                self.current_tipo = 'convencional'

                # Mostrar imagen en la UI
                img8 = normalize_to_uint8(img)
                self._show_in_label(img8, self.ui.lbl_jpgpng)

                # Desactivar sliders y limpiar cortes
                self._reset_sliders()
                self._clear_volume_labels()

                self.ui.lblrtaEstado.setText("Imagen JPG/PNG cargada")
                return

            # Si la extensión no está soportada
            QtWidgets.QMessageBox.warning(
                self.ventana,
                "Formato no soportado",
                f"Extensión {ext} no soportada."
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(self.ventana, "Error al cargar", str(e))


    # Configura sliders para moverse en Z, Y y X con cortes 3D.  
    def _setup_volume_sliders_and_display(self, vol):
        if vol is None or vol.ndim != 3:
            return

        z, y, x = vol.shape

        # Slider axial (recorrido del eje Z)
        self.ui.Slideraxial.setMinimum(0)
        self.ui.Slideraxial.setMaximum(max(0, z - 1))
        self.ui.Slideraxial.setValue(z // 2)

        # Slider coronal (eje Y)
        self.ui.Slidercoronal.setMinimum(0)
        self.ui.Slidercoronal.setMaximum(max(0, y - 1))
        self.ui.Slidercoronal.setValue(y // 2)

        # Slider sagital (eje X)
        self.ui.Slidersagital.setMinimum(0)
        self.ui.Slidersagital.setMaximum(max(0, x - 1))
        self.ui.Slidersagital.setValue(x // 2)

        # Mostrar cortes iniciales
        self.actualizar_corte_axial()
        self.actualizar_corte_coronal()
        self.actualizar_corte_sagital()

  
    # Rellena metadatos en la UI y crea CSV de registro.
    def _rellenar_metadatos(self, metadata: dict, ruta: str):
        pid = metadata.get('PatientID') or metadata.get('ID Paciente') or 'N/A'
        pname = metadata.get('PatientName') or metadata.get('Nombre') or 'N/A'
        studyuid = metadata.get('StudyInstanceUID') or metadata.get('StudyUID') or os.path.basename(ruta)
        desc = metadata.get('StudyDescription') or metadata.get('Descripción') or ''
        date = metadata.get('StudyDate') or metadata.get('Fecha') or ''
        modality = metadata.get('Modality') or metadata.get('Modalidad') or metadata.get('tipo') or 'N/A'

        # Mostrar en etiquetas
        try:
            self.ui.lbl_IDpaciente.setText(str(pid))
            self.ui.lbl_nombre.setText(str(pname))
            self.ui.lbl_IDU.setText(str(studyuid))
            self.ui.lbl_desc.setText(str(desc))
            self.ui.lbl_fecha.setText(str(date))
            self.ui.lbl_mod.setText(str(modality))
        except Exception:
            pass

        # Guardar archivo CSV individual
        folder = ensure_results_folder()
        base = os.path.splitext(os.path.basename(ruta))[0]
        t = datetime.now().strftime("%Y%m%d_%H%M%S")

        single_csv = os.path.join(folder, f"{base}_metadata_{t}.csv")
        try:
            with open(single_csv, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['Campo', 'Valor'])
                w.writerow(['PatientID', pid])
                w.writerow(['PatientName', pname])
                w.writerow(['StudyUID', studyuid])
                w.writerow(['StudyDescription', desc])
                w.writerow(['StudyDate', date])
                w.writerow(['Modality', modality])
        except Exception as e:
            print("Error guardando CSV individual:", e)

        # Agregar registro al CSV consolidado
        master = os.path.join(folder, 'estudios.csv')
        exists = os.path.exists(master)
        try:
            with open(master, 'a', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                if not exists:
                    w.writerow([
                        'timestamp', 'archivo', 'PatientID', 'PatientName',
                        'StudyUID', 'StudyDescription', 'StudyDate', 'Modality'
                    ])
                w.writerow([
                    t, os.path.basename(ruta), pid, pname,
                    studyuid, desc, date, modality
                ])
        except Exception as e:
            print("Error appending master CSV:", e)

    # Muestra una imagen 2D normalizada dentro de un QLabel.
    def _show_in_label(self, img2d, label_widget):
        if img2d is None or img2d.ndim != 2:
            return

        img8 = normalize_to_uint8(img2d)
        h, w = img8.shape

        # Convertir a QImage y mostrarlo
        try:
            qimg = QtGui.QImage(img8.tobytes(), w, h, w, QtGui.QImage.Format_Grayscale8)
            pix = QtGui.QPixmap.fromImage(qimg)
            label_widget.setPixmap(
                pix.scaled(label_widget.width(), label_widget.height(),
                           QtCore.Qt.KeepAspectRatio)
            )
        except Exception as e:
            print("Error creando QImage:", e)

    # Limpia las 3 vistas de cortes del volumen.
    def _clear_volume_labels(self):
        try:
            self.ui.lblImagenAxial.clear()
            self.ui.lblImagenCoronal.clear()
            self.ui.lblImagenSagital.clear()
        except Exception:
            pass

    # Desactiva todos los sliders cuando no hay volumen 3D cargado.
    def _reset_sliders(self):
        try:
            self.ui.Slideraxial.setMinimum(0)
            self.ui.Slideraxial.setMaximum(0)
            self.ui.Slideraxial.setValue(0)

            self.ui.Slidercoronal.setMinimum(0)
            self.ui.Slidercoronal.setMaximum(0)
            self.ui.Slidercoronal.setValue(0)

            self.ui.Slidersagital.setMinimum(0)
            self.ui.Slidersagital.setMaximum(0)
            self.ui.Slidersagital.setValue(0)
        except Exception:
            pass

    # Actualiza corte axial (transversal) del volumen.
    def actualizar_corte_axial(self):
        vol = getattr(self.modelo, 'imagen', None)
        if vol is None or getattr(vol, 'ndim', None) != 3:
            return

        idx = int(self.ui.Slideraxial.value())
        slice2d = self.modelo.obtener_corte_axial(idx)
        self._show_in_label(slice2d, self.ui.lblImagenAxial)

    # Actualiza corte coronal.
    def actualizar_corte_coronal(self):
        vol = getattr(self.modelo, 'imagen', None)
        if vol is None or getattr(vol, 'ndim', None) != 3:
            return

        idx = int(self.ui.Slidercoronal.value())
        slice2d = self.modelo.obtener_corte_coronal(idx)
        self._show_in_label(slice2d, self.ui.lblImagenCoronal)

    # Actualiza corte sagital.
    def actualizar_corte_sagital(self):
        vol = getattr(self.modelo, 'imagen', None)
        if vol is None or getattr(vol, 'ndim', None) != 3:
            return

        idx = int(self.ui.Slidersagital.value())
        slice2d = self.modelo.obtener_corte_sagital(idx)
        self._show_in_label(slice2d, self.ui.lblImagenSagital)

    # Mensaje informativo para procesamientos JPG/PNG.
    def _info_procesar_general(self):
        QtWidgets.QMessageBox.information(
            self.ventana,
            "Procesar",
            "Usa el selector y el botón Aplicar para JPG/PNG en la parte inferior."
        )

    # Aplica procesamiento básico a imágenes JPG/PNG:
    # binarización, bordes, filtro gaussiano, etc.
    def aplicar_transformacion_jpgpng(self):
        # Validar que es imagen convencional
        if getattr(self.modelo, 'imagen', None) is None or self.current_tipo != 'convencional':
            QtWidgets.QMessageBox.warning(
                self.ventana, "Aviso", "Primero cargue una imagen JPG/PNG."
            )
            return

        # Opción seleccionada por el usuario
        raw = self.ui.boxprocesamiento_jpgpng.currentText()
        opcion = self._normalize_option(raw)

        img = self.modelo.imagen.copy()
        if img.dtype != np.uint8:
            img = normalize_to_uint8(img)

        try:
            # Binarización por umbral fijo
            if opcion in ('binarizacion', 'binarizacion', 'binarizacion'):
                _, out = cv2.threshold(img, 128, 255, cv2.THRESH_BINARY)

            # Detección de bordes con Canny
            elif opcion in ('detecciondebordes', 'detecciondebordes', 'detenciondebordes'):
                out = cv2.Canny(img, 50, 150)

            # Filtro Gaussiano
            elif opcion in ('filtraciongaussiana', 'filtrado', 'filtracion', 'gaussiana'):
                out = cv2.GaussianBlur(img, (5, 5), 0)

            # Normalización
            elif opcion in ('normalizado', 'normalizar'):
                out = normalize_to_uint8(img)

            # Umbralización Otsu
            elif opcion in ('umbralizacion', 'umbralizacion', 'otsu', 'umbral'):
                _, out = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Dilatación morfológica
            elif opcion in ('dilatacion', 'dilatacion', 'dilat'):
                kernel = np.ones((5, 5), np.uint8)
                out = cv2.dilate(img, kernel, iterations=1)

            else:
                QtWidgets.QMessageBox.warning(
                    self.ventana, "Opción desconocida", f"Opción: {raw}"
                )
                return

        except Exception as e:
            QtWidgets.QMessageBox.critical(self.ventana, "Error procesando", str(e))
            return

        # Guardar resultado temporal y mostrarlo
        self.imagen_procesada = out
        self.modelo.imagen = out
        self._show_in_label(out, self.ui.lbl_jpgpng)
        self.ui.lblrtaEstado.setText(f"Aplicada: {raw}")

    # Guarda imagen procesada (JPG/PNG) o cortes del volumen 3D.
    def guardar_imagen(self):
        folder = ensure_results_folder()

        # ----- Guardar imagen procesada convencional -----
        if getattr(self, 'imagen_procesada', None) is not None and self.current_tipo == 'convencional':
            t = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(folder, f"imagen_procesada_{t}.png")

            try:
                cv2.imwrite(path, normalize_to_uint8(self.imagen_procesada))
                QtWidgets.QMessageBox.information(
                    self.ventana, "Guardado", f"Imagen guardada en:\n{path}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.ventana, "Error guardando", str(e))
            return

        # ----- Guardar cortes de volumen 3D -----
        vol = getattr(self.modelo, 'imagen', None)
        if vol is not None and getattr(vol, 'ndim', None) == 3:
            z_idx = int(self.ui.Slideraxial.value())
            y_idx = int(self.ui.Slidercoronal.value())
            x_idx = int(self.ui.Slidersagital.value())

            axial = self.modelo.obtener_corte_axial(z_idx)
            coronal = self.modelo.obtener_corte_coronal(y_idx)
            sagital = self.modelo.obtener_corte_sagital(x_idx)

            t = datetime.now().strftime("%Y%m%d_%H%M%S")
            fn_ax = os.path.join(folder, f"axial_{t}.png")
            fn_cor = os.path.join(folder, f"coronal_{t}.png")
            fn_sag = os.path.join(folder, f"sagital_{t}.png")

            try:
                cv2.imwrite(fn_ax, normalize_to_uint8(axial))
                cv2.imwrite(fn_cor, normalize_to_uint8(coronal))
                cv2.imwrite(fn_sag, normalize_to_uint8(sagital))

                QtWidgets.QMessageBox.information(
                    self.ventana,
                    "Guardado",
                    f"Cortes guardados:\n{fn_ax}\n{fn_cor}\n{fn_sag}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.ventana, "Error guardando", str(e))
            return

        # Si no hay nada para guardar
        QtWidgets.QMessageBox.warning(
            self.ventana, "Guardar", "No hay datos listos para guardar."
        )

    # Vuelve al menú principal (dashboard)
    def volver_menu(self):
        self.ventana.close()
        self.dashboard.show()
