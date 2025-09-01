# CRM Legal - Sistema de Gestión de Casos Legales
# Versión Refactorizada con Sistema de Partes Intervinientes
# main_app.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog, Toplevel
import crm_database as db
import os
import datetime
import time
import sys
import subprocess
import sqlite3
import json
import logging
from tkcalendar import Calendar, DateEntry
import threading
import webbrowser
import re
import urllib.parse
import shutil
import configparser
from typing import Optional, Dict, Any
import date_utils  # Utilidades de fecha para formato argentino
from lazy_loader import create_lazy_module, preload_module
from report_generator_window import ReportGeneratorWindow
from client_dialog_manager import ClientManager
from case_dialog_manager import CaseManager
# --- LAZY LOADING: Módulos pesados se cargan solo cuando se necesitan ---
# Módulos de exportación y documentos
docx_module = create_lazy_module("docx", "docx")
requests_module = create_lazy_module("requests", "requests")
PIL_Image = create_lazy_module("PIL_Image", "PIL.Image")
PIL_ImageTk = create_lazy_module("PIL_ImageTk", "PIL.ImageTk")
plyer_module = create_lazy_module("plyer", "plyer")
pystray_module = create_lazy_module("pystray", "pystray")

# --- BLOQUE DE DEBUG ---
with open("debug_log.txt", "w", encoding="utf-8") as f:
    f.write("Rutas del sistema en el ejecutable:\n")
    f.write("\n".join(sys.path))
    f.write("\n\nVariables de entorno:\n")
    f.write(str(os.environ))
# --- FIN BLOQUE DE DEBUG ---

# --- LAZY LOADING: Módulos pesados se cargan solo cuando se necesitan ---
# IA Analyzer - Solo se carga cuando se usa análisis IA
ia_analyzer = create_lazy_module("ia_analyzer", "ia_analyzer")

# ChromaDB - Solo se carga cuando se usa vectorización
chromadb = create_lazy_module("chromadb", "chromadb")

# --- Imports diferidos para ventanas y diálogos ---
# Estos se importan cuando se necesitan para evitar carga inicial pesada
def get_case_detail_window():
    """Importa CaseDetailWindow solo cuando se necesita"""
    from case_detail_window import CaseDetailWindow
    return CaseDetailWindow

def get_scba_scraper_window():
    """Importa SCBAScraperWindow solo cuando se necesita"""
    from scba_scraper_window import SCBAScraperWindow
    return SCBAScraperWindow

def get_client_manager():
    """Importa ClientManager solo cuando se necesita"""
    from client_dialog_manager import ClientManager
    return ClientManager

def get_partes_dialog_manager():
    """Importa PartesDialogManager solo cuando se necesita"""
    from partes_dialog_manager import PartesDialogManager
    return PartesDialogManager

def get_case_manager():
    """Importa CaseManager solo cuando se necesita"""
    from case_dialog_manager import CaseManager
    return CaseManager

def get_prospect_manager():
    """Importa ProspectManager solo cuando se necesita"""
    from prospect_manager import ProspectManager
    return ProspectManager

def get_report_generator_window():
    """Importa ReportGeneratorWindow solo cuando se necesita"""
    from report_generator_ui import ReportGeneratorWindow
    return ReportGeneratorWindow
def get_contactos_manager():
    """Importa ContactosManagerWindow solo cuando se necesita"""
    from contactos_manager_ui import open_contactos_manager
    return open_contactos_manager


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


