import tkinter as tk
from tkinter import ttk

# Importar todos los módulos de las pestañas
from detalles_tab_ui import DetallesTab
from documentos_tab_ui import DocumentosTab
from tareas_ui import TareasTab
from partes_ui import PartesTab
from seguimiento_ui import SeguimientoTab
from cuenta_corriente_ui import CuentaCorrienteTab

class CaseDetailWindow(tk.Toplevel):
    def __init__(self, parent, app_controller, case_id):
        super().__init__(parent)
        self.app_controller = app_controller
        self.case_id = case_id
        
        self.case_data = self.app_controller.db_crm.get_case_by_id(self.case_id)
        if not self.case_data:
            self.destroy()
            return
            
        self.title(f"Detalles del Caso: {self.case_data.get('caratula', 'N/A')}")
        
        # -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
        # 1. TAMAÑO DE LA VENTANA AJUSTADO (MÁS GRANDE)
        self.geometry("850x600") 
        self.minsize(650, 450)
        # -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=10)

        # --- Crear e instanciar cada pestaña ---
        
        # Pestaña 0: Detalles
        # DetallesTab necesita case_data para la carga inicial.
        self.detalles_tab = DetallesTab(self.notebook, self.app_controller, self.case_data) 
        self.notebook.add(self.detalles_tab, text="Detalles del Caso")
        # self.detalles_tab.load_details(self.case_data) # Se llama desde el __init__ de DetallesTab ahora

        # Pestaña 1: Documentación
        # DocumentosTab necesita case_data para la ruta inicial de la carpeta.
        self.documentos_tab = DocumentosTab(self.notebook, self.app_controller, self.case_data)
        self.notebook.add(self.documentos_tab, text="Documentación")
        # La carga inicial de documentos se hace en el __init__ de DocumentosTab

        # Pestaña 2: Tareas/Plazos
        self.tareas_tab = TareasTab(self.notebook, self.app_controller) # app_controller para diálogos
        self.notebook.add(self.tareas_tab, text="Tareas/Plazos")
        #if self.case_id: # Solo cargar si hay case_id (debería haberlo si case_data existe)
         #   self.tareas_tab.load_tareas(self.case_id) 
         #   self.tareas_tab.set_add_button_state()     

        # Pestaña 3: Partes
        self.partes_tab = PartesTab(self.notebook, self.app_controller) # app_controller para diálogos
        self.notebook.add(self.partes_tab, text="Partes")
        #if self.case_id:
        #    self.partes_tab.load_partes(self.case_id)
        #    self.partes_tab.set_add_button_state(None) 

        # Pestaña 4: Seguimiento
        self.seguimiento_tab = SeguimientoTab(self.notebook, self.app_controller) # app_controller para diálogos
        self.notebook.add(self.seguimiento_tab, text="Seguimiento")
        #if self.case_id:
        #    self.seguimiento_tab.load_actividades(self.case_id)
        #    self.seguimiento_tab.set_add_button_state(None)

        # Pestaña 5: Cuenta Corriente
        self.cuenta_corriente_tab = CuentaCorrienteTab(self.notebook, self.app_controller)
        self.notebook.add(self.cuenta_corriente_tab, text="Cuenta Corriente") 
        
        # Seleccionamos la primera pestaña para que el notebook sea visible al abrir
        self.notebook.select(self.detalles_tab)
        
        # Cargar los datos después de un breve retraso para asegurar que la UI esté lista
        self.after(100, self.load_all_tabs_data)

    def load_all_tabs_data(self):
        """Carga o recarga los datos de todas las pestañas."""
        # Primero, refrescamos los datos del caso por si han cambiado
        self.case_data = self.app_controller.db_crm.get_case_by_id(self.case_id)
        if not self.case_data:
            print(f"Error: No se encontraron datos para el caso {self.case_id} al recargar.")
            return

        print(f"Cargando/Recargando datos para todas las pestañas del caso {self.case_id}")
        
        # Load each tab independently to prevent one error from affecting others
        try:
            self.detalles_tab.load_details(self.case_data)
        except Exception as e:
            print(f"Error cargando detalles: {e}")
            
        try:
            self.documentos_tab.load_case_documents(self.case_data.get('ruta_carpeta', ''))
        except Exception as e:
            print(f"Error cargando documentos: {e}")
            
        try:
            self.tareas_tab.load_tareas(self.case_id)
        except Exception as e:
            print(f"Error cargando tareas: {e}")
            
        try:
            self.partes_tab.load_partes(self.case_id)
        except Exception as e:
            print(f"Error cargando partes: {e}")
            
        try:
            self.seguimiento_tab.load_actividades(self.case_id)
        except Exception as e:
            print(f"Error cargando seguimiento: {e}")
            
        # Always try to load the economic module
        try:
            self.cuenta_corriente_tab.load_movimientos(self.case_id)
            print(f"[Cuenta Corriente] Datos cargados exitosamente para caso {self.case_id}")
        except Exception as e:
            print(f"Error cargando cuenta corriente: {e}")

    # -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-
    # 2. NUEVO MÉTODO PARA SELECCIONAR UNA PESTAÑA
    def select_tab(self, tab_index):
        """Selecciona una pestaña del notebook por su índice."""
        try:
            self.notebook.select(tab_index)
        except tk.TclError: # Podría ser si el índice está fuera de rango o el widget no existe
            print(f"Error: No se pudo seleccionar la pestaña con índice {tab_index}")
    # -*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-

# En case_detail_window.py, DENTRO de la clase CaseDetailWindow

    def refresh_active_tab(self):
        """Recarga todas las pestañas para asegurar consistencia de datos."""
        try:
            print(f"[Refresh] Recargando todas las pestañas para caso ID {self.case_id}...")
            # Solución robusta: recargar todas las pestañas en lugar de solo la activa
            self.load_all_tabs_data()
            print(f"[Refresh] Recarga completa finalizada para caso ID {self.case_id}")
        except Exception as e:
            print(f"[Refresh] Error al recargar pestañas: {e}")
        
        # (Añadir aquí otras pestañas si es necesario en el futuro)
        
        except Exception as e:
            print(f"Error al intentar refrescar la pestaña activa: {e}")
        
        print(f"Orden de refresco recibida para la ventana del caso {self.case_id}.")
        # La forma más robusta es simplemente recargar todo.
        # Es rápido y evita problemas de sincronización.
        self.load_all_tabs_data()

    def on_close(self):
        self.app_controller.on_case_window_close(self.case_id) # Notificar al controlador principal
        self.destroy()