class CRMLegalApp:
    # En main_app.py, dentro de la clase CRMLegalApp

    def __init__(self, root):
        self.root = root
        
        # 1. CONFIGURACIÓN INICIAL
        self._load_configuration()
        
        # 2. BASE DE DATOS (CRÍTICO)
        if not self._initialize_database():
            return  # Error crítico, no continuar
        
        # 3. VARIABLES DE ESTADO
        self._initialize_state_variables()
        
        # 4. CONFIGURAR VENTANA Y MENÚS
        self._setup_window_and_menus()
        
        # 5. MANAGERS
        self._initialize_managers()
        
        # 6. WIDGETS UI
        self.create_widgets()
        
        # 7. CARGA DE DATOS
        self._load_initial_data()
        
        # 8. HILOS DE FONDO (ÚLTIMO)
        self._start_background_threads()
        
        # 9. CONFIGURACIÓN FINAL
        self._finalize_setup()

    def _load_configuration(self):
        """Carga la configuración desde config.ini."""
        self.current_user = "Usuario por Defecto"
        try:
            config = configparser.ConfigParser()
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
            if os.path.exists(config_path):
                config.read(config_path)
                if 'app_settings' in config and 'current_user_name' in config['app_settings']:
                    self.current_user = config['app_settings']['current_user_name']
                    print(f"Usuario actual cargado desde config.ini: '{self.current_user}'")
        except Exception as e:
            print(f"Error al leer config.ini: {e}")

    def _setup_window_and_menus(self):
        """Configura la ventana principal y los menús."""
        self.root.title("Legal Practice Management Software             Powered by Legal-IT-Ø")
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.attributes("-zoomed", True)
        
    # --- ¡SECCIÓN DEL MENUBAR RESTAURADA! ---
        menubar = tk.Menu(self.root)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Mostrar Ventana", command=self._mostrar_ventana_callback)
        filemenu.add_separator()
        filemenu.add_command(label="Ocultar a Bandeja", command=self.ocultar_a_bandeja)
        filemenu.add_separator()
        filemenu.add_command(label="Salir", command=self.cerrar_aplicacion_directamente)
        menubar.add_cascade(label="Archivo", menu=filemenu)

        ia_menu = tk.Menu(menubar, tearoff=0)
        ia_menu.add_command(label="Reformular Hechos...", command=self.open_reformular_hechos_dialog)
        menubar.add_cascade(label="Asistente IA", menu=ia_menu)

        prospects_menu = tk.Menu(menubar, tearoff=0)
        prospects_menu.add_command(label="Gestión de Prospectos...", command=self.open_prospects_window)
        menubar.add_cascade(label="Prospectos", menu=prospects_menu)

        contactos_menu = tk.Menu(menubar, tearoff=0)
        contactos_menu.add_command(label="Gestionar Contactos...", command=self._abrir_gestor_de_contactos)
        menubar.add_cascade(label="Contactos", menu=contactos_menu)

        reports_menu = tk.Menu(menubar, tearoff=0)
        reports_menu.add_command(label="Listado de Casos...", command=self._abrir_generador_reportes)
        menubar.add_cascade(label="Reportes", menu=reports_menu)

        modelos_menu = tk.Menu(menubar, tearoff=0)
        modelos_menu.add_command(label="Generar Documento...", command=self._abrir_modelos_escritos)
        modelos_menu.add_separator()
        modelos_menu.add_command(label="Abrir Carpeta de Modelos", command=self._abrir_carpeta_modelos)
        menubar.add_cascade(label="Modelos de Escritos", menu=modelos_menu)

        adminmenu = tk.Menu(menubar, tearoff=0)
        adminmenu.add_command(label="Crear Copia de Seguridad...", command=self.crear_copia_de_seguridad)
        menubar.add_cascade(label="Administración", menu=adminmenu)
    
        self.root.config(menu=menubar)

    def _initialize_database(self):
        """Inicialización crítica de la base de datos."""
        print("--- INICIALIZACIÓN DEL SISTEMA ---")
        self.db_crm = db
        print("Verificando la conexión a la base de datos...")
        
        conn = self.db_crm.connect_db()
        if not conn:
            messagebox.showerror("Error Crítico de Base de Datos",
                               "No se pudo conectar a la base de datos.\n"
                               "Por favor, verifique 'config.ini' y que el servidor esté en línea.\n\n"
                               "La aplicación se cerrará.")
            self.root.destroy()
            return False
        
        print("Conexión a la base de datos exitosa.")
        conn.close()
        
        print("Verificando y creando el esquema de tablas...")
        self.db_crm.create_tables()
        print("Esquema de tablas verificado.")
        return True

    def _initialize_state_variables(self):
        """Inicializa las variables de estado de la aplicación."""
        self.selected_client = None
        self.selected_case = None
        self.open_case_windows = {}
        self.app_controller = self
        self.fecha_seleccionada_agenda = datetime.date.today().strftime("%Y-%m-%d")
        self.audiencia_seleccionada_id = None
        self.recordatorios_mostrados_hoy = set()
        self.logo_image_tk = None

    def _initialize_managers(self):
        """Inicializa los managers de la aplicación."""
        self.client_manager = ClientManager(self)
        self.case_manager = CaseManager(self)

    def _load_initial_data(self):
        """Carga los datos iniciales de la aplicación."""
        self.client_manager.load_clients()
        self.cargar_audiencias_fecha_actual()
        self.marcar_dias_audiencias_calendario()

    def _start_background_threads(self):
        """Inicia todos los hilos de fondo como último paso."""
        print("Iniciando hilos de fondo...")
        
        # Recordatorios
        self.stop_event_recordatorios = threading.Event()
        self.thread_recordatorios = threading.Thread(
            target=self.verificar_recordatorios_periodicamente,
            args=(self.stop_event_recordatorios,),
            daemon=True
        )
        self.thread_recordatorios.start()
        
        # Inactividad
        self.stop_event_inactividad = threading.Event()
        self.thread_inactividad = threading.Thread(
            target=self.verificar_inactividad_casos_periodicamente,
            args=(self.stop_event_inactividad,),
            daemon=True
        )
        self.thread_inactividad.start()
        
        # Bandeja del sistema
        self._setup_system_tray()

    def _finalize_setup(self):
        """Configuración final de la aplicación."""
        self.root.protocol("WM_DELETE_WINDOW", self.ocultar_a_bandeja)





    def select_and_update_movimientos_folder(self):
        """
        Abre un diálogo para seleccionar la carpeta de movimientos, la guarda en la BD
        y la devuelve.
        """
        if not self.selected_case:
            messagebox.showwarning(
                "Advertencia", "Seleccione un caso primero.", parent=self.root
            )
            return None

        initial_dir = self.selected_case.get(
            "ruta_carpeta_movimientos"
        ) or os.path.expanduser("~")
        folder_selected = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Seleccionar Carpeta de Movimientos Scrapeados",
        )

        if folder_selected:
            case_id = self.selected_case["id"]
            # Usaremos nuestra función de ayuda, ¡pero necesitamos añadir el nuevo campo a la lista blanca!
            self.update_case_field(case_id, "ruta_carpeta_movimientos", folder_selected)

            # Actualizar el diccionario en memoria
            self.selected_case["ruta_carpeta_movimientos"] = folder_selected
            messagebox.showinfo(
                "Éxito", "Carpeta de movimientos asignada al caso.", parent=self.root
            )
            return folder_selected

        return None

    def iniciar_depuracion_ia(
        self, status_label_widget, result_text_widget, button_widget, rol_usuario
    ):
        if not self.selected_case:
            messagebox.showwarning(
                "Advertencia",
                "Por favor, seleccione un caso primero.",
                parent=self.root,
            )
            return

        directorio_de_movimientos = self.selected_case.get("ruta_carpeta_movimientos")

        if not directorio_de_movimientos or not os.path.isdir(
            directorio_de_movimientos
        ):
            messagebox.showwarning(
                "Carpeta no Válida",
                "Por favor, asigne una carpeta de movimientos válida para este caso antes de depurar.",
                parent=self.root,
            )
            return

        caso_id = self.selected_case["id"]

        # --- Crear el "portero" (client) una sola vez ---
        ruta_db_caso = os.path.join(ia_analyzer.VECTOR_DB_BASE_DIR, f"caso_{caso_id}")
        db_client = chromadb.PersistentClient(
            path=ruta_db_caso, settings=chromadb.Settings(anonymized_telemetry=False)
        )

        button_widget.config(state=tk.DISABLED, text="Depurando...")
        result_text_widget.config(state=tk.NORMAL)
        result_text_widget.delete("1.0", tk.END)
        result_text_widget.insert("1.0", "Procesando en modo depuración (sin costo)...")
        result_text_widget.config(state=tk.DISABLED)
        self.root.update_idletasks()

        def thread_target_debug(client_para_hilo):
            try:
                logging.info(
                    f"Procesando carpeta: '{directorio_de_movimientos}' con el rol: '{rol_usuario}'"
                )

                self.root.after(
                    0,
                    lambda: status_label_widget.config(
                        text=f"Estado: 1/3 - Concatenando..."
                    ),
                )
                ruta_archivo_fuente = ia_analyzer.preparar_y_concatenar_movimientos(
                    directorio_de_movimientos, caso_id
                )
                if not ruta_archivo_fuente:
                    self.root.after(
                        0,
                        lambda: status_label_widget.config(
                            text="Error: No se encontraron .txt."
                        ),
                    )
                    return

                self.root.after(
                    0,
                    lambda: status_label_widget.config(
                        text="Estado: 2/3 - Indexando..."
                    ),
                )
                nombre_coleccion = ia_analyzer.indexar_expediente(
                    client_para_hilo, ruta_archivo_fuente, caso_id
                )
                if not nombre_coleccion:
                    self.root.after(
                        0,
                        lambda: status_label_widget.config(
                            text="Error: Falló la indexación."
                        ),
                    )
                    return

                self.root.after(
                    0,
                    lambda: status_label_widget.config(
                        text="Estado: 3/3 - Buscando fragmentos..."
                    ),
                )
                prompt_de_prueba = (
                    f"Actuando como el abogado de la '{rol_usuario}', "
                    f"dame un resumen del estado actual del caso y los próximos pasos a seguir."
                )

                resultado_debug = ia_analyzer.debug_retriever(
                    client_para_hilo, nombre_coleccion, prompt_de_prueba
                )

                def actualizar_ui_debug():
                    result_text_widget.config(state=tk.NORMAL)
                    result_text_widget.delete("1.0", tk.END)
                    result_text_widget.insert("1.0", resultado_debug)
                    result_text_widget.config(state=tk.DISABLED)
                    status_label_widget.config(
                        text="Estado: Depuración completada (sin costo)."
                    )

                self.root.after(0, actualizar_ui_debug)

            except Exception as e:
                self.root.after(
                    0, lambda err=e: status_label_widget.config(text=f"Error: {err}")
                )
                import traceback

                traceback.print_exc()

            finally:
                self.root.after(
                    0,
                    lambda: button_widget.config(
                        state=tk.NORMAL, text="Depurar Búsqueda (Sin Costo)"
                    ),
                )

        threading.Thread(
            target=thread_target_debug, args=(db_client,), daemon=True
        ).start()

    def iniciar_analisis_ia(
        self, status_label_widget, result_text_widget, button_widget, rol_usuario
    ):
        if not self.selected_case:
            messagebox.showwarning(
                "Advertencia",
                "Por favor, seleccione un caso primero.",
                parent=self.root,
            )
            return

        directorio_de_movimientos = self.selected_case.get("ruta_carpeta_movimientos")
        if not directorio_de_movimientos or not os.path.isdir(
            directorio_de_movimientos
        ):
            messagebox.showwarning(
                "Carpeta no Válida",
                "Por favor, asigne una carpeta de movimientos válida para este caso antes de analizar.",
                parent=self.root,
            )
            return

        caso_id = self.selected_case["id"]
        ruta_db_caso = os.path.join(ia_analyzer.VECTOR_DB_BASE_DIR, f"caso_{caso_id}")
        db_client = chromadb.PersistentClient(
            path=ruta_db_caso, settings=chromadb.Settings(anonymized_telemetry=False)
        )

        button_widget.config(
            state=tk.DISABLED, text="Analizando... Espere por favor..."
        )
        status_label_widget.config(text="Estado: Iniciando análisis...")
        result_text_widget.config(state=tk.NORMAL)
        result_text_widget.delete("1.0", tk.END)
        result_text_widget.insert(
            "1.0", "Procesando, esto puede tardar varios segundos..."
        )
        result_text_widget.config(state=tk.DISABLED)
        self.root.update_idletasks()

        def thread_target(client_para_hilo):
            try:
                self.root.after(
                    0,
                    lambda: status_label_widget.config(
                        text="Estado: 1/4 - Concatenando movimientos..."
                    ),
                )
                ruta_archivo_fuente = ia_analyzer.preparar_y_concatenar_movimientos(
                    directorio_de_movimientos, caso_id
                )
                if not ruta_archivo_fuente:
                    self.root.after(
                        0,
                        lambda: status_label_widget.config(
                            text="Error: No se encontraron .txt."
                        ),
                    )
                    return

                self.root.after(
                    0,
                    lambda: status_label_widget.config(
                        text="Estado: 2/4 - Indexando expediente..."
                    ),
                )
                nombre_coleccion = ia_analyzer.indexar_expediente(
                    client_para_hilo, ruta_archivo_fuente, caso_id
                )
                if not nombre_coleccion:
                    self.root.after(
                        0,
                        lambda: status_label_widget.config(
                            text="Error: Falló la indexación."
                        ),
                    )
                    return

                self.update_case_field(caso_id, "ruta_vector_db", ruta_db_caso)
                self.update_case_field(caso_id, "estado_indexacion", "Indexado")

                self.root.after(
                    0,
                    lambda: status_label_widget.config(
                        text="Estado: 3/4 - Realizando consulta a la IA..."
                    ),
                )

                # --- NUEVO: Cargar el prompt desde un archivo externo ---
                try:
                    with open(
                        "prompts/analisis_expediente.txt", "r", encoding="utf-8"
                    ) as f:
                        plantilla_prompt = f.read()

                    # Rellenar el marcador {rol_usuario} con el valor real
                    prompt_final = plantilla_prompt.format(rol_usuario=rol_usuario)

                except FileNotFoundError:
                    print(
                        "ERROR: No se encontró el archivo de prompt 'prompts/analisis_expediente.txt'"
                    )
                    # Usamos un prompt de fallback por si acaso
                    prompt_final = f"Actuando como el abogado de la '{rol_usuario}', dame un resumen del caso."
                # --- FIN DE LA CARGA DEL PROMPT ---
                resultado = ia_analyzer.consultar_expediente(
                    client_para_hilo, nombre_coleccion, prompt_final
                )

                self.root.after(
                    0,
                    lambda: status_label_widget.config(
                        text="Estado: 4/4 - Mostrando resultado."
                    ),
                )

                def actualizar_ui_final():
                    result_text_widget.config(state=tk.NORMAL)
                    result_text_widget.delete("1.0", tk.END)

                    if "error" in resultado:
                        texto_final = f"ERROR: {resultado['error']}"
                        result_text_widget.insert("1.0", texto_final)
                    else:
                        texto_final = resultado.get("result", "No se obtuvo respuesta.")
                        result_text_widget.insert("1.0", texto_final)

                        try:
                            print(
                                f"Guardando análisis de IA como actividad en el caso ID {caso_id}."
                            )
                            self._save_new_actividad(
                                caso_id=caso_id,
                                tipo_actividad="Análisis IA de Expediente",
                                descripcion=texto_final,
                                referencia_doc="Informe IA",
                            )
                            print(
                                "Análisis guardado con éxito en el seguimiento del caso."
                            )
                        except Exception as e_save:
                            # Si el guardado falla, no es un error crítico, pero lo registramos
                            print(
                                f"Error al intentar guardar el análisis como actividad: {e_save}"
                            )
                    # --- FIN DEL CÓDIGO DE GUARDADO ---

                    # result_text_widget.insert('1.0', "\n\nAnálisis guardado como actividad en el caso.")
                    result_text_widget.config(state=tk.DISABLED)
                    status_label_widget.config(
                        text="Estado: Análisis completo y guardado."
                    )

                self.root.after(0, actualizar_ui_final)

            except Exception as e:
                self.root.after(
                    0, lambda err=e: status_label_widget.config(text=f"Error: {err}")
                )
                import traceback

                traceback.print_exc()

            finally:
                self.root.after(
                    0,
                    lambda: button_widget.config(
                        state=tk.NORMAL,
                        text="Analizar Movimientos del Expediente con IA",
                    ),
                )

        threading.Thread(target=thread_target, args=(db_client,), daemon=True).start()

    def _refresh_open_case_window(self, case_id):
        """Si una ventana de detalles para un caso está abierta, le pide que refresque su pestaña activa."""
        if case_id in self.open_case_windows:
            print(f"Notificando a la ventana del caso {case_id} para que se refresque.")
            window = self.open_case_windows[case_id]
            # window.refresh_active_tab()
            self.root.after(50, window.refresh_active_tab)

    def update_case_field(self, case_id, field_name, value):
        """Método de ayuda para actualizar un solo campo de un caso en la BD."""
        try:
            allowed_fields = [
                "ruta_vector_db",
                "estado_indexacion",
                "ruta_carpeta_movimientos",
                "ruta_carpeta",  # AGREGADO: Permitir actualizar carpeta principal
            ]
            if field_name not in allowed_fields:
                print(
                    f"Error: Intento de actualizar un campo no permitido: {field_name}"
                )
                return

            # Usar la función del nuevo crm_database.py
            conn = self.db_crm.connect_db()
            if not conn:
                print(
                    f"Error: No se pudo conectar a la BD para actualizar el campo {field_name}."
                )
                return

            with conn.cursor() as cursor:
                # CORREGIDO: Usar sintaxis PostgreSQL (%s) en lugar de SQLite (?)
                sql = f"UPDATE casos SET {field_name} = %s WHERE id = %s"
                cursor.execute(sql, (value, case_id))
                conn.commit()
                print(
                    f"Campo '{field_name}' actualizado a '{value}' para el caso ID {case_id}."
                )

                # Actualizar timestamp de actividad
                self.db_crm.update_last_activity(case_id)

        except Exception as e:  # CORREGIDO: Usar Exception genérico para PostgreSQL
            print(f"Error en BD al actualizar campo '{field_name}': {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()

    def launch_scba_scraper(self):

        # Por ahora, permitiremos múltiples instancias si el usuario hace clic de nuevo.
        try:
            SCBAScraperWindow = get_scba_scraper_window()
            scraper_win = SCBAScraperWindow(self.root)
            scraper_win.grab_set()  # Para hacerla modal respecto a la ventana principal del CRM
            # scraper_win.focus_force() # No siempre necesario con grab_set
        except ImportError:
            messagebox.showerror(
                "Error de Importación",
                "No se pudo cargar el módulo customtkinter. Verifique la instalación.",
            )
            print("Error: customtkinter no está instalado o no se pudo importar.")
        except Exception as e:
            messagebox.showerror(
                "Error al Abrir Scraper",
                f"No se pudo abrir la ventana del scraper SCBA:\n{type(e).__name__}: {e}",
            )
            print(f"Error al instanciar SCBAScraperWindow: {e}")

    def _launch_pjn_scraper(self):
        """Launch PJN scraper - can use SCBA interface or external script"""
        try:
            # Opción 1: Intentar usar la interfaz del scraper SCBA para PJN
            # (siguiendo tu sugerencia de reutilizar la interfaz)
            try:
                SCBAScraperWindow = get_scba_scraper_window()
                # Crear ventana del scraper con configuración para PJN
                scraper_win = SCBAScraperWindow(self.root, scraper_type="PJN")
                scraper_win.grab_set()
                return
            except (ImportError, TypeError):
                # Si no se puede usar la interfaz SCBA, continuar con opción 2
                pass
            
            # Opción 2: Lanzar script externo scraper_pjn.py si existe
            if os.path.exists('scraper_pjn.py'):
                subprocess.Popen([sys.executable, 'scraper_pjn.py'])
                messagebox.showinfo(
                    "Scraper PJN", 
                    "Scraper PJN lanzado en ventana separada.",
                    parent=self.root
                )
            else:
                # Opción 3: Mensaje informativo si no hay implementación disponible
                messagebox.showinfo(
                    "Scraper PJN",
                    "El scraper PJN se puede implementar usando:\n"
                    "1. La interfaz del scraper SCBA adaptada para PJN\n"
                    "2. Un script independiente 'scraper_pjn.py'\n\n"
                    "Contacte al desarrollador para más información.",
                    parent=self.root
                )
                
        except Exception as e:
            messagebox.showerror(
                "Error al Lanzar Scraper PJN",
                f"No se pudo abrir el scraper PJN:\n{type(e).__name__}: {e}",
                parent=self.root
            )
            print(f"Error al lanzar scraper PJN: {e}")

    def verificar_inactividad_casos_periodicamente(self, stop_event):
        print("[Inactividad Casos] Hilo iniciado.")
        while not stop_event.is_set():
            current_processing_start_time = time.monotonic()
            try:
                casos_a_notificar = self.db_crm.get_cases_for_inactivity_check()
                for caso in casos_a_notificar:
                    if stop_event.is_set():
                        break

                    print(
                        f"[Inactividad Casos] ¡Alerta! Caso ID: {caso['id']} ('{caso['caratula']}') ha superado el umbral de inactividad de {caso['inactivity_threshold_days']} días."
                    )

                    # Preparar notificación
                    titulo = f"Alerta de Inactividad: Caso {caso['id']}"
                    mensaje = f"El caso '{caso['caratula']}' no ha tenido actividad en más de {caso['inactivity_threshold_days']} días."
                    app_nombre = "CRM Legal"
                    icon_path_notif = ""
                    try:
                        icon_path_notif = resource_path("assets/icono.ico")
                        if not os.path.exists(icon_path_notif):
                            print(
                                f"Advertencia: Icono notificación no encontrado: {icon_path_notif}"
                            )
                            icon_path_notif = ""
                    except Exception as e:
                        print(f"Error obteniendo ruta de icono para notificación: {e}")
                        icon_path_notif = ""

                    # Mostrar notificación
                    try:
                        print(
                            f"[Inactividad Casos] Enviando notificación: T='{titulo}', M='{mensaje}'"
                        )
                        plyer_module.notification.notify(
                            title=titulo,
                            message=mensaje,
                            app_name=app_nombre,
                            app_icon=icon_path_notif,
                            timeout=20,  # Segundos que la notificación es visible (puede variar por OS)
                        )
                        print(
                            "[Inactividad Casos] Notificación plyer.notify() llamada."
                        )
                        # Actualizar timestamp de última notificación de inactividad
                        self.db_crm.update_case_inactivity_notified(caso["id"])
                    except NotImplementedError:
                        print(
                            "[Inactividad Casos] Notificación Plyer no soportada en esta plataforma. Usando fallback messagebox."
                        )
                        # Este fallback es problemático para un hilo en segundo plano,
                        # pero es mejor que nada si plyer no está disponible.
                        # Idealmente, se registraría el error y se continuaría.
                        self.root.after(
                            0,
                            messagebox.showwarning,
                            titulo,
                            mensaje,
                            {"parent": self.root},
                        )
                        self.db_crm.update_case_inactivity_notified(
                            caso["id"]
                        )  # Intentar actualizar incluso con fallback
                    except Exception as e_notify:
                        print(
                            f"[Inactividad Casos] Error durante notificación Plyer: {e_notify}. Usando fallback messagebox."
                        )
                        self.root.after(
                            0,
                            messagebox.showwarning,
                            titulo,
                            mensaje,
                            {"parent": self.root},
                        )
                        self.db_crm.update_case_inactivity_notified(
                            caso["id"]
                        )  # Intentar actualizar

            except sqlite3.Error as dbe:
                print(f"[Inactividad Casos] Error de Base de Datos en hilo: {dbe}")
                # Esperar más tiempo si hay error de BD antes de reintentar
                stop_event.wait(300)  # Esperar 5 minutos
            except Exception as ex_thread:
                print(
                    f"[Inactividad Casos] Error inesperado en hilo: {type(ex_thread).__name__}: {ex_thread}"
                )
                import traceback

                traceback.print_exc()
                stop_event.wait(120)  # Esperar 2 minutos

            # Calcular tiempo de espera para el próximo chequeo (ej. cada hora)
            processing_duration = time.monotonic() - current_processing_start_time
            # Chequear cada 1 hora (3600 segundos). Ajustar según necesidad.
            sleep_interval = max(1.0, 3600.0 - processing_duration)
            print(
                f"[Inactividad Casos] Ciclo completado en {processing_duration:.2f}s. Durmiendo por {sleep_interval:.2f}s."
            )
            stop_event.wait(sleep_interval)
        print("[Inactividad Casos] Hilo detenido.")

    # Esta es la definición CORRECTA de create_widgets que queremos conservar y usar.
    # La segunda definición duplicada será eliminada.
    def open_case_detail_window(self, event=None):
        if not self.selected_case:
            return
        case_id = self.selected_case["id"]
        if case_id in self.open_case_windows:
            window = self.open_case_windows[case_id]
            window.lift()
            window.focus_force()
            return
        CaseDetailWindow = get_case_detail_window()
        new_window = CaseDetailWindow(self.root, self, case_id)
        self.open_case_windows[case_id] = new_window

    def on_case_window_close(self, case_id):
        if case_id in self.open_case_windows:
            del self.open_case_windows[case_id]

    def create_widgets(self):
        print(
            "--- EJECUTANDO create_widgets VERSIÓN FINAL (LOGO EN COL 2, CASOS EN COL 3) ---"
        )

        # ESTRUCTURA DE 3 COLUMNAS REVISADA SEGÚN TU PROPUESTA
        crm_main_frame = ttk.Frame(self.root, padding="10")
        crm_main_frame.pack(fill=tk.BOTH, expand=True)

        crm_main_frame.rowconfigure(0, weight=1)
        crm_main_frame.columnconfigure(0, weight=0)  # Clientes
        crm_main_frame.columnconfigure(1, weight=0)  # Logo y Calendario
        crm_main_frame.columnconfigure(2, weight=2)  # Casos y Audiencias

        # --- Columna 1: Clientes ---
        col1_frame = ttk.Frame(crm_main_frame)
        col1_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        col1_frame.rowconfigure(0, weight=1)
        col1_frame.columnconfigure(0, weight=1)
        client_list_frame = ttk.LabelFrame(col1_frame, text="Clientes", padding="5")
        client_list_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        client_list_frame.columnconfigure(0, weight=1)
        client_list_frame.rowconfigure(0, weight=1)
        self.client_tree = ttk.Treeview(
            client_list_frame,
            columns=("ID", "Nombre"),
            show="headings",
            selectmode="browse",
        )
        self.client_tree.heading("ID", text="ID")
        self.client_tree.heading("Nombre", text="Nombre")
        self.client_tree.column("ID", width=40, stretch=tk.NO)
        self.client_tree.column("Nombre", width=150, stretch=tk.YES)
        client_scrollbar_y = ttk.Scrollbar(
            client_list_frame, orient=tk.VERTICAL, command=self.client_tree.yview
        )
        self.client_tree.configure(yscrollcommand=client_scrollbar_y.set)
        client_scrollbar_x = ttk.Scrollbar(
            client_list_frame, orient=tk.HORIZONTAL, command=self.client_tree.xview
        )
        self.client_tree.configure(xscrollcommand=client_scrollbar_x.set)
        self.client_tree.grid(row=0, column=0, sticky="nsew")
        client_scrollbar_y.grid(row=0, column=1, sticky="ns")
        client_scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.client_tree.bind(
            "<<TreeviewSelect>>", self.client_manager.on_client_select
        )
        client_buttons_frame = ttk.Frame(col1_frame)
        client_buttons_frame.grid(row=1, column=0, sticky="ew", pady=5)
        self.add_client_btn = ttk.Button(
            client_buttons_frame,
            text="ALTA",
            command=lambda: self.client_manager.open_client_dialog(),
        )
        self.add_client_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.edit_client_btn = ttk.Button(
            client_buttons_frame,
            text="MODIFICAR",
            command=lambda: self.client_manager.open_client_dialog(
                self.selected_client["id"] if self.selected_client else None
            ),
            state=tk.DISABLED,
        )
        self.edit_client_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.delete_client_btn = ttk.Button(
            client_buttons_frame,
            text="BORRAR",
            command=self.client_manager.delete_client,
            state=tk.DISABLED,
        )
        self.delete_client_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))
        client_details_frame = ttk.LabelFrame(
            col1_frame, text="Detalles Cliente", padding="10"
        )
        client_details_frame.grid(row=2, column=0, sticky="ew", pady=(5, 0))
        client_details_frame.columnconfigure(1, weight=1)
        ttk.Label(client_details_frame, text="Nombre:").grid(
            row=0, column=0, sticky=tk.W, pady=1, padx=5
        )
        self.client_detail_name_lbl = ttk.Label(
            client_details_frame, text="", wraplength=200
        )
        self.client_detail_name_lbl.grid(row=0, column=1, sticky=tk.EW, pady=1, padx=5)
        ttk.Label(client_details_frame, text="Dirección:").grid(
            row=1, column=0, sticky=tk.W, pady=1, padx=5
        )
        self.client_detail_address_lbl = ttk.Label(
            client_details_frame, text="", wraplength=200
        )
        self.client_detail_address_lbl.grid(
            row=1, column=1, sticky=tk.EW, pady=1, padx=5
        )
        ttk.Label(client_details_frame, text="Email:").grid(
            row=2, column=0, sticky=tk.W, pady=1, padx=5
        )
        self.client_detail_email_lbl = ttk.Label(
            client_details_frame, text="", wraplength=200
        )
        self.client_detail_email_lbl.grid(row=2, column=1, sticky=tk.EW, pady=1, padx=5)
        ttk.Label(client_details_frame, text="WhatsApp:").grid(
            row=3, column=0, sticky=tk.W, pady=1, padx=5
        )
        self.client_detail_whatsapp_lbl = ttk.Label(
            client_details_frame, text="", wraplength=200
        )
        self.client_detail_whatsapp_lbl.grid(
            row=3, column=1, sticky=tk.EW, pady=1, padx=5
        )
        ttk.Label(client_details_frame, text="Etiquetas:").grid(
            row=4, column=0, sticky=tk.W, pady=1, padx=5
        )
        self.client_detail_tags_lbl = ttk.Label(
            client_details_frame, text="", wraplength=200
        )
        self.client_detail_tags_lbl.grid(row=4, column=1, sticky=tk.EW, pady=1, padx=5)

        # --- Columna 2: Logo y Calendario ---
        col2_frame = ttk.Frame(crm_main_frame)
        col2_frame.grid(row=0, column=1, sticky="nsew", padx=5)
        col2_frame.rowconfigure(1, weight=0)
        col2_frame.columnconfigure(0, weight=1)
        logo_frame = ttk.LabelFrame(col2_frame, text="Powered by")
        logo_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5), ipady=5)
        logo_frame.columnconfigure(0, weight=1)
        try:
            logo_path = resource_path("assets/logoLegalito01.png")
            img = PIL_Image.open(logo_path)
            w, h = img.size
            new_w = 220
            new_h = int(h * (new_w / w))
            img = img.resize((new_w, new_h), PIL_Image.Resampling.LANCZOS)
            self.logo_image_tk = PIL_ImageTk.PhotoImage(img)
            logo_label = ttk.Label(logo_frame, image=self.logo_image_tk)
            logo_label.grid(row=0, column=0)
        except Exception as e:
            ttk.Label(logo_frame, text="Legal-IT").pack(pady=20)
            # Handle encoding issues in error message
            try:
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                print(f"Error al cargar el logo: {error_msg}")
            except (UnicodeEncodeError, UnicodeDecodeError):
                print("Error al cargar el logo: [Error de codificación en el mensaje]")
            # Also handle system tray encoding issues
            try:
                # Try to fix the system tray encoding issue
                import sys
                if hasattr(sys.stdout, 'reconfigure'):
                    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
                    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass  # Ignore if reconfigure is not available

        # --- Frame para botones de Scraping ---
        scrap_buttons_frame = ttk.Frame(col2_frame)
        scrap_buttons_frame.grid(
            row=1, column=0, sticky="ew", pady=5
        )  # Ubicado debajo del logo
        self.scrap_scba_btn = ttk.Button(
            scrap_buttons_frame, text="Scrap SCBA", command=self.launch_scba_scraper
        )
        self.scrap_scba_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 2))
        self.scrap_pjn_btn = ttk.Button(
            scrap_buttons_frame,
            text="Scrap PJN",
            command=self._launch_pjn_scraper,
            state=tk.NORMAL
        )
        self.scrap_pjn_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(2, 0))

        # Calendario debajo de los botones de scraping
        cal_frame = ttk.LabelFrame(col2_frame, text="Calendario", padding=5)
        cal_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        cal_frame.columnconfigure(0, weight=1)
        cal_frame.rowconfigure(0, weight=1)
        self.agenda_cal = Calendar(
            cal_frame, selectmode="day", date_pattern="y-mm-dd", locale="es_ES"
        )
        self.agenda_cal.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.agenda_cal.bind("<<CalendarSelected>>", self.actualizar_lista_audiencias)
        self.agenda_cal.tag_config(
            "audiencia_marcador", background="lightblue", foreground="black"
        )
        # Botón de agregar audiencia debajo del calendario
        add_aud_frame = ttk.Frame(col2_frame)
        add_aud_frame.grid(row=3, column=0, sticky="ew", pady=(5, 0))
        self.add_audiencia_btn = ttk.Button(
            add_aud_frame,
            text="Agregar Audiencia",
            command=lambda: self.abrir_dialogo_audiencia(),
            state=tk.DISABLED,
        )
        self.add_audiencia_btn.pack(fill=tk.X, padx=10, pady=5)

        # Ajustar rowconfigure de col2_frame para que el calendario no se expanda demasiado y los botones queden visibles
        col2_frame.rowconfigure(0, weight=0)  # Logo
        col2_frame.rowconfigure(1, weight=0)  # Botones Scrap
        col2_frame.rowconfigure(
            2, weight=0
        )  # Calendario (no se expande, pero su contenido sí)
        col2_frame.rowconfigure(3, weight=0)  # Botón Agregar Audiencia

        # --- Columna 3: Casos y Audiencias ---
        # Renombrar col3_frame a col_casos_audiencias_frame para claridad
        col_casos_audiencias_frame = ttk.Frame(crm_main_frame)
        col_casos_audiencias_frame.grid(row=0, column=2, sticky="nsew", padx=(5, 0))
        col_casos_audiencias_frame.rowconfigure(
            0, weight=2
        )  # Lista de Casos (más peso)
        col_casos_audiencias_frame.rowconfigure(
            1, weight=1
        )  # Área de Audiencias (peso estándar)
        col_casos_audiencias_frame.columnconfigure(
            0, weight=1
        )  # Columna única para los frames internos

        # Frame para la lista de Casos (ocupa la parte superior de col_casos_audiencias_frame)
        case_list_frame = ttk.LabelFrame(
            col_casos_audiencias_frame, text="Casos Cliente", padding="5"
        )
        case_list_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        case_list_frame.columnconfigure(0, weight=1)
        case_list_frame.rowconfigure(0, weight=1)
        self.case_tree = ttk.Treeview(
            case_list_frame,
            columns=("ID", "Nro/Ano", "Caratula"),
            show="headings",
            selectmode="browse",
        )
        self.case_tree.heading("ID", text="ID")
        self.case_tree.heading("Nro/Ano", text="Nro/Ano")
        self.case_tree.heading("Caratula", text="Caratula")
        self.case_tree.column("ID", width=40, stretch=tk.NO)
        self.case_tree.column("Nro/Ano", width=80, stretch=tk.NO)
        self.case_tree.column("Caratula", width=250, stretch=tk.YES)
        case_scrollbar_Y = ttk.Scrollbar(
            case_list_frame, orient=tk.VERTICAL, command=self.case_tree.yview
        )
        self.case_tree.configure(yscrollcommand=case_scrollbar_Y.set)
        case_scrollbar_x = ttk.Scrollbar(
            case_list_frame, orient=tk.HORIZONTAL, command=self.case_tree.xview
        )
        self.case_tree.configure(xscrollcommand=case_scrollbar_x.set)
        self.case_tree.grid(row=0, column=0, sticky="nsew")
        case_scrollbar_Y.grid(row=0, column=1, sticky="ns")
        case_scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.case_tree.bind("<<TreeviewSelect>>", self.on_case_select)
        self.case_tree.bind("<Double-1>", self.open_case_detail_window)
        case_buttons_frame = ttk.Frame(case_list_frame)
        case_buttons_frame.grid(row=2, column=0, sticky="ew", pady=5)
        self.add_case_btn = ttk.Button(
            case_buttons_frame,
            text="Alta",
            command=lambda: self.case_manager.open_case_dialog(),
            state=tk.DISABLED,
        )
        self.add_case_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.edit_case_btn = ttk.Button(
            case_buttons_frame,
            text="Modificar",
            command=lambda: self.case_manager.open_case_dialog(
                self.selected_case["id"] if self.selected_case else None
            ),
            state=tk.DISABLED,
        )
        self.edit_case_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.delete_case_btn = ttk.Button(
            case_buttons_frame,
            text="Baja",
            command=self.case_manager.delete_case,
            state=tk.DISABLED,
        )
        self.delete_case_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        # Botón para Acuerdos de Mediación
        self.mediacion_btn = ttk.Button(
            case_buttons_frame,
            text="Acuerdo Mediación",
            command=self.generar_acuerdo_mediacion,
            state=tk.DISABLED,
        )
        self.mediacion_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5, 0))

        # Frame para el área de Audiencias (ocupa la parte inferior de col_casos_audiencias_frame)
        audiencia_main_area_frame = ttk.Frame(col_casos_audiencias_frame)
        audiencia_main_area_frame.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        # Configurar columnas para agenda_list_frame (más ancho) y audiencia_details_frame
        audiencia_main_area_frame.columnconfigure(
            0, weight=0
        )  # Lista de audiencias del día
        audiencia_main_area_frame.columnconfigure(1, weight=1)  # Detalles de audiencia
        audiencia_main_area_frame.rowconfigure(
            0, weight=1
        )  # Para que ambos se expandan verticalmente

        agenda_list_frame = ttk.LabelFrame(
            audiencia_main_area_frame, text="Audiencias del Día", padding="5"
        )
        agenda_list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        agenda_list_frame.rowconfigure(0, weight=1)
        agenda_list_frame.columnconfigure(0, weight=1)
        agenda_cols = ("ID", "Hora", "Detalle", "Caso")
        self.audiencia_tree = ttk.Treeview(
            agenda_list_frame, columns=agenda_cols, show="headings", selectmode="browse"
        )
        self.audiencia_tree.heading("ID", text="ID")
        self.audiencia_tree.heading("Hora", text="Hora")
        self.audiencia_tree.heading("Detalle", text="Detalle")
        self.audiencia_tree.heading("Caso", text="Caso")
        self.audiencia_tree.column("ID", width=30, stretch=tk.NO)
        self.audiencia_tree.column("Hora", width=50, stretch=tk.NO)
        self.audiencia_tree.column("Detalle", width=150, stretch=True)
        self.audiencia_tree.column("Caso", width=120, stretch=True)
        agenda_scroll_y = ttk.Scrollbar(
            agenda_list_frame, orient=tk.VERTICAL, command=self.audiencia_tree.yview
        )
        self.audiencia_tree.configure(yscrollcommand=agenda_scroll_y.set)
        agenda_scroll_y.grid(row=0, column=1, sticky="ns")
        self.audiencia_tree.grid(row=0, column=0, sticky="nsew")
        self.audiencia_tree.bind("<<TreeviewSelect>>", self.on_audiencia_tree_select)
        self.audiencia_tree.bind("<Double-1>", self.abrir_link_audiencia_seleccionada)
        audiencia_actions_frame = ttk.Frame(agenda_list_frame)
        audiencia_actions_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        self.edit_audiencia_btn = ttk.Button(
            audiencia_actions_frame,
            text="Editar",
            command=self.editar_audiencia_seleccionada,
            state=tk.DISABLED,
        )
        self.edit_audiencia_btn.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        self.delete_audiencia_btn = ttk.Button(
            audiencia_actions_frame,
            text="Eliminar",
            command=self.eliminar_audiencia_seleccionada,
            state=tk.DISABLED,
        )
        self.delete_audiencia_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.share_audiencia_btn = ttk.Button(
            audiencia_actions_frame,
            text="Compartir",
            command=self.mostrar_menu_compartir_audiencia,
            state=tk.DISABLED,
        )
        self.share_audiencia_btn.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.open_link_audiencia_btn = ttk.Button(
            audiencia_actions_frame,
            text="Abrir Link",
            command=self.abrir_link_audiencia_seleccionada,
            state=tk.DISABLED,
        )
        self.open_link_audiencia_btn.pack(side=tk.LEFT, padx=3, fill=tk.X, expand=True)

        audiencia_details_frame = ttk.LabelFrame(
            audiencia_main_area_frame, text="Detalles Completos del Evento", padding="5"
        )
        audiencia_details_frame.grid(row=0, column=1, sticky="nsew")
        audiencia_details_frame.rowconfigure(0, weight=1)
        audiencia_details_frame.columnconfigure(0, weight=1)
        self.audiencia_details_text = tk.Text(
            audiencia_details_frame, height=5, wrap=tk.WORD, state=tk.DISABLED
        )
        audiencia_details_scroll = ttk.Scrollbar(
            audiencia_details_frame,
            orient=tk.VERTICAL,
            command=self.audiencia_details_text.yview,
        )
        self.audiencia_details_text.configure(
            yscrollcommand=audiencia_details_scroll.set
        )
        audiencia_details_scroll.grid(row=0, column=1, sticky="ns")
        self.audiencia_details_text.grid(row=0, column=0, sticky="nsew")

    # REFACTORIZADO: Método movido a CaseManager
    def on_case_select(self, event):
        """REFACTORIZADO: Ahora usa CaseManager.on_case_select()"""
        return self.case_manager.on_case_select(event)

        # REFACTORIZADO: Método movido a CaseManager

    def open_agent_interface(self):
        """Abrir la interfaz del agente inteligente para generación de acuerdos"""
        try:
            from agent_interface import open_agent_interface
            agent_window = open_agent_interface(self.root)
            if agent_window:
                print("[INFO] Interfaz del agente IA abierta correctamente")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la interfaz del agente IA:\n{str(e)}",
                parent=self.root
            )
            print(f"[ERROR] Error abriendo interfaz del agente: {e}")

    def open_reformular_hechos_dialog(self):
        # Determinar si hay un caso seleccionado para pre-llenar o asociar
        caso_actual_id = self.selected_case["id"] if self.selected_case else None
        caso_actual_caratula = (
            self.selected_case.get("caratula", "General")
            if self.selected_case
            else "General"
        )

        dialog = Toplevel(self.root)
        dialog.title(f"Reformular Hechos con IA (Caso: {caso_actual_caratula[:30]})")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.geometry("700x600")
        dialog.resizable(True, True)

        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(
            0, weight=1
        )  # Única columna principal para los frames de texto y status
        # main_frame.rowconfigure(0, weight=0) # Etiqueta de entrada (no necesita expandirse)
        main_frame.rowconfigure(1, weight=2)  # Para el input_text_frame
        # main_frame.rowconfigure(2, weight=0) # Etiqueta de salida (no necesita expandirse)
        main_frame.rowconfigure(3, weight=3)  # Para el output_text_frame
        # main_frame.rowconfigure(4, weight=0) # Status label
        # main_frame.rowconfigure(5, weight=0) # Button frame

        ttk.Label(
            main_frame, text="Ingrese los hechos del cliente (o texto a reformular):"
        ).grid(row=0, column=0, sticky=tk.NW, pady=(0, 2))

        input_text_frame = ttk.Frame(main_frame)
        input_text_frame.grid(row=1, column=0, sticky="nsew", pady=2)
        input_text_frame.columnconfigure(0, weight=1)
        input_text_frame.rowconfigure(0, weight=1)
        hechos_entrada_text = tk.Text(input_text_frame, wrap=tk.WORD, height=10)
        hechos_entrada_text.grid(row=0, column=0, sticky="nsew")
        hechos_entrada_scroll = ttk.Scrollbar(
            input_text_frame, command=hechos_entrada_text.yview
        )
        hechos_entrada_scroll.grid(row=0, column=1, sticky="ns")
        hechos_entrada_text["yscrollcommand"] = hechos_entrada_scroll.set

        ttk.Label(main_frame, text="Hechos Reformulados por IA:").grid(
            row=2, column=0, sticky=tk.NW, pady=(5, 2)
        )

        output_text_frame = ttk.Frame(main_frame)
        output_text_frame.grid(row=3, column=0, sticky="nsew", pady=2)
        output_text_frame.columnconfigure(0, weight=1)
        output_text_frame.rowconfigure(0, weight=1)
        resultado_ia_text = tk.Text(
            output_text_frame, wrap=tk.WORD, height=15, state=tk.DISABLED
        )
        resultado_ia_text.grid(row=0, column=0, sticky="nsew")
        resultado_ia_scroll = ttk.Scrollbar(
            output_text_frame, command=resultado_ia_text.yview
        )
        resultado_ia_scroll.grid(row=0, column=1, sticky="ns")
        resultado_ia_text["yscrollcommand"] = resultado_ia_scroll.set

        status_var = tk.StringVar(value="Listo para recibir hechos.")
        status_label = ttk.Label(
            main_frame, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_label.grid(
            row=4, column=0, sticky=tk.EW, pady=(5, 5)
        )  # Pady para separar de botones

        # --- AQUÍ DEBEN ESTAR LAS DEFINICIONES DE LAS FUNCIONES ---
        def actualizar_ui_con_respuesta(resultado_json):  # Movida antes de su uso
            resultado_ia_text.config(state=tk.NORMAL)
            resultado_ia_text.delete("1.0", tk.END)
            if resultado_json and "hechos_reformulados" in resultado_json:
                resultado_ia_text.insert("1.0", resultado_json["hechos_reformulados"])
                status_var.set("Respuesta de IA recibida.")
                copiar_btn.config(
                    state=(
                        tk.NORMAL
                        if resultado_ia_text.get("1.0", tk.END).strip()
                        else tk.DISABLED
                    )
                )
                guardar_docx_btn.config(
                    state=(
                        tk.NORMAL
                        if resultado_ia_text.get("1.0", tk.END).strip()
                        else tk.DISABLED
                    )
                )
            elif resultado_json and "error" in resultado_json:
                error_msg_ia = (
                    f"Error devuelto por el Asistente IA: {resultado_json['error']}"
                )
                resultado_ia_text.insert("1.0", error_msg_ia)
                status_var.set("Error en la IA.")
                messagebox.showerror("Error de IA", error_msg_ia, parent=dialog)
                copiar_btn.config(state=tk.DISABLED)
                guardar_docx_btn.config(state=tk.DISABLED)
            else:
                resultado_ia_text.insert(
                    "1.0", "Respuesta inesperada o vacía del servidor."
                )
                status_var.set("Error: Respuesta no reconocida.")
                copiar_btn.config(state=tk.DISABLED)
                guardar_docx_btn.config(state=tk.DISABLED)
            resultado_ia_text.config(state=tk.DISABLED)

        def actualizar_ui_con_error(
            mensaje_error, es_error_conexion=False
        ):  # Movida antes de su uso
            resultado_ia_text.config(state=tk.NORMAL)
            resultado_ia_text.delete("1.0", tk.END)
            resultado_ia_text.insert(
                "1.0", f"Error en la comunicación:\n{mensaje_error}"
            )
            resultado_ia_text.config(state=tk.DISABLED)
            status_var.set("Error de comunicación.")
            if not es_error_conexion:
                messagebox.showerror(
                    "Error de Comunicación con IA", mensaje_error, parent=dialog
                )
            copiar_btn.config(state=tk.DISABLED)
            guardar_docx_btn.config(state=tk.DISABLED)

        def solicitar_reformulacion():
            texto_hechos = hechos_entrada_text.get("1.0", tk.END).strip()
            if not texto_hechos:
                messagebox.showwarning(
                    "Entrada Vacía",
                    "Por favor, ingrese el texto de los hechos a reformular.",
                    parent=dialog,
                )
                return

            status_var.set("Procesando con Asistente IA local, por favor espere...")
            resultado_ia_text.config(state=tk.NORMAL)
            resultado_ia_text.delete("1.0", tk.END)
            resultado_ia_text.config(state=tk.DISABLED)
            dialog.update_idletasks()

            def do_request_thread():
                try:
                    mcp_url = "http://localhost:5000/api/reformular_hechos"
                    payload = {"texto_hechos": texto_hechos}
                    response = requests_module.post(mcp_url, json=payload, timeout=90)
                    response.raise_for_status()
                    resultado_json = response.json()
                    self.root.after(
                        0, lambda: actualizar_ui_con_respuesta(resultado_json)
                    )
                except requests_module.exceptions.ConnectionError:
                    error_msg = (
                        f"Error de Conexión: No se pudo conectar con el servidor del Asistente IA local en {mcp_url}.\n\n"
                        f"Verifique que:\n1. 'mcp_server.py' esté ejecutándose.\n"
                        f"2. Ollama/LM Studio esté activo y sirviendo el modelo correcto.\n"
                        f"3. No haya un firewall bloqueando la conexión a localhost en ese puerto."
                    )
                    self.root.after(
                        0,
                        lambda: actualizar_ui_con_error(
                            error_msg, es_error_conexion=True
                        ),
                    )
                except requests_module.exceptions.Timeout:
                    error_msg = (
                        f"Timeout: La solicitud al Asistente IA local en {mcp_url} tardó demasiado en responder (90s).\n\n"
                        f"Verifique el modelo LLM y la carga de su sistema."
                    )
                    self.root.after(0, lambda: actualizar_ui_con_error(error_msg))
                except requests_module.exceptions.HTTPError as http_err:
                    error_msg = f"Error HTTP {http_err.response.status_code} del servidor MCP: {http_err.response.text}"
                    self.root.after(0, lambda: actualizar_ui_con_error(error_msg))
                except requests_module.exceptions.JSONDecodeError:
                    error_msg = (
                        "Error: El servidor MCP no devolvió una respuesta JSON válida."
                    )
                    self.root.after(0, lambda: actualizar_ui_con_error(error_msg))
                except Exception as e_thread:
                    error_msg = f"Error inesperado durante la solicitud a la IA: {type(e_thread).__name__}: {e_thread}"
                    import traceback

                    traceback.print_exc()
                    self.root.after(0, lambda: actualizar_ui_con_error(error_msg))

            threading.Thread(target=do_request_thread, daemon=True).start()

        def copiar_resultado_ia():
            texto_a_copiar = resultado_ia_text.get("1.0", tk.END).strip()
            if texto_a_copiar:
                self.root.clipboard_clear()
                self.root.clipboard_append(texto_a_copiar)
                status_var.set("¡Resultado copiado al portapapeles!")
                # messagebox.showinfo("Copiado", "El resultado ha sido copiado.", parent=dialog) # Quizás mucho
            else:
                messagebox.showwarning(
                    "Nada que Copiar", "No hay resultado para copiar.", parent=dialog
                )

        def guardar_resultado_como_docx():
            texto_a_guardar = resultado_ia_text.get("1.0", tk.END).strip()
            if not texto_a_guardar:
                messagebox.showwarning(
                    "Nada que Guardar", "No hay resultado para guardar.", parent=dialog
                )
                return
            caso_actual_caratula_saneada = "Hechos_IA"
            if self.selected_case and self.selected_case.get("caratula"):
                nombre_base = re.sub(
                    r"[^\w\s-]", "", self.selected_case.get("caratula", "Caso")
                )
                nombre_base = re.sub(r"\s+", "_", nombre_base).strip("_")
                caso_actual_caratula_saneada = f"Hechos_IA_{nombre_base[:30]}"
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            suggested_filename = f"{caso_actual_caratula_saneada}_{timestamp}.docx"
            filepath = filedialog.asksaveasfilename(
                title="Guardar Hechos como DOCX",
                initialfile=suggested_filename,
                defaultextension=".docx",
                filetypes=[("Documento Word", "*.docx")],
                parent=dialog,
            )
            if filepath:
                try:
                    Document = docx_module.Document
                    WD_ALIGN_PARAGRAPH = docx_module.enum.text.WD_ALIGN_PARAGRAPH

                    doc = Document()
                    doc.add_paragraph(texto_a_guardar)
                    doc.save(filepath)
                    messagebox.showinfo(
                        "Documento Guardado",
                        f"Documento guardado en:\n{filepath}",
                        parent=dialog,
                    )
                    status_var.set(f"Guardado como {os.path.basename(filepath)}")
                    if messagebox.askyesno(
                        "Abrir Documento",
                        "¿Desea abrir el documento ahora?",
                        parent=dialog,
                    ):
                        if sys.platform == "win32":
                            os.startfile(filepath)
                        elif sys.platform == "darwin":
                            subprocess.call(["open", filepath])
                        else:
                            subprocess.call(["xdg-open", filepath])
                except ImportError:
                    messagebox.showerror(
                        "Error Librería",
                        "Falta 'python-docx'. Instálala con: pip install python-docx",
                        parent=dialog,
                    )
                except Exception as e_docx:
                    messagebox.showerror(
                        "Error al Guardar DOCX",
                        f"No se pudo guardar:\n{e_docx}",
                        parent=dialog,
                    )

        # --- FIN DEFINICIONES DE FUNCIONES ---

        button_frame_dialog = ttk.Frame(main_frame)
        button_frame_dialog.grid(row=5, column=0, pady=10, sticky=tk.EW)

        button_frame_dialog.columnconfigure(0, weight=1)
        button_frame_dialog.columnconfigure(1, weight=1)
        button_frame_dialog.columnconfigure(2, weight=1)
        button_frame_dialog.columnconfigure(3, weight=1)

        reformular_btn = ttk.Button(
            button_frame_dialog,
            text="Reformular con IA",
            command=solicitar_reformulacion,
        )
        reformular_btn.grid(row=0, column=0, padx=2, pady=2, sticky=tk.EW)

        copiar_btn = ttk.Button(
            button_frame_dialog,
            text="Copiar Resultado",
            command=copiar_resultado_ia,
            state=tk.DISABLED,
        )
        copiar_btn.grid(row=0, column=1, padx=2, pady=2, sticky=tk.EW)

        guardar_docx_btn = ttk.Button(
            button_frame_dialog,
            text="Guardar como DOCX",
            command=guardar_resultado_como_docx,
            state=tk.DISABLED,
        )
        guardar_docx_btn.grid(row=0, column=2, padx=2, pady=2, sticky=tk.EW)

        cerrar_btn = ttk.Button(
            button_frame_dialog, text="Cerrar", command=dialog.destroy
        )
        cerrar_btn.grid(row=0, column=3, padx=2, pady=2, sticky=tk.EW)

        hechos_entrada_text.focus_set()
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    # Necesitarás añadir un método para guardar la interacción si quieres ese botón
    def _guardar_interaccion_ia_como_actividad(
        self, caso_id, tipo_consulta, consulta, respuesta_ia
    ):
        if not caso_id:
            return
        descripcion_completa = f"CONSULTA A IA ({tipo_consulta}):\n{consulta}\n\nRESPUESTA IA:\n{respuesta_ia}"
        # Llamar a tu función _save_new_actividad o db.add_actividad_caso
        self._save_new_actividad(
            caso_id, f"Asistencia IA - {tipo_consulta}", descripcion_completa
        )
        print(f"Interacción con IA guardada como actividad en caso ID {caso_id}")

    def crear_copia_de_seguridad(self):
        """
        Realiza un backup de la base de datos PostgreSQL usando la herramienta pg_dump.
        """
        print("Iniciando proceso de backup de la base de datos PostgreSQL...")

        # --- 1. Definir la ruta a pg_dump ---
        # Idealmente, esta ruta debería estar en una configuración, pero por ahora la ponemos aquí.
        # ¡¡¡IMPORTANTE!!! Revisa si esta es la ruta correcta en tu sistema.
        pg_dump_path = r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"  # Usa 16, 17 o la que tengas

        if not os.path.exists(pg_dump_path):
            messagebox.showerror(
                "Error de Backup",
                f"No se encontró la herramienta 'pg_dump.exe' en la ruta:\n{pg_dump_path}\n\n"
                "Por favor, verifica la ruta en el código de main_app.py.",
            )
            return

        # --- 2. Leer la configuración de la base de datos desde config.ini ---
        try:
            config = configparser.ConfigParser()
            config.read("config.ini")
            db_config = config["postgresql"]
            db_name = db_config["database"]
            db_user = db_config["user"]
            db_pass = db_config["password"]
            db_host = db_config["host"]
        except Exception as e:
            messagebox.showerror(
                "Error de Configuración",
                f"No se pudo leer la configuración de la base de datos desde config.ini: {e}",
            )
            return

        # --- 3. Definir el nombre y la ruta del archivo de backup ---
        backup_folder = "backups"
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"backup_{db_name}_{timestamp}.sql"
        backup_filepath = os.path.join(backup_folder, backup_filename)

        # --- 4. Construir y ejecutar el comando pg_dump ---
        # (Esto requiere que la contraseña se pase a través de una variable de entorno por seguridad)
        command = [
            pg_dump_path,
            "--host",
            db_host,
            "--username",
            db_user,
            "--dbname",
            db_name,
            "--file",
            backup_filepath,
            "--format",
            "c",  # Formato custom, comprimido y robusto
            "--blobs",
            "--verbose",
        ]

        try:
            # Establecer la variable de entorno para la contraseña
            env = os.environ.copy()
            env["PGPASSWORD"] = db_pass

            print(f"Ejecutando comando de backup: {' '.join(command)}")
            # Usamos subprocess.run para ejecutar el comando externo
            result = subprocess.run(
                command, capture_output=True, text=True, check=True, env=env
            )

            print("Salida de pg_dump:", result.stdout)
            print("Errores de pg_dump:", result.stderr)

            messagebox.showinfo(
                "Backup Exitoso",
                f"El backup de la base de datos se ha guardado exitosamente en:\n{backup_filepath}",
            )

        except subprocess.CalledProcessError as e:
            print("--- ERROR DURANTE EL BACKUP ---")
            print("Comando:", e.cmd)
            print("Código de Salida:", e.returncode)
            print("Salida (stdout):", e.stdout)
            print("Error (stderr):", e.stderr)
            messagebox.showerror(
                "Error de Backup",
                f"Falló la ejecución de pg_dump. Revisa la consola para más detalles.\n\nError: {e.stderr}",
            )
        except Exception as e:
            messagebox.showerror(
                "Error Inesperado",
                f"Ocurrió un error inesperado durante el backup: {e}",
            )

    def open_prospects_window(self):
        """Abre la ventana de gestión de prospectos"""
        try:
            from prospects_window import ProspectsWindow

            ProspectsWindow(self)
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo abrir la ventana de prospectos:\n{str(e)}"
            )
            print(f"Error abriendo ventana de prospectos: {e}")

    def _abrir_generador_reportes(self):
        """Abre la ventana del generador de reportes"""
        try:
            ReportGeneratorWindow = get_report_generator_window()
            ReportGeneratorWindow(self)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el generador de reportes:\n{str(e)}",
                parent=self.root,
            )
            print(f"Error abriendo generador de reportes: {e}")
            import traceback
            traceback.print_exc()

    def _abrir_gestor_de_contactos(self):
        """Abre la ventana del gestor de contactos"""
        try:
            open_contactos_manager = get_contactos_manager()
            open_contactos_manager(self.root)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el gestor de contactos:\n{str(e)}",
                parent=self.root,
            )
            print(f"Error abriendo gestor de contactos: {e}")
            import traceback
            traceback.print_exc()

    def _abrir_modelos_escritos(self):
        """Abre la ventana de modelos de escritos"""
        try:
            from modelos_escritos_manager import ModelosEscritosManager
            modelos_manager = ModelosEscritosManager()
            
            # Obtener caso seleccionado si existe
            case_id = None
            if hasattr(self, 'selected_case') and self.selected_case:
                case_id = self.selected_case.get('id')
            
            modelos_manager.open_modelos_manager_window(self.root, case_id)
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el módulo de modelos de escritos:\n{str(e)}",
                parent=self.root,
            )
            print(f"Error abriendo modelos de escritos: {e}")
            import traceback
            traceback.print_exc()

    def _abrir_carpeta_modelos(self):
        """Abre la carpeta de modelos de escritos en el explorador"""
        try:
            import os
            import subprocess
            import platform
            
            models_path = os.path.abspath("modelos_escritos")
            
            # Crear carpeta si no existe
            if not os.path.exists(models_path):
                os.makedirs(models_path)
            
            # Abrir en explorador según el sistema operativo
            if platform.system() == "Windows":
                subprocess.run(["explorer", models_path])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", models_path])
            else:  # Linux
                subprocess.run(["xdg-open", models_path])
                
            print(f"Carpeta de modelos abierta: {models_path}")
            
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la carpeta de modelos:\n{str(e)}",
                parent=self.root,
            )
            print(f"Error abriendo carpeta de modelos: {e}")

    def cerrar_aplicacion_directamente(self):
        if messagebox.askokcancel(
            "Confirmar Salida",
            "¿Estás seguro de que quieres cerrar completamente la aplicación?",
            parent=self.root,
        ):
            self.cerrar_aplicacion()

    def cerrar_aplicacion(self):
        """Cierre limpio de la aplicación."""
        print("Iniciando secuencia de cierre de la aplicación...")

        # Detener pystray ANTES de cerrar Tkinter
        if hasattr(self, 'tray_icon') and self.tray_icon:
            print("Deteniendo icono de bandeja explícitamente...")
            try:
                self.tray_icon.stop()
            except Exception as e:
                print(f"Error al detener icono de bandeja: {e}")

        # Detener hilos de fondo
        if hasattr(self, 'stop_event_recordatorios'):
            print("Deteniendo hilo de recordatorios...")
            self.stop_event_recordatorios.set()

        if hasattr(self, 'stop_event_inactividad'):
            print("Deteniendo hilo de inactividad...")
            self.stop_event_inactividad.set()

        # Cerrar la aplicación
        self.root.quit()
        self.root.destroy()
        print("Solicitud de cierre completada.")

    # --- MÉTODOS AUXILIARES PARA INTEGRACIÓN CON AGENTE IA ---

    def _show_mediation_agreement_dialog(self, case_caratula: str) -> Optional[Dict[str, Any]]:
        """
        Muestra un diálogo para ingresar los datos del acuerdo de mediación.

        Args:
            case_caratula: Carátula del caso

        Returns:
            Dict con los datos del acuerdo o None si se canceló
        """
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Datos del Acuerdo de Mediación - {case_caratula[:50]}...")
        dialog.transient(self.root)
        dialog.grab_set()

        # Centrar diálogo
        dialog_width = 500
        dialog_height = 400
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        x_pos = parent_x + (parent_width - dialog_width) // 2
        y_pos = parent_y + (parent_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x_pos}+{y_pos}")

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # Variables
        monto_var = tk.StringVar()
        plazo_var = tk.StringVar()
        banco_var = tk.StringVar()
        cbu_var = tk.StringVar()
        alias_var = tk.StringVar()
        cuit_var = tk.StringVar()

        row_idx = 0

        # Caso
        ttk.Label(frame, text="Caso:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Label(frame, text=case_caratula, wraplength=300).grid(row=row_idx, column=1, sticky=tk.W, pady=3, padx=5)
        row_idx += 1

        # Monto
        ttk.Label(frame, text="*Monto Compensación:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Entry(frame, textvariable=monto_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # Plazo
        ttk.Label(frame, text="*Plazo (días):").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Entry(frame, textvariable=plazo_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # Banco
        ttk.Label(frame, text="*Banco:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Entry(frame, textvariable=banco_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # CBU
        ttk.Label(frame, text="*CBU:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Entry(frame, textvariable=cbu_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # Alias
        ttk.Label(frame, text="*Alias:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Entry(frame, textvariable=alias_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # CUIT
        ttk.Label(frame, text="*CUIT:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        ttk.Entry(frame, textvariable=cuit_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=20, sticky=tk.E)

        result = {"cancelled": True}

        def on_accept():
            # Validar campos obligatorios
            if not all([monto_var.get(), plazo_var.get(), banco_var.get(),
                       cbu_var.get(), alias_var.get(), cuit_var.get()]):
                messagebox.showerror("Error", "Todos los campos marcados con * son obligatorios.", parent=dialog)
                return

            result.update({
                "cancelled": False,
                "monto_compensacion_numeros": monto_var.get(),
                "plazo_pago_dias": plazo_var.get(),
                "banco_actor": banco_var.get(),
                "cbu_actor": cbu_var.get(),
                "alias_actor": alias_var.get(),
                "cuit_actor": cuit_var.get()
            })
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ttk.Button(button_frame, text="Generar Acuerdo", command=on_accept).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=on_cancel).pack(side=tk.LEFT, padx=5)

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)
        dialog.wait_window(dialog)

        return None if result["cancelled"] else result

    def _show_progress_window(self, title: str, message: str) -> tk.Toplevel:
        """
        Muestra una ventana de progreso modal.

        Args:
            title: Título de la ventana
            message: Mensaje a mostrar

        Returns:
            tk.Toplevel: La ventana de progreso creada
        """
        progress_window = tk.Toplevel(self.root)
        progress_window.title(title)
        progress_window.transient(self.root)
        progress_window.grab_set()

        # Centrar ventana
        window_width = 300
        window_height = 100
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        x_pos = parent_x + (parent_width - window_width) // 2
        y_pos = parent_y + (parent_height - window_height) // 2
        progress_window.geometry(f"{window_width}x{window_height}+{x_pos}+{y_pos}")

        frame = ttk.Frame(progress_window, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=message, wraplength=250).pack(pady=10)
        progress_bar = ttk.Progressbar(frame, mode='indeterminate')
        progress_bar.pack(fill=tk.X, pady=5)
        progress_bar.start()

        return progress_window

    def _show_agreement_result(self, result: Dict[str, Any], case_caratula: str):
        """
        Muestra el resultado de la generación del acuerdo.

        Args:
            result: Resultado de la generación
            case_caratula: Carátula del caso
        """
        if result["success"]:
            messagebox.showinfo(
                "Éxito",
                f"Acuerdo de mediación generado exitosamente para:\n{case_caratula}\n\n"
                "El resultado ha sido guardado como actividad en el seguimiento del caso.",
                parent=self.root
            )
        else:
            messagebox.showerror(
                "Error",
                f"Error generando acuerdo para:\n{case_caratula}\n\n"
                f"Error: {result.get('error', 'Error desconocido')}",
                parent=self.root
            )

    def _show_agreement_error(self, error: str, case_caratula: str):
        """
        Muestra un error de generación del acuerdo.

        Args:
            error: Mensaje de error
            case_caratula: Carátula del caso
        """
        messagebox.showerror(
            "Error",
            f"Error generando acuerdo para:\n{case_caratula}\n\n{error}",
            parent=self.root
        )

    # --- Métodos de Lógica CRM (Clientes y Casos) ---

    # REFACTORIZADO: Método movido a CaseManager

    def clear_case_details(self):
        self.disable_case_buttons()
        # También nos aseguramos de que el botón de agregar audiencia se actualice.
        self.update_add_audiencia_button_state()

    def enable_case_buttons(self):
        self.edit_case_btn.config(state=tk.NORMAL)
        self.delete_case_btn.config(state=tk.NORMAL)
        self.mediacion_btn.config(state=tk.NORMAL)

    def disable_case_buttons(self):
        self.edit_case_btn.config(state=tk.DISABLED)
        self.delete_case_btn.config(state=tk.DISABLED)
        self.mediacion_btn.config(state=tk.DISABLED)

    def generar_acuerdo_mediacion(self):
        """Genera un acuerdo de mediación usando el agente IA con datos precargados del caso."""
        if not self.selected_case:
            messagebox.showwarning(
                "Advertencia",
                "Seleccione un caso para generar el acuerdo de mediación.",
                parent=self.root
            )
            return

        case_id = self.selected_case['id']
        case_caratula = self.selected_case.get('caratula', f'ID {case_id}')

        try:
            print(f"[AGENTE] Generando acuerdo de mediación para caso {case_id}: {case_caratula}")

            # Mostrar diálogo para obtener datos del acuerdo
            agreement_data = self._show_mediation_agreement_dialog(case_caratula)

            if not agreement_data:
                print("[AGENTE] Usuario canceló la generación del acuerdo")
                return

            # Mostrar progreso
            progress_window = self._show_progress_window("Generando Acuerdo de Mediación",
                                                        f"Procesando caso: {case_caratula}")

            def generate_agreement_thread():
                try:
                    # Importar y usar la integración del agente
                    from agent_integration import create_mediation_agreement

                    # Generar el acuerdo usando el agente con datos precargados del caso
                    result = create_mediation_agreement(case_id, agreement_data)

                    # Cerrar ventana de progreso
                    self.root.after(0, progress_window.destroy)

                    # Mostrar resultado
                    self.root.after(0, lambda: self._show_agreement_result(result, case_caratula))

                except Exception as e:
                    # Cerrar ventana de progreso
                    self.root.after(0, progress_window.destroy)

                    # Mostrar error
                    self.root.after(0, lambda: self._show_agreement_error(str(e), case_caratula))

            # Ejecutar en hilo separado para no bloquear la UI
            import threading
            thread = threading.Thread(target=generate_agreement_thread, daemon=True)
            thread.start()

        except Exception as e:
            print(f"[ERROR] Error generando acuerdo de mediación: {e}")
            messagebox.showerror(
                "Error",
                f"Error generando acuerdo de mediación:\n{str(e)}",
                parent=self.root
            )

    # enable_detail_tabs_for_case y disable_detail_tabs_for_case ya no son necesarios
    # porque el notebook principal ha sido eliminado.

    # --- MÉTODOS RELACIONADOS CON DOCUMENTOS (AHORA PARA USO DE DOCUMENTOS_TAB_UI) ---
    # Estos métodos son llamados por DocumentosTab y operan sobre el treeview que se les pasa.

    def clear_document_list_for_tab(self, document_tree_widget):
        """Limpia un treeview de documentos específico (usado por DocumentosTab)."""
        if document_tree_widget:
            for i in document_tree_widget.get_children():
                document_tree_widget.delete(i)

    def load_case_documents_for_tab(
        self, document_tree_widget, folder_path, case_data_for_tab
    ):
        """Carga documentos en un treeview específico (usado por DocumentosTab)."""
        if not document_tree_widget or not case_data_for_tab:
            return

        self.clear_document_list_for_tab(document_tree_widget)

        # current_folder_for_display = folder_path # No es necesario aquí, se maneja en DocumentosTab
        if folder_path and os.path.isdir(folder_path):
            try:
                # Botón para subir un nivel
                # case_data_for_tab es el case_data específico para la instancia de CaseDetailWindow
                if folder_path != case_data_for_tab.get("ruta_carpeta"):
                    parent_dir = os.path.dirname(folder_path)
                    root_case_folder = case_data_for_tab.get("ruta_carpeta", "")
                    if (
                        parent_dir
                        and os.path.isdir(parent_dir)
                        and parent_dir != folder_path
                        and (
                            parent_dir == root_case_folder
                            or parent_dir.startswith(root_case_folder + os.sep)
                        )
                    ):
                        document_tree_widget.insert(
                            "",
                            0,
                            values=("[..] Subir Nivel", "Carpeta", ""),
                            iid=parent_dir,
                            tags=("parent_folder",),
                        )

                for entry in sorted(
                    os.scandir(folder_path), key=lambda e: e.name.lower()
                ):
                    if entry.is_dir():
                        # ... (lógica de inserción de directorio igual que antes, usando document_tree_widget)
                        try:
                            stat_info = entry.stat()
                            mod_time = datetime.datetime.fromtimestamp(
                                stat_info.st_mtime
                            ).strftime("%Y-%m-%d %H:%M")
                            document_tree_widget.insert(
                                "",
                                tk.END,
                                values=(f"[CARPETA] {entry.name}", "Carpeta", mod_time),
                                iid=entry.path,
                                tags=("folder",),
                            )
                        except OSError as e:
                            print(
                                f"Warn: No se pudo leer info de carpeta {entry.path}: {e}"
                            )
                        except Exception as e:
                            print(f"Error procesando carpeta {entry.path}: {e}")
                    elif entry.is_file():
                        # ... (lógica de inserción de archivo igual que antes, usando document_tree_widget)
                        try:
                            stat_info = entry.stat()
                            size_bytes = stat_info.st_size
                            if size_bytes < 1024:
                                size_display = f"{size_bytes} B"
                            elif size_bytes < 1024**2:
                                size_display = f"{size_bytes/1024:.1f} KB"
                            # ... (resto de la lógica de tamaño) ...
                            else:
                                size_display = f"{size_bytes/1024**3:.1f} GB"
                            mod_time = datetime.datetime.fromtimestamp(
                                stat_info.st_mtime
                            ).strftime("%Y-%m-%d %H:%M")
                            document_tree_widget.insert(
                                "",
                                tk.END,
                                values=(entry.name, size_display, mod_time),
                                iid=entry.path,
                                tags=("file",),
                            )
                        except OSError as e:
                            print(
                                f"Warn: No se pudo leer info de archivo {entry.path}: {e}"
                            )
                        except Exception as e:
                            print(f"Error procesando archivo {entry.path}: {e}")
            except OSError as e:
                document_tree_widget.insert(
                    "",
                    tk.END,
                    values=(f"Error al leer dir: {e}", "", ""),
                    iid="error_dir_listing",
                )
            except Exception as e:
                document_tree_widget.insert(
                    "",
                    tk.END,
                    values=("Error inesperado al listar", "", ""),
                    iid="error_unexpected_listing",
                )
        elif case_data_for_tab:  # Si no hay folder_path pero sí hay case_data
            document_tree_widget.insert(
                "",
                tk.END,
                values=("Carpeta no asignada o no encontrada.", "", ""),
                iid="no_folder_or_invalid",
            )

    def select_case_folder_from_tab(self, case_id_for_tab, current_folder_path):
        """Permite seleccionar una carpeta para el caso, llamado desde DocumentosTab."""
        # Esta función podría mantenerse si DocumentosTab la necesita para actualizar la BD
        # y luego recargar sus propios documentos.
        # Devuelve la nueva ruta seleccionada o None.
        initial_dir = current_folder_path or os.path.expanduser("~")
        folder_selected = filedialog.askdirectory(
            initialdir=initial_dir,
            title="Seleccionar Carpeta de Documentos del Caso",
            parent=self.root,
        )  # Parent podría ser la Toplevel
        if folder_selected:
            if db.update_case_folder(case_id_for_tab, folder_selected):
                # La actualización en self.selected_case (si es el mismo) se maneja al recargar
                messagebox.showinfo(
                    "Éxito",
                    "Carpeta de documentos asignada con éxito.",
                    parent=self.root,
                )
                return folder_selected
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo guardar la ruta de la carpeta en la BD.",
                    parent=self.root,
                )
        return None

    def open_case_folder_from_tab(self, case_data_for_tab):
        """Abre la carpeta del caso, llamado desde DocumentosTab."""
        if not case_data_for_tab or not case_data_for_tab.get("ruta_carpeta"):
            messagebox.showwarning(
                "Advertencia", "Caso sin carpeta asignada.", parent=self.root
            )  # Parent podría ser Toplevel
            return
        folder_path = case_data_for_tab.get("ruta_carpeta")
        # ... (resto de la lógica de open_case_folder igual que antes) ...
        if folder_path and os.path.isdir(folder_path):
            try:
                if sys.platform == "win32":
                    os.startfile(folder_path)
                elif sys.platform == "darwin":
                    subprocess.call(["open", folder_path])
                else:
                    subprocess.call(["xdg-open", folder_path])
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo abrir la carpeta:\n{e}", parent=self.root
                )
        else:
            messagebox.showwarning(
                "Advertencia", "Ruta de carpeta inválida.", parent=self.root
            )

    def on_document_double_click_from_tab(
        self, event, document_tree_widget, case_id_for_tab, case_data_for_tab
    ):
        """Maneja doble clic en el treeview de documentos de una pestaña."""
        if not document_tree_widget:
            return
        item_id = document_tree_widget.identify_row(event.y)
        if not item_id:
            return

        path_to_open = item_id
        item_tags = document_tree_widget.item(item_id, "tags")

        if "file" in item_tags and os.path.isfile(path_to_open):
            # ... (lógica de abrir archivo y registrar actividad igual que antes) ...
            try:
                if sys.platform == "win32":
                    os.startfile(path_to_open)
                # ... (resto de plataformas) ...
                else:
                    subprocess.call(["xdg-open", path_to_open])
                if case_id_for_tab:
                    # ... (registrar actividad) ...
                    file_name = os.path.basename(path_to_open)
                    self._save_new_actividad(
                        caso_id=case_id_for_tab,
                        tipo_actividad="Documento Abierto (Toplevel)",  # Indicar que fue desde Toplevel
                        descripcion=f"Se abrió el documento: {file_name}",
                        referencia_doc=file_name,
                    )
            except Exception as e:
                messagebox.showerror(
                    "Error al abrir archivo",
                    f"No se pudo abrir:\n{e}",
                    parent=self.root,
                )

        elif ("folder" in item_tags or "parent_folder" in item_tags) and os.path.isdir(
            path_to_open
        ):
            print(
                f"Navegando a carpeta (en Toplevel): {path_to_open}. DocumentosTab debe recargar."
            )
            # En DocumentosTab, el on_document_double_click debería hacer:
            # if 'folder' in item_tags: self.load_case_documents(path_to_open)

    # --- FIN MÉTODOS DOCUMENTOS PARA PESTAÑA ---

    # --- NUEVOS MÉTODOS PARA DIÁLOGOS Y LÓGICA DE TAREAS ---

    def open_tarea_dialog(self, tarea_id=None, caso_id=None):
        """Abre el diálogo para agregar o editar una tarea."""
        print(
            f"[open_tarea_dialog] Iniciando. tarea_id: {tarea_id}, caso_id: {caso_id}"
        )

        # Determinar el caso_id y nombre del caso para el título y asociación
        current_caso_id = None
        case_display_name = "Tarea General"  # Por defecto si no hay caso

        if tarea_id:  # Editando tarea existente
            tarea_data_dict = self.db_crm.get_tarea_by_id(tarea_id)
            if not tarea_data_dict:
                messagebox.showerror(
                    "Error",
                    f"No se pudo cargar la tarea ID {tarea_id}.",
                    parent=self.root,
                )
                return
            current_caso_id = tarea_data_dict.get("caso_id")
            if current_caso_id:
                case_info = self.db_crm.get_case_by_id(current_caso_id)
                case_display_name = (
                    case_info.get("caratula", f"ID {current_caso_id}")
                    if case_info
                    else f"ID {current_caso_id}"
                )
            dialog_title = f"Editar Tarea ID: {tarea_id}"
        elif caso_id:  # Nueva tarea para un caso específico (pasado desde TareasTab)
            current_caso_id = caso_id
            case_info = self.db_crm.get_case_by_id(current_caso_id)
            case_display_name = (
                case_info.get("caratula", f"ID {current_caso_id}")
                if case_info
                else f"ID {current_caso_id}"
            )
            dialog_title = f"Agregar Tarea a Caso: {case_display_name[:40]}"
            tarea_data_dict = {}  # Vacío para nueva tarea
        elif self.selected_case:  # Nueva tarea, caso seleccionado en la UI principal
            current_caso_id = self.selected_case["id"]
            case_display_name = self.selected_case.get(
                "caratula", f"ID {current_caso_id}"
            )
            dialog_title = f"Agregar Tarea a Caso: {case_display_name[:40]}"
            tarea_data_dict = {}
        else:  # Nueva tarea general (si se implementa esta lógica en TareasTab)
            dialog_title = "Agregar Tarea General"
            tarea_data_dict = {}
            # current_caso_id permanece None

        dialog = Toplevel(self.root)
        dialog.title(dialog_title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(
            True, True
        )  # Permitir redimensionar por el campo de notas/descripción

        # Geometría y centrado
        dialog_width = 550
        dialog_height = 580  # Ajustar según necesidad
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        x_pos = parent_x + (parent_width - dialog_width) // 2
        y_pos = parent_y + (parent_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x_pos}+{y_pos}")
        dialog.minsize(dialog_width - 100, dialog_height - 150)

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(expand=True, fill=tk.BOTH)
        frame.columnconfigure(1, weight=1)  # Columna de widgets expandible

        # Variables de Tkinter para los campos
        descripcion_var = tk.StringVar(
            value=tarea_data_dict.get("descripcion", "")
        )  # Se usará con Text

        # Fecha de Vencimiento
        fecha_venc_str = tarea_data_dict.get("fecha_vencimiento", "")
        # DateEntry necesita un objeto date, o None si está vacío.
        fecha_venc_dt_obj = None
        if fecha_venc_str:
            try:
                fecha_venc_dt_obj = datetime.datetime.strptime(
                    fecha_venc_str, "%Y-%m-%d"
                ).date()
            except ValueError:
                print(
                    f"Advertencia: Fecha de vencimiento '{fecha_venc_str}' con formato incorrecto, se ignora."
                )

        prioridad_var = tk.StringVar(value=tarea_data_dict.get("prioridad", "Media"))
        estado_var = tk.StringVar(value=tarea_data_dict.get("estado", "Pendiente"))
        notas_var = tk.StringVar(
            value=tarea_data_dict.get("notas", "")
        )  # Se usará con Text
        es_plazo_var = tk.IntVar(value=tarea_data_dict.get("es_plazo_procesal", 0))
        recordatorio_activo_var = tk.IntVar(
            value=tarea_data_dict.get("recordatorio_activo", 0)
        )
        recordatorio_dias_var = tk.IntVar(
            value=tarea_data_dict.get("recordatorio_dias_antes", 1)
        )

        # Creación de Widgets del Diálogo
        row_idx = 0
        if current_caso_id:
            ttk.Label(frame, text="Caso Asociado:").grid(
                row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
            )
            ttk.Label(frame, text=case_display_name, wraplength=350).grid(
                row=row_idx, column=1, sticky=tk.W, pady=3, padx=5
            )
            row_idx += 1

        ttk.Label(frame, text="*Descripción:").grid(
            row=row_idx, column=0, sticky=tk.NW, pady=(5, 2), padx=5
        )
        desc_text_frame = ttk.Frame(frame)
        desc_text_frame.grid(row=row_idx, column=1, sticky=tk.NSEW, pady=2, padx=5)
        desc_text_frame.columnconfigure(0, weight=1)
        desc_text_frame.rowconfigure(0, weight=1)
        desc_text_widget = tk.Text(desc_text_frame, height=5, width=40, wrap=tk.WORD)
        desc_text_widget.grid(row=0, column=0, sticky="nsew")
        desc_scroll = ttk.Scrollbar(
            desc_text_frame, orient=tk.VERTICAL, command=desc_text_widget.yview
        )
        desc_scroll.grid(row=0, column=1, sticky="ns")
        desc_text_widget["yscrollcommand"] = desc_scroll.set
        desc_text_widget.insert("1.0", tarea_data_dict.get("descripcion", ""))
        frame.rowconfigure(row_idx, weight=1)  # Permitir que descripción se expanda
        row_idx += 1

        ttk.Label(frame, text="Fecha Vencimiento:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        # Usar DateEntry de tkcalendar
        # Si fecha_venc_dt_obj es None, DateEntry se mostrará sin fecha seleccionada.
        # Al leerlo, si no hay fecha, get_date() podría dar error o un valor que hay que manejar.
        # O podemos usar un Entry simple y validar el formato YYYY-MM-DD
        fecha_venc_entry = DateEntry(
            frame,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="dd-mm-y",
            locale="es_ES",
        )
        if fecha_venc_dt_obj:
            fecha_venc_entry.set_date(fecha_venc_dt_obj)
        else:
            pass  # Se deja el DateEntry como está, el usuario debe seleccionar o dejar la actual.
        fecha_venc_entry.grid(row=row_idx, column=1, sticky=tk.W, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Prioridad:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        prioridades = ["Alta", "Media", "Baja"]
        ttk.Combobox(
            frame,
            textvariable=prioridad_var,
            values=prioridades,
            state="readonly",
            width=15,
        ).grid(row=row_idx, column=1, sticky=tk.W, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Estado:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        estados = ["Pendiente", "En Progreso", "Completada", "Cancelada"]
        # Si es una nueva tarea, el estado "Completada" o "Cancelada" no debería ser una opción inicial común.
        # Pero para editar, sí.
        estado_combo = ttk.Combobox(
            frame, textvariable=estado_var, values=estados, state="readonly", width=15
        )
        estado_combo.grid(row=row_idx, column=1, sticky=tk.W, pady=3, padx=5)
        row_idx += 1

        ttk.Checkbutton(frame, text="¿Es Plazo Procesal?", variable=es_plazo_var).grid(
            row=row_idx, column=0, columnspan=2, sticky=tk.W, pady=3, padx=5
        )
        row_idx += 1

        # Sección Recordatorio
        rec_frame_tarea = ttk.LabelFrame(frame, text="Recordatorio")
        rec_frame_tarea.grid(
            row=row_idx, column=0, columnspan=2, sticky=tk.EW, pady=5, padx=5
        )
        ttk.Checkbutton(
            rec_frame_tarea,
            text="Activar Recordatorio",
            variable=recordatorio_activo_var,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Label(rec_frame_tarea, text="Días antes:").pack(side=tk.LEFT, padx=(10, 2))
        ttk.Spinbox(
            rec_frame_tarea, from_=0, to=30, width=3, textvariable=recordatorio_dias_var
        ).pack(side=tk.LEFT, padx=2)
        row_idx += 1

        ttk.Label(frame, text="Notas Adicionales:").grid(
            row=row_idx, column=0, sticky=tk.NW, pady=(5, 2), padx=5
        )
        notas_text_frame = ttk.Frame(frame)
        notas_text_frame.grid(row=row_idx, column=1, sticky=tk.NSEW, pady=2, padx=5)
        notas_text_frame.columnconfigure(0, weight=1)
        notas_text_frame.rowconfigure(0, weight=1)
        notas_text_widget_dialog = tk.Text(
            notas_text_frame, height=4, width=40, wrap=tk.WORD
        )
        notas_text_widget_dialog.grid(row=0, column=0, sticky="nsew")
        notas_scroll_dialog = ttk.Scrollbar(
            notas_text_frame, orient=tk.VERTICAL, command=notas_text_widget_dialog.yview
        )
        notas_scroll_dialog.grid(row=0, column=1, sticky="ns")
        notas_text_widget_dialog["yscrollcommand"] = notas_scroll_dialog.set
        notas_text_widget_dialog.insert("1.0", tarea_data_dict.get("notas", ""))
        frame.rowconfigure(row_idx, weight=1)  # Permitir que notas se expanda
        row_idx += 1

        button_frame_dialog = ttk.Frame(frame)
        button_frame_dialog.grid(
            row=row_idx, column=0, columnspan=2, pady=15, sticky=tk.E
        )

        def on_save_wrapper():
            # Obtener fecha de DateEntry. Si no se seleccionó, get_date() podría dar error.
            # O si el DateEntry no está "presente" (ej. por un check), no intentar obtenerla.
            fecha_venc_final_str = None
            try:
                # DateEntry devuelve un objeto date de Python. Convertir a YYYY-MM-DD string.
                fecha_venc_dt = fecha_venc_entry.get_date()
                fecha_venc_final_str = fecha_venc_dt.strftime("%Y-%m-%d")
            except Exception:
                pass

            self._save_tarea(
                tarea_id=tarea_id,
                caso_id=current_caso_id,
                descripcion=desc_text_widget.get("1.0", tk.END).strip(),
                fecha_vencimiento=fecha_venc_final_str,  # Usar el string formateado o None
                prioridad=prioridad_var.get(),
                estado=estado_var.get(),
                notas=notas_text_widget_dialog.get("1.0", tk.END).strip(),
                es_plazo_procesal=es_plazo_var.get(),
                recordatorio_activo=recordatorio_activo_var.get(),
                recordatorio_dias_antes=recordatorio_dias_var.get(),
                dialog=dialog,
            )

        ttk.Button(
            button_frame_dialog, text="Guardar Tarea", command=on_save_wrapper
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame_dialog, text="Cancelar", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

        desc_text_widget.focus_set()  # Foco en el primer campo útil
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        self.root.wait_window(dialog)

    def _save_tarea(
        self,
        tarea_id,
        caso_id,
        descripcion,
        fecha_vencimiento,
        prioridad,
        estado,
        notas,
        es_plazo_procesal,
        recordatorio_activo,
        recordatorio_dias_antes,
        dialog,
    ):
        if not descripcion.strip():
            messagebox.showerror(
                "Validación",
                "La descripción de la tarea es obligatoria.",
                parent=dialog,
            )
            return

        # Podríamos añadir más validaciones aquí (ej. formato de fecha si no usamos DateEntry)

        success = False
        msg_op = ""

        if tarea_id is None:  # Nueva tarea
            new_id = self.db_crm.add_tarea(
                descripcion=descripcion,
                caso_id=caso_id,
                fecha_vencimiento=fecha_vencimiento,
                prioridad=prioridad,
                estado=estado,
                notas=notas,
                es_plazo_procesal=es_plazo_procesal,
                recordatorio_activo=recordatorio_activo,
                recordatorio_dias_antes=recordatorio_dias_antes,
            )
            success = new_id is not None
            msg_op = "agregada"
        else:  # Editar tarea
            success = self.db_crm.update_tarea(
                tarea_id=tarea_id,
                descripcion=descripcion,
                fecha_vencimiento=fecha_vencimiento,
                prioridad=prioridad,
                estado=estado,
                notas=notas,
                es_plazo_procesal=es_plazo_procesal,
                recordatorio_activo=recordatorio_activo,
                recordatorio_dias_antes=recordatorio_dias_antes,
            )
            msg_op = "actualizada"
            # Nota: update_tarea en crm_database ya maneja si hay cambios o no.

        if success:
            messagebox.showinfo("Éxito", f"Tarea {msg_op} con éxito.", parent=self.root)
            dialog.destroy()
            # Recargar la lista de tareas en la pestaña correspondiente
            if hasattr(self, "tareas_tab_frame"):
                if (
                    caso_id
                ):  # Si la tarea está asociada a un caso, recargar las tareas de ese caso
                    self.tareas_tab_frame.load_tareas(caso_id=caso_id)
                # else:
                # Si implementamos una vista de "todas las tareas", recargar esa vista.
                # self.tareas_tab_frame.load_tareas(mostrar_solo_pendientes_activas=True)
        else:
            messagebox.showerror(
                "Error",
                f"No se pudo {msg_op} la tarea. Verifique la consola.",
                parent=dialog,
            )

    def marcar_tarea_como_completada(self, tarea_id, caso_id_asociado):
        """Cambia el estado de la tarea seleccionada a 'Completada'."""
        if not tarea_id:
            messagebox.showwarning(
                "Aviso", "No hay tarea seleccionada.", parent=self.root
            )
            return

        # Confirmación opcional
        # if not messagebox.askyesno("Confirmar", "¿Marcar esta tarea como completada?", parent=self.root):
        # return

        # Obtenemos la descripción para el mensaje de éxito, aunque no es estrictamente necesario
        tarea_data = self.db_crm.get_tarea_by_id(tarea_id)
        desc_corta = (
            tarea_data.get("descripcion", f"ID {tarea_id}")[:30]
            if tarea_data
            else f"ID {tarea_id}"
        )

        success = self.db_crm.update_tarea(tarea_id=tarea_id, estado="Completada")

        if success:
            messagebox.showinfo(
                "Tarea Completada",
                f"Tarea '{desc_corta}...' marcada como completada.",
                parent=self.root,
            )
            if hasattr(self, "tareas_tab_frame"):
                # Recargar la lista de tareas del caso actual o la vista global
                if self.selected_case and self.selected_case["id"] == caso_id_asociado:
                    self.tareas_tab_frame.load_tareas(caso_id=self.selected_case["id"])
                elif (
                    caso_id_asociado
                ):  # Si la tarea era de otro caso (no debería pasar si el botón depende de selección)
                    self.tareas_tab_frame.load_tareas(caso_id=caso_id_asociado)
                # else:
                # self.tareas_tab_frame.load_tareas(mostrar_solo_pendientes_activas=True) # Para vista global
        else:
            messagebox.showerror(
                "Error",
                "No se pudo actualizar el estado de la tarea.",
                parent=self.root,
            )

    def delete_selected_tarea(self, tarea_id, caso_id_asociado):
        """Elimina la tarea seleccionada después de confirmación."""
        if not tarea_id:
            messagebox.showwarning(
                "Aviso", "No hay tarea seleccionada para eliminar.", parent=self.root
            )
            return

        tarea_data = self.db_crm.get_tarea_by_id(tarea_id)
        desc_confirm = (
            tarea_data.get("descripcion", f"ID {tarea_id}")[:50]
            if tarea_data
            else f"ID {tarea_id}"
        )

        if messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la tarea:\n'{desc_confirm}'?",
            parent=self.root,
            icon="warning",
        ):

            success = self.db_crm.delete_tarea(tarea_id)
            if success:
                messagebox.showinfo(
                    "Tarea Eliminada",
                    f"Tarea '{desc_confirm}' eliminada correctamente.",
                    parent=self.root,
                )
                if hasattr(self, "tareas_tab_frame"):
                    # Recargar la lista de tareas del caso actual o la vista global
                    if (
                        self.selected_case
                        and self.selected_case["id"] == caso_id_asociado
                    ):
                        self.tareas_tab_frame.load_tareas(
                            caso_id=self.selected_case["id"]
                        )
                    elif caso_id_asociado:
                        self.tareas_tab_frame.load_tareas(caso_id=caso_id_asociado)
                    # else:
                    # self.tareas_tab_frame.load_tareas(mostrar_solo_pendientes_activas=True)
            else:
                messagebox.showerror(
                    "Error",
                    f"No se pudo eliminar la tarea '{desc_confirm}'.",
                    parent=self.root,
                )

    def open_rol_dialog(self, caso_id, rol_id=None):
        """Abre el diálogo para gestionar un rol (crear o editar) con validación."""
        try:
            # Validar parámetros de entrada
            if not caso_id:
                messagebox.showerror(
                    "Error", "No se especificó un caso válido.", parent=self.root
                )
                return

            # Validar que el caso existe
            caso_data = self.db_crm.get_case_by_id(caso_id)
            if not caso_data:
                messagebox.showerror(
                    "Error",
                    f"No se encontró el caso con ID {caso_id}.",
                    parent=self.root,
                )
                return

            # Si es edición, validar que el rol existe
            if rol_id:
                roles = self.db_crm.get_roles_by_caso_id(caso_id)
                if not any(r.get("rol_id") == rol_id for r in roles):
                    messagebox.showerror(
                        "Error",
                        f"No se encontró el rol con ID {rol_id} en este caso.",
                        parent=self.root,
                    )
                    return

            # Crear y mostrar diálogo usando lazy loading
            PartesDialogManager = get_partes_dialog_manager()
            dialog = PartesDialogManager(self.root, self, caso_id, rol_id)
            self.root.wait_window(dialog)

        except Exception as e:
            messagebox.showerror(
                "Error Inesperado",
                f"Error al abrir el diálogo de partes:\n{str(e)}",
                parent=self.root,
            )

    def delete_selected_actividad(self, actividad_id, caso_id):
        """Elimina la actividad seleccionada después de confirmación."""
        if not actividad_id:
            messagebox.showwarning(
                "Advertencia", "No hay actividad seleccionada para eliminar."
            )
            return

        # Obtener datos de la actividad para mostrar en la confirmación
        actividad_data = self.db_crm.get_actividad_by_id(actividad_id)
        if not actividad_data:
            messagebox.showerror(
                "Error", "No se pudo obtener la información de la actividad."
            )
            return

        # Confirmar eliminación
        tipo_actividad = actividad_data.get("tipo_actividad", "Actividad")
        descripcion = (
            actividad_data.get("descripcion", "")[:50] + "..."
            if len(actividad_data.get("descripcion", "")) > 50
            else actividad_data.get("descripcion", "")
        )

        confirm_msg = f"¿Está seguro de que desea eliminar esta actividad?\n\n"
        confirm_msg += f"Tipo: {tipo_actividad}\n"
        confirm_msg += f"Descripción: {descripcion}\n\n"
        confirm_msg += "Esta acción no se puede deshacer."

        if messagebox.askyesno("Confirmar Eliminación", confirm_msg):
            success = self.db_crm.delete_actividad_caso(actividad_id)
            if success:
                messagebox.showinfo(
                    "Éxito", "La actividad ha sido eliminada correctamente."
                )
                # Refrescar la ventana del caso si está abierta
                if caso_id in self.open_case_windows:
                    self.open_case_windows[caso_id].refresh_active_tab()
            else:
                messagebox.showerror("Error", "No se pudo eliminar la actividad.")

    def _save_new_actividad(
        self, caso_id, tipo_actividad, descripcion, referencia_doc=None
    ):
        """Guarda una nueva actividad en el caso."""
        try:
            from datetime import datetime

            fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            actividad_id = self.db_crm.add_actividad_caso(
                caso_id=caso_id,
                fecha_hora=fecha_hora,
                tipo_actividad=tipo_actividad,
                descripcion=descripcion,
                creado_por="Sistema",
                referencia_documento=referencia_doc,
            )

            if actividad_id:
                print(f"Actividad guardada exitosamente con ID: {actividad_id}")
                # Refrescar la ventana del caso si está abierta
                if caso_id in self.open_case_windows:
                    self.open_case_windows[caso_id].refresh_active_tab()
                return actividad_id
            else:
                print("Error al guardar la actividad")
                return None

        except Exception as e:
            print(f"Error en _save_new_actividad: {e}")
            return None

    def open_edit_actividad_dialog(self, actividad_id, caso_id):
        """Abre el diálogo para editar una actividad."""
        # Por ahora, mostrar un mensaje informativo
        # TODO: Implementar diálogo de edición de actividades
        messagebox.showinfo(
            "Información",
            "La funcionalidad de edición de actividades estará disponible próximamente.",
        )

    def delete_selected_rol(self, rol_id, caso_id):
        """Elimina un rol del caso con validación completa."""
        try:
            # Validar parámetros
            if not rol_id or not caso_id:
                messagebox.showerror(
                    "Error", "Parámetros inválidos para eliminar rol.", parent=self.root
                )
                return False

            # Validar que el rol existe
            roles = self.db_crm.get_roles_by_caso_id(caso_id)
            rol_info = next((r for r in roles if r.get("rol_id") == rol_id), None)

            if not rol_info:
                messagebox.showerror(
                    "Error", "El rol seleccionado ya no existe.", parent=self.root
                )
                return False

            # Intentar eliminar
            success = self.db_crm.delete_rol(rol_id)

            if success:
                nombre = rol_info.get("nombre_completo", "la parte")
                messagebox.showinfo(
                    "Éxito",
                    f"El rol de '{nombre}' ha sido eliminado del caso.",
                    parent=self.root,
                )
                self.refresh_current_case_view()
                return True
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo eliminar el rol. Puede que ya haya sido eliminado.",
                    parent=self.root,
                )
                return False

        except Exception as e:
            messagebox.showerror(
                "Error Inesperado",
                f"Error al eliminar el rol:\n{str(e)}",
                parent=self.root,
            )
            return False

    def refresh_case_window(self, case_id):
        """Refresca una ventana de caso específica."""
        self._refresh_open_case_window(case_id)

    # --- MÉTODOS PARA DIÁLOGOS DE MOVIMIENTOS FINANCIEROS ---

    def open_movimiento_ingreso_dialog(self, caso_id):
        """Abre el diálogo para registrar un ingreso."""
        try:
            if not caso_id:
                messagebox.showerror("Error", "No se especificó un caso válido.", parent=self.root)
                return

            # Validar que el caso existe
            caso_data = self.db_crm.get_case_by_id(caso_id)
            if not caso_data:
                messagebox.showerror("Error", f"No se encontró el caso con ID {caso_id}.", parent=self.root)
                return

            # Importar y mostrar diálogo
            from movimiento_dialog import show_add_ingreso_dialog
            result = show_add_ingreso_dialog(self.root, self, caso_id)
            
            if result:
                # Refrescar ventana del caso si está abierta
                self.refresh_case_window(caso_id)
                return True
            return False

        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Error al abrir diálogo de ingreso:\n{str(e)}", parent=self.root)
            return False

    def open_movimiento_gasto_dialog(self, caso_id):
        """Abre el diálogo para registrar un gasto."""
        try:
            if not caso_id:
                messagebox.showerror(
                    "Error", "No se especificó un caso válido.", parent=self.root
                )
                return

            # Validar que el caso existe
            caso_data = self.db_crm.get_case_by_id(caso_id)
            if not caso_data:
                messagebox.showerror(
                    "Error",
                    f"No se encontró el caso con ID {caso_id}.",
                    parent=self.root,
                )
                return

            # Importar y mostrar diálogo
            from movimiento_dialog import show_add_gasto_dialog

            result = show_add_gasto_dialog(self.root, self, caso_id)

            if result:
                # Refrescar ventana del caso si está abierta
                self.refresh_case_window(caso_id)
                return True
            return False

        except Exception as e:
            messagebox.showerror(
                "Error Inesperado",
                f"Error al abrir diálogo de gasto:\n{str(e)}",
                parent=self.root,
            )
            return False

    def open_edit_movimiento_dialog(self, movimiento_id):
        """Abre el diálogo para editar un movimiento financiero."""
        try:
            if not movimiento_id:
                messagebox.showerror(
                    "Error", "No se especificó un movimiento válido.", parent=self.root
                )
                return

            # Obtener datos del movimiento
            movimiento_data = self.db_crm.get_movimiento_by_id(movimiento_id)
            if not movimiento_data:
                messagebox.showerror(
                    "Error",
                    f"No se encontró el movimiento con ID {movimiento_id}.",
                    parent=self.root,
                )
                return

            # Importar y mostrar diálogo
            from movimiento_dialog import show_edit_movimiento_dialog

            result = show_edit_movimiento_dialog(self.root, self, movimiento_data)

            if result:
                # Refrescar ventana del caso si está abierta
                self.refresh_case_window(movimiento_data["caso_id"])
                return True
            return False

        except Exception as e:
            messagebox.showerror(
                "Error Inesperado",
                f"Error al abrir diálogo de edición:\n{str(e)}",
                parent=self.root,
            )
            return False

    def open_actividad_dialog_for_seguimiento_tab(self, caso_id):
        """Abre el diálogo para agregar una nueva actividad desde la pestaña de seguimiento."""
        try:
            if not caso_id:
                messagebox.showerror(
                    "Error", "No se ha especificado un caso.", parent=self.root
                )
                return

            # Importar y mostrar el diálogo de actividad
            from actividad_dialog import ActividadDialog

            dialog = ActividadDialog(self.root, self, caso_id=caso_id)
            self.root.wait_window(dialog)

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir el diálogo de actividad:\n{e}",
                parent=self.root,
            )

    def refresh_current_case_view(self):
        """Refresca la pestaña de partes en la ventana de detalles del caso con manejo de errores."""
        try:
            if not self.selected_case:
                return

            case_id = self.selected_case["id"]

            # Verificar que la ventana del caso esté abierta
            if case_id not in self.open_case_windows:
                return

            case_window = self.open_case_windows[case_id]

            # Verificar que la ventana aún existe
            if not case_window or not case_window.winfo_exists():
                # Limpiar referencia a ventana cerrada
                del self.open_case_windows[case_id]
                return

            # Refrescar la pestaña de partes
            if hasattr(case_window, "partes_tab"):
                case_window.partes_tab.load_partes(case_id)
            
            # Also refresh the active tab to update any changes
            if hasattr(case_window, "refresh_active_tab"):
                case_window.refresh_active_tab()

        except tk.TclError:
            # La ventana fue cerrada, limpiar referencia
            if case_id in self.open_case_windows:
                del self.open_case_windows[case_id]
        except Exception as e:
            print(f"Error refreshing case view: {e}")
        except Exception as e:
            print(f"Error al refrescar vista del caso: {e}")
            # No mostrar messagebox aquí para evitar spam de errores

    # --- Métodos de Lógica para la Agenda Global ---
    def marcar_dias_audiencias_calendario(self):
        """
        Marca los días que tienen audiencias en el calendario.
        Corregido para manejar fechas de PostgreSQL correctamente.
        """
        try:
            # Clear existing markers
            self.agenda_cal.calevent_remove(tag="audiencia_marcador")
            
            # Get dates with audiencias
            fechas = db.get_fechas_con_audiencias()
            
            if not fechas:
                print("[Calendar] No se encontraron fechas con audiencias para marcar")
                return
            
            marked_count = 0
            error_count = 0
            
            for fecha_str in fechas:
                try:
                    # Parse date string (should be in YYYY-MM-DD format from database)
                    fecha_dt = datetime.datetime.strptime(fecha_str, "%Y-%m-%d").date()
                    
                    # Create calendar event marker
                    self.agenda_cal.calevent_create(
                        fecha_dt, "Audiencia", tags="audiencia_marcador"
                    )
                    marked_count += 1
                    
                except ValueError as ve:
                    print(f"[Calendar] [WARN] Formato fecha inválido en BD: {fecha_str} - {ve}")
                    error_count += 1
                except Exception as e:
                    print(f"[Calendar] [ERROR] Error marcando fecha {fecha_str}: {e}")
                    error_count += 1
            
            # Log results
            if marked_count > 0:
                print(f"[Calendar] [OK] Marcados {marked_count} días con audiencias en el calendario")
            if error_count > 0:
                print(f"[Calendar] [WARN] {error_count} errores al marcar fechas")

        except Exception as e:
            print(f"[Calendar] [ERROR] Error general en marcar_dias_audiencias_calendario: {e}")
            import traceback
            traceback.print_exc()

    def actualizar_lista_audiencias(self, event=None):
        """
        Actualiza la lista de audiencias para la fecha seleccionada.
        Muestra fechas en formato argentino y marca audiencias vencidas visualmente.
        """
        if event:
            self.fecha_seleccionada_agenda = self.agenda_cal.get_date()
        
        # Clear existing items
        for i in self.audiencia_tree.get_children():
            self.audiencia_tree.delete(i)
        
        # Get audiencias for selected date
        audiencias = db.get_audiencias_by_fecha(self.fecha_seleccionada_agenda)
        
        if not audiencias:
            print(f"[Audiencias] No hay audiencias para la fecha {self.fecha_seleccionada_agenda}")
        
        expired_count = 0
        valid_count = 0
        
        for aud in audiencias:
            # Check if audiencia is expired
            is_expired = date_utils.DateFormatter.is_date_expired(
                aud.get("fecha"), aud.get("hora")
            )
            
            # Format time
            hora = aud.get("hora", "--:--") or "--:--"
            if is_expired:
                hora = f"[EXPIRED] {hora}"  # Add clock emoji for expired
                expired_count += 1
            else:
                valid_count += 1
            
            # Format description
            desc_full = aud.get("descripcion", "")
            desc_corta = (desc_full.split("\n")[0])[:60] + (
                "..." if len(desc_full) > 60 else ""
            )
            
            # Add visual indicator for expired audiencias
            if is_expired:
                desc_corta = f"[VENCIDA] {desc_corta}"
            
            # Format case info
            caso_full = aud.get("caso_caratula", "Caso Desc.")
            caso_corto = caso_full[:50] + ("..." if len(caso_full) > 50 else "")
            
            # Format link
            link_full = aud.get("link", "") or ""
            link_corto = link_full[:40] + ("..." if len(link_full) > 40 else "")
            
            # Insert item with visual styling
            item_id = self.audiencia_tree.insert(
                "",
                tk.END,
                values=(aud["id"], hora, desc_corta, caso_corto, link_corto),
                iid=str(aud["id"]),
            )
            
            # Apply visual styling for expired audiencias
            if is_expired:
                try:
                    # Set gray color for expired audiencias
                    self.audiencia_tree.set(item_id, "#0", "")  # Clear icon
                    # Note: ttkTreeview styling is limited, but we've added text indicators
                except Exception as e:
                    print(f"[Audiencias] Error aplicando estilo visual: {e}")
        
        # Log results
        total_audiencias = len(audiencias)
        if total_audiencias > 0:
            fecha_display = date_utils.DateFormatter.to_display_format(self.fecha_seleccionada_agenda)
            print(f"[Audiencias] {fecha_display}: {valid_count} válidas, {expired_count} vencidas")
        
        self.deshabilitar_botones_audiencia()
        self.limpiar_detalles_audiencia()

    def cargar_audiencias_fecha_actual(self):
        self.fecha_seleccionada_agenda = datetime.date.today().strftime("%Y-%m-%d")
        self.agenda_cal.selection_set(datetime.date.today())
        self.actualizar_lista_audiencias()

    def on_audiencia_tree_select(self, event=None):
        selected_items = self.audiencia_tree.selection()
        if selected_items:
            try:
                audiencia_id = int(selected_items[0])
                self.audiencia_seleccionada_id = audiencia_id
                self.mostrar_detalles_audiencia(audiencia_id)
                self.habilitar_botones_audiencia()
            except (IndexError, ValueError, TypeError):
                print("Error seleccionando audiencia.")
                self.audiencia_seleccionada_id = None
                self.limpiar_detalles_audiencia()
                self.deshabilitar_botones_audiencia()
        else:
            self.audiencia_seleccionada_id = None
            self.limpiar_detalles_audiencia()
            self.deshabilitar_botones_audiencia()

    def mostrar_detalles_audiencia(self, audiencia_id):
        audiencia = db.get_audiencia_by_id(audiencia_id)
        self.limpiar_detalles_audiencia()
        self.audiencia_details_text.config(state=tk.NORMAL)
        if audiencia:
            fecha_db = audiencia.get("fecha", "N/A")
            if fecha_db != "N/A":
                # Use date utilities for Argentine format (DD/MM/YYYY)
                fecha_display = date_utils.DateFormatter.to_display_format(fecha_db)
                if not fecha_display:
                    fecha_display = str(fecha_db)  # Fallback if conversion fails
            else:
                fecha_display = "N/A"

            hora_db = audiencia.get("hora")
            if hora_db:
                try:
                    # Manejar tanto objetos time como strings
                    if hasattr(hora_db, "strftime"):
                        # Es un objeto time
                        hora = hora_db.strftime("%H:%M")
                    else:
                        # Es un string
                        hora = str(hora_db)
                except (AttributeError, ValueError):
                    hora = str(hora_db)
            else:
                hora = "Sin hora"
            link = audiencia.get("link") or "Sin link"
            rec_activo = "Sí" if audiencia.get("recordatorio_activo") else "No"
            rec_minutos = (
                f" ({audiencia.get('recordatorio_minutos', 15)} min antes)"
                if audiencia.get("recordatorio_activo")
                else ""
            )
            caso_caratula = audiencia.get("caso_caratula", "Caso Desc.")
            cliente_nombre = audiencia.get("cliente_nombre", "Cliente Desc.")
            texto = (
                f"**Audiencia ID:** {audiencia['id']}\n"
                f"**Cliente:** {cliente_nombre}\n"
                f"**Caso:** {caso_caratula} (ID: {audiencia['caso_id']})\n"
                f"------------------------------------\n"
                f"**Fecha:** {fecha_display}\n"
                f"**Hora:** {hora}\n\n"
                f"**Descripción:**\n{audiencia.get('descripcion', 'N/A')}\n\n"
                f"**Link:**\n{link}\n\n"
                f"**Recordatorio:** {rec_activo}{rec_minutos}"
            )
            self.audiencia_details_text.insert("1.0", texto)
        else:
            self.audiencia_details_text.insert("1.0", "Detalles no disponibles.")
        self.audiencia_details_text.config(state=tk.DISABLED)

    def limpiar_detalles_audiencia(self):
        self.audiencia_details_text.config(state=tk.NORMAL)
        self.audiencia_details_text.delete("1.0", tk.END)
        self.audiencia_details_text.config(state=tk.DISABLED)

    def habilitar_botones_audiencia(self):
        state = tk.NORMAL
        self.edit_audiencia_btn.config(state=state)
        self.delete_audiencia_btn.config(state=state)
        self.share_audiencia_btn.config(state=state)
        link_presente = False
        if self.audiencia_seleccionada_id:
            audiencia = db.get_audiencia_by_id(self.audiencia_seleccionada_id)
            if audiencia and audiencia.get("link"):
                link_presente = True
        self.open_link_audiencia_btn.config(
            state=tk.NORMAL if link_presente else tk.DISABLED
        )

    def deshabilitar_botones_audiencia(self):
        state = tk.DISABLED
        self.edit_audiencia_btn.config(state=state)
        self.delete_audiencia_btn.config(state=state)
        self.share_audiencia_btn.config(state=state)
        self.open_link_audiencia_btn.config(state=state)

    def update_add_audiencia_button_state(self):  # Botón global para agregar audiencia
        is_case_selected = self.selected_case is not None
        print(
            f"[DEBUG update_add_audiencia_button_state] self.selected_case is {'SET' if is_case_selected else 'None'}. Button state to: {'NORMAL' if is_case_selected else 'DISABLED'}"
        )
        self.add_audiencia_btn.config(
            state=tk.NORMAL if self.selected_case else tk.DISABLED
        )

    def abrir_link_audiencia_seleccionada(self, event=None):
        if not self.audiencia_seleccionada_id:
            if event:
                return
            else:
                messagebox.showinfo(
                    "Info", "Selecciona una audiencia con link.", parent=self.root
                )
                return
        audiencia = db.get_audiencia_by_id(self.audiencia_seleccionada_id)
        link = audiencia.get("link") if audiencia else None
        if link:
            try:
                if not link.startswith(("http://", "https://")):
                    link = "http://" + link
                webbrowser.open_new_tab(link)
                if audiencia and audiencia.get("caso_id"):
                    self.db_crm.update_last_activity(audiencia["caso_id"])
            except Exception as e:
                messagebox.showerror(
                    "Error", f"No se pudo abrir link:\n{e}", parent=self.root
                )
        elif event is None:
            messagebox.showinfo("Info", "Audiencia sin link.", parent=self.root)

    def _compartir_audiencia_por_email(self):
        if not self.audiencia_seleccionada_id:
            return
        audiencia = self.db_crm.get_audiencia_by_id(self.audiencia_seleccionada_id)
        if not audiencia:
            messagebox.showerror(
                "Error", "No se pudo obtener info de audiencia.", parent=self.root
            )
            return
        desc_corta = (audiencia.get("descripcion", "Evento")).split("\n")[0][:30]
        asunto = f"Audiencia: {audiencia.get('fecha','')} - {desc_corta}"
        cuerpo = self._formatear_texto_audiencia_para_compartir(audiencia)
        asunto_codificado = urllib.parse.quote(asunto)
        cuerpo_codificado = urllib.parse.quote(cuerpo)
        try:
            webbrowser.open(
                f"mailto:?subject={asunto_codificado}&body={cuerpo_codificado}"
            )
            self.db_crm.update_last_activity(audiencia["caso_id"])
        except Exception as e:
            messagebox.showerror(
                "Error", f"No se pudo abrir cliente email:\n{e}", parent=self.root
            )

    def _compartir_audiencia_por_whatsapp(self):
        if not self.audiencia_seleccionada_id:
            return
        try:
            audiencia = self.db_crm.get_audiencia_by_id(
                self.audiencia_seleccionada_id
            )  # Corregido aquí
            if audiencia:
                texto = self._formatear_texto_audiencia_para_compartir(audiencia)
                texto_codificado = urllib.parse.quote(texto, encoding="utf-8")

                whatsapp_url = f"https://wa.me/?text={texto_codificado}"
                webbrowser.open(whatsapp_url)
                # Actualizar actividad del caso
                if audiencia.get("caso_id"):
                    self.db_crm.update_last_activity(audiencia["caso_id"])
        except Exception as e:
            messagebox.showerror("Error", f"Error al compartir por WhatsApp: {e}")

    def _formatear_texto_audiencia_para_compartir(self, audiencia):
        """Crea el texto estandarizado para compartir."""
        caso_info = "Sin caso asociado"
        if audiencia.get("caso_id"):
            caso = self.db_crm.get_case_by_id(audiencia["caso_id"])
            if caso:
                caso_info = caso.get("caratula", "N/A")

        fecha_dt = audiencia.get("fecha")
        # Manejar tanto strings como objetos datetime
        if fecha_dt:
            if isinstance(fecha_dt, str):
                try:
                    # Intentar parsear diferentes formatos de fecha
                    if 'T' in fecha_dt:
                        fecha_obj = datetime.datetime.fromisoformat(fecha_dt.replace('Z', '+00:00'))
                    else:
                        fecha_obj = datetime.datetime.strptime(fecha_dt, "%Y-%m-%d")
                    fecha_display = fecha_obj.strftime("%d-%m-%Y")
                except (ValueError, TypeError):
                    fecha_display = str(fecha_dt)
            else:
                fecha_display = fecha_dt.strftime("%d-%m-%Y")
        else:
            fecha_display = "N/A"

        texto = f"""[RECORDATORIO] RECORDATORIO DE AUDIENCIA\n\n[FECHA] Fecha: {fecha_display}\n[HORA] Hora: {audiencia.get('hora', 'N/A')}\n[CASO] Caso: {caso_info}\n[DESCRIPCION] Descripción: {audiencia.get('descripcion', 'N/A')}"""

        if audiencia.get("link") and audiencia["link"].strip():
            texto += f"\n[LINK] Link: {audiencia['link'].strip()}"

        texto += "\n\n\nPowered by Legal-IT-Ø"
        return texto

    def mostrar_menu_compartir_audiencia(self):
        if not self.audiencia_seleccionada_id:
            messagebox.showwarning(
                "Advertencia", "Selecciona audiencia para compartir.", parent=self.root
            )
            return
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(
            label="Compartir por Email", command=self._compartir_audiencia_por_email
        )
        menu.add_separator()
        menu.add_command(
            label="Compartir por WhatsApp",
            command=self._compartir_audiencia_por_whatsapp,
        )
        try:
            widget = self.share_audiencia_btn
            x = widget.winfo_rootx()
            y = widget.winfo_rooty() + widget.winfo_height()
            menu.tk_popup(x, y)
        except Exception as e:
            print(f"Error mostrando menú compartir: {e}.")
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def abrir_dialogo_audiencia(self, audiencia_id=None):
        is_edit = audiencia_id is not None
        datos_audiencia = {}
        caso_asociado_id = None
        caso_asociado_caratula = "N/A"
        fecha_inicial_dt = (
            datetime.date.today()
        )  # Valor por defecto para una nueva audiencia
        datos_audiencia = {}

        if is_edit:

            # dialog.title("Editar Audiencia")
            datos_audiencia = self.db_crm.get_audiencia_by_id(audiencia_id)
            if not datos_audiencia:
                messagebox.showerror(
                    "Error", "No se cargó info de audiencia."
                )  # , parent=self.root
                dialog.destroy()
                return

            dialog_title = f"Editar Audiencia ID: {audiencia_id}"
            caso_asociado_id = datos_audiencia["caso_id"]
            caso_asociado_caratula = datos_audiencia.get(
                "caso_caratula", f"Caso ID {caso_asociado_id}"
            )

            # Handle date from database - PostgreSQL returns datetime.date objects
            fecha_de_la_bd = datos_audiencia.get("fecha")
            if isinstance(fecha_de_la_bd, datetime.date):
                fecha_inicial_dt = fecha_de_la_bd
            elif isinstance(fecha_de_la_bd, str):
                # If for some reason it's a string, try to convert it
                try:
                    fecha_inicial_dt = datetime.datetime.strptime(
                        fecha_de_la_bd, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    print(
                        f"Advertencia: no se pudo parsear la fecha '{fecha_de_la_bd}' al editar audiencia."
                    )
                    fecha_inicial_dt = datetime.date.today()  # Fallback to today
            else:
                fecha_inicial_dt = datetime.date.today()  # Fallback to today

        else:  # Nueva audiencia
            selected_items = self.case_tree.selection()
            if not selected_items:
                messagebox.showwarning(
                    "Advertencia",
                    "Por favor, seleccione un caso de la lista para agregar una audiencia.",
                    parent=self.root,
                )
                return

            try:
                caso_asociado_id = int(selected_items[0])
                item_values = self.case_tree.item(selected_items[0], "values")
                caso_asociado_caratula = (
                    item_values[2]
                    if len(item_values) > 2
                    else f"Caso ID {caso_asociado_id}"
                )
            except (ValueError, IndexError):
                messagebox.showerror(
                    "Error",
                    "No se pudo identificar el caso seleccionado. Por favor, selecciónelo de nuevo.",
                    parent=self.root,
                )
                return

            dialog_title = f"Agregar Audiencia para: {caso_asociado_caratula[:50]}..."

        dialog = tk.Toplevel(self.root)
        dialog.title(dialog_title)
        dialog.geometry("480x420")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding="15")
        frame.pack(expand=True, fill=tk.BOTH)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(4, weight=1)  # Desc se expande

        ttk.Label(frame, text="Caso:").grid(
            row=0, column=0, sticky=tk.W, pady=3, padx=5
        )
        ttk.Label(frame, text=caso_asociado_caratula, wraplength=300).grid(
            row=0, column=1, sticky=tk.W, pady=3, padx=5
        )

        ttk.Label(frame, text="*Fecha:").grid(
            row=1, column=0, sticky=tk.W, pady=3, padx=5
        )

        # For new audiencias, check if there's a selected date from agenda
        if (
            not is_edit
            and hasattr(self, "fecha_seleccionada_agenda")
            and self.fecha_seleccionada_agenda
        ):
            try:
                fecha_inicial_dt = datetime.datetime.strptime(
                    self.fecha_seleccionada_agenda, "%Y-%m-%d"
                ).date()
            except ValueError:
                print(
                    f"Error parseando fecha de agenda: {self.fecha_seleccionada_agenda}"
                )
                fecha_inicial_dt = datetime.date.today()

        # Create DateEntry with the date object directly
        entry_fecha = DateEntry(
            frame,
            width=12,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy",
            date=fecha_inicial_dt,  # Pass the date object directly
        )
        entry_fecha.grid(row=1, column=1, sticky=tk.W, pady=3, padx=5)

        ttk.Label(frame, text="Hora (HH:MM):").grid(
            row=2, column=0, sticky=tk.W, pady=3, padx=5
        )
        hora_var = tk.StringVar(value=datos_audiencia.get("hora", ""))
        entry_hora = ttk.Entry(frame, textvariable=hora_var, width=7)
        entry_hora.grid(row=2, column=1, sticky=tk.W, pady=3, padx=5)
        ttk.Label(frame, text="Link:").grid(
            row=3, column=0, sticky=tk.W, pady=3, padx=5
        )
        link_var = tk.StringVar(value=datos_audiencia.get("link", ""))
        ttk.Entry(frame, textvariable=link_var).grid(
            row=3, column=1, sticky=tk.EW, pady=3, padx=5
        )

        ttk.Label(frame, text="*Descripción:").grid(
            row=4, column=0, sticky=tk.NW, pady=3, padx=5
        )
        desc_frame = ttk.Frame(frame)
        desc_frame.grid(row=4, column=1, sticky=tk.NSEW, pady=3, padx=5)
        desc_frame.rowconfigure(0, weight=1)
        desc_frame.columnconfigure(0, weight=1)
        desc_text_dialog = tk.Text(desc_frame, height=6, wrap=tk.WORD)
        desc_text_dialog.grid(row=0, column=0, sticky="nsew")
        desc_scroll_dialog = ttk.Scrollbar(
            desc_frame, orient=tk.VERTICAL, command=desc_text_dialog.yview
        )
        desc_scroll_dialog.grid(row=0, column=1, sticky="ns")
        desc_text_dialog["yscrollcommand"] = desc_scroll_dialog.set
        if is_edit:
            desc_text_dialog.insert("1.0", datos_audiencia.get("descripcion", ""))

        rec_frame = ttk.LabelFrame(frame, text="Recordatorio")
        rec_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, pady=10, padx=5)
        rec_act_var = tk.IntVar(value=datos_audiencia.get("recordatorio_activo", 0))
        rec_chk = ttk.Checkbutton(rec_frame, text="Activar", variable=rec_act_var)
        rec_chk.pack(side=tk.LEFT, padx=(5, 10))
        ttk.Label(rec_frame, text="Minutos antes:").pack(side=tk.LEFT)
        rec_min_var = tk.IntVar(value=datos_audiencia.get("recordatorio_minutos", 15))
        vcmd = (frame.register(self.validate_int_positive), "%P")
        rec_spin = ttk.Spinbox(
            rec_frame,
            from_=1,
            to=1440,
            width=5,
            textvariable=rec_min_var,
            validate="key",
            validatecommand=vcmd,
        )
        rec_spin.pack(side=tk.LEFT, padx=5)

        btn_frame_dialog = ttk.Frame(frame)
        btn_frame_dialog.grid(row=6, column=0, columnspan=2, pady=15)
        save_cmd = lambda: self.guardar_audiencia(
            audiencia_id,
            caso_asociado_id,
            entry_fecha.get_date(),
            hora_var.get(),
            link_var.get(),
            desc_text_dialog.get("1.0", tk.END).strip(),
            rec_act_var.get(),
            rec_min_var.get(),
            dialog,
        )
        ttk.Button(btn_frame_dialog, text="Guardar", command=save_cmd).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame_dialog, text="Cancelar", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

        entry_fecha.focus_set()
        self.root.wait_window(dialog)

    def validate_int_positive(self, P):
        return (P.isdigit() and int(P) >= 0) or P == ""

    def parsear_hora(self, hora_str):
        if not hora_str or hora_str.isspace():
            return None
        hora_str = hora_str.strip().replace(".", ":").replace(" ", "")
        match_hm = re.fullmatch(r"(\d{1,2}):(\d{1,2})", hora_str)
        if match_hm:
            h, m = int(match_hm.group(1)), int(match_hm.group(2))
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{h:02d}:{m:02d}"
            else:
                return None
        match_h = re.fullmatch(r"(\d{1,2})", hora_str)
        if match_h:
            h = int(match_h.group(1))
            if 0 <= h <= 23:
                return f"{h:02d}:00"
            else:
                return None
        return None

    def guardar_audiencia(
        self,
        audiencia_id,
        caso_id,
        fecha_dt_obj,
        hora_str,
        link,
        desc,
        r_act,
        r_min,
        dialog,
    ):
        # fecha_dt_obj es ahora un objeto datetime.date de DateEntry
        if not fecha_dt_obj:
            messagebox.showerror(
                "Validación", "La fecha de la audiencia es obligatoria.", parent=dialog
            )
            return
        fecha_db = fecha_dt_obj.strftime(
            "%Y-%m-%d"
        )  # Formatear a YYYY-MM-DD para la BD

        hora_db = self.parsear_hora(hora_str)
        if hora_str and not hora_str.isspace() and hora_db is None:
            messagebox.showerror(
                "Validación", "Formato hora inválido (HH:MM o H).", parent=dialog
            )
            return
        if not desc:
            messagebox.showerror(
                "Validación", "Descripción obligatoria.", parent=dialog
            )
            return
        try:
            minutos_rec = int(r_min)
        except ValueError:
            minutos_rec = 15

        success = False
        msg_op = ""
        if audiencia_id is None:
            new_id = db.add_audiencia(
                caso_id, fecha_db, hora_db, desc, link.strip(), bool(r_act), minutos_rec
            )
            success = new_id is not None
            msg_op = "agregada"
        else:
            success = db.update_audiencia(
                audiencia_id,
                fecha_db,
                hora_db,
                desc,
                link.strip(),
                bool(r_act),
                minutos_rec,
            )
            msg_op = "actualizada"

        if success:
            messagebox.showinfo("Éxito", f"Audiencia {msg_op}.", parent=self.root)
            dialog.destroy()
            self.agenda_cal.selection_set(fecha_dt_obj)
            self.actualizar_lista_audiencias()
            self.marcar_dias_audiencias_calendario()
            # db.update_last_activity(caso_id) # Ya se hace en add/update_audiencia en db
        else:
            messagebox.showerror(
                "Error", f"No se pudo {msg_op} audiencia.", parent=dialog
            )

    def editar_audiencia_seleccionada(self):
        if self.audiencia_seleccionada_id:
            self.abrir_dialogo_audiencia(self.audiencia_seleccionada_id)
        else:
            messagebox.showwarning(
                "Advertencia", "Selecciona audiencia para editar.", parent=self.root
            )

    def eliminar_audiencia_seleccionada(self):
        if not self.audiencia_seleccionada_id:
            messagebox.showwarning(
                "Advertencia", "Selecciona audiencia para eliminar.", parent=self.root
            )
            return
        try:
            desc_corta = self.audiencia_tree.item(str(self.audiencia_seleccionada_id))[
                "values"
            ][2]
        except:
            desc_corta = f"ID {self.audiencia_seleccionada_id}"

        if messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar audiencia:\n'{desc_corta}'?",
            parent=self.root,
            icon="warning",
        ):
            # audiencia_info = db.get_audiencia_by_id(self.audiencia_seleccionada_id) # Para caso_id, ya se maneja en delete_audiencia en db
            if db.delete_audiencia(self.audiencia_seleccionada_id):
                messagebox.showinfo("Éxito", "Audiencia eliminada.", parent=self.root)
                self.actualizar_lista_audiencias()
                self.marcar_dias_audiencias_calendario()
                self.limpiar_detalles_audiencia()
                # if audiencia_info and audiencia_info.get('caso_id'): db.update_last_activity(audiencia_info['caso_id']) # Ya se maneja en db
            else:
                messagebox.showerror(
                    "Error", "No se pudo eliminar audiencia.", parent=self.root
                )

    # --- Funciones de Recordatorios y Bandeja del Sistema ---
    def verificar_recordatorios_periodicamente(self, stop_event):
        print("[Recordatorios] Hilo iniciado.")
        while not stop_event.is_set():
            current_processing_start_time = time.monotonic()
            try:
                ahora = datetime.datetime.now()
                hoy_str = ahora.strftime("%Y-%m-%d")
                if (
                    not hasattr(self, "_dia_verificacion_recordatorios")
                    or self._dia_verificacion_recordatorios != hoy_str
                ):
                    print(
                        f"[Recordatorios] Nuevo día ({hoy_str}), reseteando mostrados."
                    )
                    self.recordatorios_mostrados_hoy = set()  # Para audiencias
                    # Para tareas, la lógica de "ya notificado hoy" está en get_tareas_para_notificacion
                    self._dia_verificacion_recordatorios = hoy_str

                # --- Procesamiento de Recordatorios de Audiencias ---
                # The get_audiencias_con_recordatorio_activo() function already filters expired audiencias
                audiencias_a_revisar = db.get_audiencias_con_recordatorio_activo()
                
                if not audiencias_a_revisar:
                    # No need to log every time, just on first check of the day
                    if not hasattr(self, '_logged_no_audiencias_today'):
                        print(f"[Recordatorios] No hay audiencias con recordatorio activo para procesar")
                        self._logged_no_audiencias_today = True
                else:
                    # Reset the flag if we have audiencias
                    if hasattr(self, '_logged_no_audiencias_today'):
                        delattr(self, '_logged_no_audiencias_today')
                
                processed_count = 0
                skipped_count = 0
                
                for aud in audiencias_a_revisar:
                    if stop_event.is_set():
                        break
                        
                    aud_id = aud["id"]
                    
                    # Skip if already notified today or missing required data
                    if (
                        not aud.get("fecha")
                        or not aud.get("hora")
                        or aud_id in self.recordatorios_mostrados_hoy
                    ):
                        skipped_count += 1
                        continue
                    
                    try:
                        # Double-check that audiencia is not expired (additional safety)
                        if date_utils.DateFormatter.is_date_expired(aud.get("fecha"), aud.get("hora")):
                            print(f"[Recordatorios] [WARN] Audiencia {aud_id} está vencida, saltando")
                            skipped_count += 1
                            continue
                        
                        # Use improved date/time handling
                        fecha_aud = aud["fecha"]
                        hora_aud = aud["hora"]

                        # Convert to database format for consistent parsing
                        fecha_str = date_utils.DateFormatter.to_database_format(fecha_aud)
                        if not fecha_str:
                            print(f"[Recordatorios] [WARN] No se pudo convertir fecha para audiencia {aud_id}")
                            skipped_count += 1
                            continue

                        # Handle time conversion
                        if hasattr(hora_aud, "strftime"):
                            hora_str = hora_aud.strftime("%H:%M")
                        else:
                            hora_str = str(hora_aud)
                            # Remove microseconds if present
                            if ":" in hora_str and len(hora_str.split(":")) > 2:
                                hora_str = ":".join(hora_str.split(":")[:2])

                        # Parse audiencia datetime
                        tiempo_audiencia = datetime.datetime.strptime(
                            f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M"
                        )
                        
                        # Calculate reminder time
                        minutos_antes = aud.get("recordatorio_minutos", 15)
                        tiempo_recordatorio = tiempo_audiencia - datetime.timedelta(
                            minutes=minutos_antes
                        )
                        
                        # Check if it's time to show reminder
                        if tiempo_recordatorio <= ahora < tiempo_audiencia:
                            fecha_display = date_utils.DateFormatter.to_display_format(fecha_aud)
                            print(
                                f"[Recordatorios AUD] ¡Alerta! Audiencia ID: {aud_id} ({hora_str}) el {fecha_display}"
                            )
                            self.root.after(
                                0, self.mostrar_recordatorio_audiencia, aud.copy()
                            )
                            self.recordatorios_mostrados_hoy.add(aud_id)
                            processed_count += 1
                        else:
                            # Not yet time for reminder
                            pass
                            
                    except ValueError as ve:
                        print(
                            f"[Recordatorios AUD] [ERROR] Error parseando fecha/hora ID {aud_id}: {ve}"
                        )
                        skipped_count += 1
                    except Exception as e:
                        print(
                            f"[Recordatorios AUD] [ERROR] Error procesando recordatorio ID {aud_id}: {e}"
                        )
                        skipped_count += 1
                
                # Log processing summary (only if there was activity)
                if processed_count > 0 or skipped_count > 0:
                    total_checked = len(audiencias_a_revisar)
                    print(f"[Recordatorios AUD] Procesadas: {processed_count}, Saltadas: {skipped_count}, Total: {total_checked}")

                # --- Procesamiento de Recordatorios de Tareas ---
                tareas_a_notificar = self.db_crm.get_tareas_para_notificacion()
                for tarea in tareas_a_notificar:
                    if stop_event.is_set():
                        break
                    tarea_id = tarea["id"]
                    print(
                        f"[Recordatorios TAREA] ¡Alerta! Tarea ID: {tarea_id} ('{tarea['descripcion'][:50]}...') vence el {tarea['fecha_vencimiento']}."
                    )
                    self.root.after(0, self.mostrar_recordatorio_tarea, tarea.copy())
                    self.db_crm.update_fecha_ultima_notificacion_tarea(tarea_id)

            except sqlite3.Error as dbe:
                print(f"[Recordatorios] Error BD en hilo: {dbe}")
                stop_event.wait(300)
            except Exception as ex:
                print(
                    f"[Recordatorios] Error inesperado en hilo: {type(ex).__name__}: {ex}"
                )
                import traceback

                traceback.print_exc()
                stop_event.wait(120)

            processing_duration = time.monotonic() - current_processing_start_time
            sleep_interval = max(
                1.0, 60.0 - processing_duration
            )  # Verificar cada minuto
            stop_event.wait(sleep_interval)
        print("[Recordatorios] Hilo detenido.")

    def mostrar_recordatorio_audiencia(self, audiencia):
        if not audiencia:
            return
        print(f"[Notificación AUD] Mostrando para Audiencia ID: {audiencia.get('id')}")
        hora_audiencia = audiencia.get("hora", "N/A")
        desc_full = audiencia.get("descripcion", "")
        desc_alerta = (desc_full.split("\n")[0])[:100] + (
            "..." if len(desc_full) > 100 else ""
        )
        link = audiencia.get("link", "")
        link_corto = (link[:60] + "...") if len(link) > 60 else link
        mensaje = f"Próxima audiencia: {desc_alerta}"
        if link_corto:
            mensaje += f"\nLink: {link_corto}"
        titulo = f"Recordatorio Audiencia: {hora_audiencia}"
        app_nombre = "CRM Legal"
        icon_path_notif = ""
        try:
            icon_path_notif = resource_path("assets/icono.ico")
            if not os.path.exists(icon_path_notif):
                print(f"Advertencia: Icono notif. no encontrado: {icon_path_notif}")
                icon_path_notif = ""
        except Exception as e:
            print(f"Error ruta icono notif.: {e}")
            icon_path_notif = ""

        try:
            print(
                f"[Notificación] Enviando: T='{titulo}', M='{mensaje}', Icono='{icon_path_notif}'"
            )
            plyer_module.notification.notify(
                title=titulo,
                message=mensaje,
                app_name=app_nombre,
                app_icon=icon_path_notif,
                timeout=20,
            )
            print("[Notificación AUD] Plyer notify() llamado.")
        except NotImplementedError:
            print("[Notificación AUD] Plataforma no soportada. Usando fallback.")
            self.root.after(
                0, messagebox.showwarning, titulo, mensaje, {"parent": self.root}
            )
        except Exception as e:
            print(f"[Notificación AUD] Error Plyer: {e}. Usando fallback.")
            self.root.after(
                0, messagebox.showwarning, titulo, mensaje, {"parent": self.root}
            )

    def mostrar_recordatorio_tarea(self, tarea):
        if not tarea:
            return
        print(f"[Notificación TAREA] Mostrando para Tarea ID: {tarea.get('id')}")

        desc_full = tarea.get("descripcion", "Tarea sin descripción")
        desc_alerta = (desc_full.split("\n")[0])[:100] + (
            "..." if len(desc_full) > 100 else ""
        )

        fecha_venc = tarea.get("fecha_vencimiento", "N/A")
        if fecha_venc != "N/A":
            # Use date utilities for Argentine format (DD/MM/YYYY)
            fecha_venc_display = date_utils.DateFormatter.to_display_format(fecha_venc)
            if not fecha_venc_display:
                fecha_venc_display = str(fecha_venc)  # Fallback if conversion fails
        else:
            fecha_venc_display = "N/A"

        caso_info = ""
        if tarea.get("caso_id"):
            caso_caratula = tarea.get("caso_caratula", f"ID {tarea.get('caso_id')}")
            caso_info = f"\nCaso: {caso_caratula[:50]}"
            if len(tarea.get("caso_caratula", "")) > 50:
                caso_info += "..."

        mensaje = (
            f"Tarea Pendiente: {desc_alerta}\nVence: {fecha_venc_display}{caso_info}"
        )
        titulo = f"Recordatorio Tarea CRM: {tarea.get('prioridad', 'Normal')}"
        app_nombre = "CRM Legal"
        icon_path_notif = ""
        try:
            icon_path_notif = resource_path("assets/icono.ico")
            if not os.path.exists(icon_path_notif):
                print(f"Advertencia: Icono notif. no encontrado: {icon_path_notif}")
                icon_path_notif = ""
        except Exception as e:
            print(f"Error ruta icono notif.: {e}")
            icon_path_notif = ""

        try:
            print(f"[Notificación TAREA] Enviando: T='{titulo}', M='{mensaje}'")
            plyer_module.notification.notify(
                title=titulo,
                message=mensaje,
                app_name=app_nombre,
                app_icon=icon_path_notif,
                timeout=20,  # Segundos
            )
            print("[Notificación TAREA] Plyer notify() llamado.")
        except NotImplementedError:
            print(
                "[Notificación TAREA] Plataforma no soportada. Usando fallback messagebox."
            )
            self.root.after(
                0, messagebox.showwarning, titulo, mensaje, {"parent": self.root}
            )
        except Exception as e:
            print(f"[Notificación TAREA] Error Plyer: {e}. Usando fallback messagebox.")
            self.root.after(
                0, messagebox.showwarning, titulo, mensaje, {"parent": self.root}
            )

    def ocultar_a_bandeja(self):
        self.root.withdraw()
        print("[Bandeja] Ventana ocultada.")
        try:
            icon_p = resource_path("assets/icono.ico")
            if os.path.exists(icon_p):
                plyer_module.notification.notify(
                    title="CRM Legal",
                    message="Ejecutándose en segundo plano.",
                    app_name="CRM Legal",
                    app_icon=icon_p,
                    timeout=10,
                )
            else:
                print(f"Advertencia: Icono notif. ocultado no encontrado: {icon_p}")
        except Exception as e:
            print(f"[Bandeja - Notif Ocultado] Error Plyer: {e}")

    def _mostrar_ventana_callback(
        self, icon=None, item=None
    ):  # icon e item son pasados por pystray
        print("[Bandeja] Solicitud para mostrar ventana.")
        self.root.after(0, self.root.deiconify)  # Deiconify en el hilo de Tkinter
        self.root.after(10, self.root.lift)  # Traer al frente
        self.root.after(20, self.root.focus_force)  # Forzar foco

    def _salir_app_callback(
        self, icon=None, item=None
    ):  # icon e item son pasados por pystray
        print("[Bandeja] Solicitud de salida.")
        # No es necesario detener el icono aquí si cerrar_aplicacion lo hace y luego destruye root.
        # Si el icono no se detiene antes de self.root.destroy(), puede dar error.
        self.cerrar_aplicacion_directamente()  # Pedir confirmación y cerrar

    def _load_tray_icon(self):
        """Carga el icono para la bandeja del sistema."""
        try:
            icon_path = resource_path("assets/icono.png")
            if not os.path.exists(icon_path):
                print(f"[Bandeja] Icono no encontrado: {icon_path}")
                return None
            print(f"[Bandeja] Cargando icono desde: {icon_path}")
            return PIL_Image.open(icon_path)
        except Exception as e:
            print(f"[Bandeja] Error cargando icono: {e}")
            return None

    def _create_tray_menu(self):
        """Crea el menú de la bandeja del sistema."""
        return (
            pystray_module.MenuItem("Mostrar CRM Legal", self._mostrar_ventana_callback, default=True),
            pystray_module.MenuItem("Salir", self._salir_app_callback),
        )

    def _setup_system_tray(self):
        """Configura la bandeja del sistema de forma segura."""
        def _create_and_run_tray():
            try:
                print("[Bandeja] Iniciando configuración del icono...")
                
                # Cargar icono
                image = self._load_tray_icon()
                if not image:
                    print("[Bandeja] No se pudo cargar el icono, omitiendo bandeja.")
                    return
                
                # Crear menú
                menu = self._create_tray_menu()
                
                # Crear icono
                self.tray_icon = pystray_module.Icon("CRMLegalAppTray", image, "CRM Legal", menu)
                
                print("[Bandeja] Iniciando icono de bandeja...")
                # run() se ejecuta en su propio hilo daemon
                self.tray_icon.run()
                print("[Bandeja] Icono de bandeja terminado.")
                
            except Exception as e:
                # Handle encoding issues in error message
                error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
                print(f"[Bandeja] Error crítico: {error_msg}")
                self.tray_icon = None
        
        # Crear hilo daemon para pystray
        self.tray_thread = threading.Thread(target=_create_and_run_tray, daemon=True)
        self.tray_thread.start()

    # Mantener compatibilidad con código existente
    def setup_tray_icon(self):
        """Método de compatibilidad - redirige a _setup_system_tray."""
        self._setup_system_tray()


def validate_major_update():
    """Validate that all major update components are working correctly"""
    print("\n" + "="*60)
    print("[VALIDACION] VALIDACION DE ACTUALIZACION MAYOR LPMS LEGAL")
    print("="*60)

    validation_results = []

    # 1. Validar IA Local
    print("[IA] Validando migracion a IA local...")
    try:
        import ia_analyzer
        # Verificar que las importaciones de Ollama estén disponibles
        from langchain_community.llms import Ollama
        validation_results.append("[OK] IA Local: Importaciones correctas")
    except ImportError as e:
        validation_results.append(f"[ERROR] IA Local: Error de importacion - {e}")

    # 2. Validar Fabrica de Documentos
    print("[DOC] Validando fabrica de documentos...")
    try:
        from docxtpl import DocxTemplate
        from num2words import num2words
        # Verificar que la plantilla existe
        template_path = 'plantillas/mediacion/acuerdo_base.docx'
        if os.path.exists(template_path):
            validation_results.append("[OK] Documentos: Plantilla y dependencias disponibles")
        else:
            validation_results.append(f"[WARN] Documentos: Plantilla no encontrada en {template_path}")
    except ImportError as e:
        validation_results.append(f"[ERROR] Documentos: Error de importacion - {e}")

    # 3. Validar Integracion de Herramientas
    print("[TOOLS] Validando integracion de herramientas externas...")
    try:
        # Verificar que subprocess esté disponible
        import subprocess
        import sys
        validation_results.append("[OK] Herramientas: Subprocess disponible para lanzamiento externo")
    except ImportError as e:
        validation_results.append(f"[ERROR] Herramientas: Error de importacion - {e}")

    # Mostrar resultados
    print("\n[RESULTADOS] RESULTADOS DE VALIDACION:")
    for result in validation_results:
        print(f"  {result}")

    success_count = len([r for r in validation_results if r.startswith("[OK]")])
    total_count = len(validation_results)

    if success_count == total_count:
        print(f"\n[SUCCESS] VALIDACION EXITOSA: {success_count}/{total_count} componentes funcionando correctamente")
    else:
        print(f"\n[WARNING] VALIDACION PARCIAL: {success_count}/{total_count} componentes funcionando")

    print("="*60 + "\n")
    return success_count == total_count

# --- Punto de entrada principal ---
if __name__ == "__main__":
    # Ejecutar validación de la actualización mayor
    validate_major_update()
    
    root = tk.Tk()
    style = ttk.Style(root)
    available_themes = style.theme_names()
    print("Temas disponibles:", available_themes)
    desired_themes = ["vista", "xpnative", "winnative", "clam", "alt", "default"]
    theme_applied = False
    for theme in desired_themes:
        if theme in available_themes:
            try:
                style.theme_use(theme)
                print(f"Tema '{theme}' aplicado.")
                theme_applied = True
                break
            except tk.TclError:
                print(f"Advertencia: No se pudo aplicar tema '{theme}'.")
    if not theme_applied:
        print(
            f"Ninguno de los temas preferidos estaba disponible. Usando tema por defecto: {style.theme_use()}"
        )

    app = CRMLegalApp(root)
    root.mainloop()
    print("Aplicación CRM Legal cerrada.")
