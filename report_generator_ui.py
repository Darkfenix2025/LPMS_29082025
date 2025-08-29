"""
Report Generator UI - Vista de Datos Interactiva para Reportes de Casos
Rediseñado según especificaciones: doble panel, vista previa interactiva, ordenamiento
"""

import tkinter as tk
from tkinter import ttk, messagebox
import crm_database as db
from report_manager import ReportManager
import logging
import date_utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('report_generator_ui')

class ReportGeneratorWindow(tk.Toplevel):
    """
    Vista de Datos Interactiva - Módulo de Reportes Rediseñado
    
    Características:
    - Doble panel con PanedWindow
    - Vista previa interactiva con Treeview
    - Ordenamiento por columnas
    - Configuración dinámica de columnas
    - Formato de fechas argentino (dd-mm-yyyy)
    """
    
    def __init__(self, app_controller):
        # Corregir constructor para recibir solo app_controller
        super().__init__(app_controller.root)
        
        self.app_controller = app_controller
        self.report_manager = ReportManager(app_controller)
        
        # Variables de estado
        self.columnas_vars = {}
        self.report_data = []
        self.tree = None
        self.current_sort_column = None
        self.current_sort_reverse = False
        
        # Configuración de ventana
        self.title("🔍 Vista de Datos Interactiva - Análisis de Casos")
        self.geometry("1400x800")
        self.minsize(1200, 600)
        
        # Centrar ventana
        self.transient(app_controller.root)
        self.grab_set()
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        
        # Configurar interfaz
        self._setup_ui()
        self._load_clients()
        
        logger.info("Vista de Datos Interactiva inicializada correctamente")

    def _setup_ui(self):
        """
        Configura la interfaz de usuario con un panel dividido.
        """
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel Izquierdo (Controles)
        left_frame = ttk.Frame(paned_window, width=300)
        paned_window.add(left_frame, weight=1)
        self._setup_left_panel(left_frame)

        # Panel Derecho (Vista Previa)
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=3)
        self._setup_right_panel(right_frame)

    def _setup_left_panel(self, parent_frame):
        """
        Configura el panel izquierdo con filtros y selección de columnas.
        """
        controls_frame = ttk.Frame(parent_frame, padding="10")
        controls_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(controls_frame, text="Configuración del Reporte", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20), anchor="center")

        self._setup_filters_section(controls_frame)
        self._setup_columns_section(controls_frame)
        self._setup_actions_section(controls_frame)

    def _setup_right_panel(self, parent_frame):
        """
        Configura el panel derecho con la vista previa interactiva (Treeview) y controles de exportación.
        """
        # Frame superior con información y estadísticas
        info_frame = ttk.Frame(parent_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.info_label = ttk.Label(info_frame, text="📊 Seleccione filtros y columnas, luego haga clic en 'Actualizar Vista Previa'", 
                                   font=("Arial", 10, "italic"))
        self.info_label.pack(side=tk.LEFT)
        
        self.stats_label = ttk.Label(info_frame, text="", font=("Arial", 10, "bold"))
        self.stats_label.pack(side=tk.RIGHT)
        
        # Frame principal de vista previa
        preview_frame = ttk.LabelFrame(parent_frame, text="🔍 Vista Previa Interactiva", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear Treeview con scrollbars
        tree_frame = ttk.Frame(preview_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_frame, show='headings', selectmode='extended')
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout para mejor control
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Frame de controles de exportación
        export_frame = ttk.Frame(parent_frame)
        export_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Información de ordenamiento
        self.sort_info_label = ttk.Label(export_frame, text="💡 Haga clic en los encabezados para ordenar", 
                                        font=("Arial", 9, "italic"))
        self.sort_info_label.pack(side=tk.LEFT)
        
        # Botones de exportación
        buttons_frame = ttk.Frame(export_frame)
        buttons_frame.pack(side=tk.RIGHT)
        
        ttk.Button(buttons_frame, text="📋 Copiar Datos", 
                  command=self._copiar_datos_clipboard).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(buttons_frame, text="📊 Exportar a Excel", 
                  command=self._exportar_vista_actual, 
                  style="Accent.TButton").pack(side=tk.LEFT)

    def _setup_filters_section(self, parent_frame):
        filters_frame = ttk.LabelFrame(parent_frame, text="Filtros", padding="10")
        filters_frame.pack(fill=tk.X, pady=(0, 15), anchor="n")
        
        client_label = ttk.Label(filters_frame, text="Cliente:")
        client_label.pack(anchor=tk.W)
        
        self.cliente_combo = ttk.Combobox(filters_frame, state="readonly", width=40)
        self.cliente_combo.pack(fill=tk.X, pady=(5, 0))

    def _setup_columns_section(self, parent_frame):
        columns_frame = ttk.LabelFrame(parent_frame, text="Columnas a Incluir", padding="10")
        columns_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        basic_frame = ttk.LabelFrame(columns_frame, text="Datos del Caso", padding="10")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        columnas_basicas = {
            'numero_expediente_anio': 'N° Expediente y Año',
            'caratula': 'Carátula',
            'juzgado': 'Juzgado',
            'etapa_procesal': 'Etapa Procesal'
        }
        
        for key, label in columnas_basicas.items():
            var = tk.BooleanVar(value=True)
            self.columnas_vars[key] = var
            checkbox = ttk.Checkbutton(basic_frame, text=label, variable=var)
            checkbox.pack(anchor=tk.W, pady=2)
        
        enriched_frame = ttk.LabelFrame(columns_frame, text="Datos Enriquecidos", padding="10")
        enriched_frame.pack(fill=tk.X)
        
        columnas_enriquecidas = {
            'partes_intervinientes': 'Partes Intervinientes',
            'ultimo_movimiento': 'Último Movimiento',
            'notas': 'Notas del Caso'
        }
        
        for key, label in columnas_enriquecidas.items():
            var = tk.BooleanVar(value=False)
            self.columnas_vars[key] = var
            checkbox = ttk.Checkbutton(enriched_frame, text=label, variable=var)
            checkbox.pack(anchor=tk.W, pady=2)

    def _setup_actions_section(self, parent_frame):
        actions_frame = ttk.Frame(parent_frame)
        actions_frame.pack(fill=tk.X, pady=(10, 0), side="bottom")
        
        update_button = ttk.Button(actions_frame, text="Actualizar Vista Previa", command=self._actualizar_vista_previa)
        update_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def _load_clients(self):
        try:
            clientes = db.get_clients()
            opciones_clientes = ["Todos los Clientes"]
            self.clientes_dict = {0: None}
            
            for i, cliente in enumerate(clientes, 1):
                nombre_cliente = cliente.get('nombre', 'Sin nombre')
                opciones_clientes.append(nombre_cliente)
                self.clientes_dict[i] = cliente['id']
            
            self.cliente_combo['values'] = opciones_clientes
            self.cliente_combo.current(0)
            logger.info(f"Cargados {len(clientes)} clientes en el filtro")
        except Exception as e:
            logger.error(f"Error al cargar clientes: {e}")
            messagebox.showerror("Error", f"Error al cargar la lista de clientes: {str(e)}", parent=self)

    def _actualizar_vista_previa(self):
        """Actualiza la vista previa con los filtros y columnas seleccionadas"""
        # Mostrar indicador de carga
        self.info_label.config(text="🔄 Cargando datos...")
        self.stats_label.config(text="")
        self.update()
        
        cliente_index = self.cliente_combo.current()
        cliente_id = self.clientes_dict.get(cliente_index)
        
        columnas_seleccionadas = self._get_selected_columns()
        
        if not columnas_seleccionadas:
            messagebox.showwarning("Selección requerida", "Debe seleccionar al menos una columna.", parent=self)
            self.info_label.config(text="⚠️ Seleccione al menos una columna")
            return
        
        try:
            # Obtener datos del ReportManager
            self.report_data = self.report_manager.get_report_data(cliente_id, columnas_seleccionadas)
            self._populate_treeview(columnas_seleccionadas)
            
            # Actualizar información
            cliente_nombre = self.cliente_combo.get()
            if cliente_nombre == "Todos los Clientes":
                self.info_label.config(text=f"📊 Mostrando todos los casos activos")
            else:
                self.info_label.config(text=f"📊 Casos de: {cliente_nombre}")
            
            self.stats_label.config(text=f"📈 {len(self.report_data)} casos encontrados")
            
        except Exception as e:
            logger.error(f"Error al actualizar la vista previa: {e}")
            messagebox.showerror("Error", f"No se pudieron obtener los datos para la vista previa: {e}", parent=self)
            self.info_label.config(text="❌ Error al cargar datos")
    
    def _populate_treeview(self, columnas_seleccionadas):
        """Puebla el Treeview con los datos obtenidos"""
        # Limpiar Treeview
        self.tree.delete(*self.tree.get_children())
        
        # Preparar columnas
        all_columns = {
            **self.report_manager.COLUMNAS_BASICAS, 
            **self.report_manager.COLUMNAS_ENRIQUECIDAS, 
            'nombre_cliente': 'Cliente'
        }
        
        # Siempre incluir cliente al inicio si no está seleccionado
        if 'nombre_cliente' not in columnas_seleccionadas:
            columnas_seleccionadas = ['nombre_cliente'] + columnas_seleccionadas
        
        # Filtrar las columnas a mostrar
        display_columns = {}
        for key in columnas_seleccionadas:
            if key in all_columns:
                display_columns[key] = all_columns[key]
        
        # Configurar columnas del Treeview
        self.tree["columns"] = list(display_columns.keys())
        self.tree["displaycolumns"] = list(display_columns.keys())
        
        # Configurar encabezados con ordenamiento
        for col_key, col_name in display_columns.items():
            self.tree.heading(col_key, text=col_name, 
                            command=lambda c=col_key: self._sort_treeview_column(c, False))
            
            # Ajustar ancho según tipo de columna
            if col_key == 'nombre_cliente':
                width = 200
            elif col_key == 'numero_expediente_anio':
                width = 150
            elif col_key == 'caratula':
                width = 300
            elif col_key in ['partes_intervinientes', 'ultimo_movimiento']:
                width = 250
            else:
                width = 180
                
            self.tree.column(col_key, width=width, anchor='w')
        
        if not self.report_data:
            # Insertar mensaje de "sin datos"
            self.tree.insert("", "end", values=["Sin datos"] + [""] * (len(display_columns) - 1))
            return
        
        # Insertar datos
        for item in self.report_data:
            values = []
            for key in display_columns.keys():
                value = item.get(key, '')
                
                # Formatear fechas al formato argentino si es necesario
                if 'fecha' in key.lower() and value:
                    try:
                        if isinstance(value, str) and len(value) >= 10:
                            # Intentar convertir fecha a formato argentino
                            formatted_date = date_utils.DateFormatter.to_display_format(value)
                            if formatted_date:
                                value = formatted_date
                    except:
                        pass  # Mantener valor original si falla la conversión
                
                values.append(str(value) if value else '')
            
            self.tree.insert("", "end", values=values)
        
        # Actualizar información de ordenamiento
        self.sort_info_label.config(text="💡 Haga clic en los encabezados para ordenar")
    
    def _sort_treeview_column(self, col, reverse):
        """Ordena el Treeview por la columna especificada"""
        try:
            # Obtener datos para ordenar
            data_list = []
            for child in self.tree.get_children():
                value = self.tree.set(child, col)
                data_list.append((value, child))
            
            # Ordenar considerando números y fechas
            def sort_key(item):
                value = item[0]
                # Intentar convertir a número
                try:
                    return float(value.replace(',', '.'))
                except:
                    # Si no es número, ordenar como texto
                    return value.lower()
            
            data_list.sort(key=sort_key, reverse=reverse)
            
            # Reorganizar items en el Treeview
            for index, (val, child) in enumerate(data_list):
                self.tree.move(child, '', index)
            
            # Actualizar comando del encabezado para alternar orden
            all_columns = {
                **self.report_manager.COLUMNAS_BASICAS, 
                **self.report_manager.COLUMNAS_ENRIQUECIDAS, 
                'nombre_cliente': 'Cliente'
            }
            col_name = all_columns.get(col, col)
            
            # Indicador visual de ordenamiento
            sort_indicator = " ↓" if reverse else " ↑"
            self.tree.heading(col, text=col_name + sort_indicator,
                            command=lambda: self._sort_treeview_column(col, not reverse))
            
            # Limpiar indicadores de otras columnas
            for other_col in self.tree["columns"]:
                if other_col != col:
                    other_name = all_columns.get(other_col, other_col)
                    self.tree.heading(other_col, text=other_name,
                                    command=lambda c=other_col: self._sort_treeview_column(c, False))
            
            # Actualizar información
            direction = "descendente" if reverse else "ascendente"
            self.sort_info_label.config(text=f"📊 Ordenado por '{col_name}' ({direction})")
            
            # Guardar estado de ordenamiento
            self.current_sort_column = col
            self.current_sort_reverse = reverse
            
        except Exception as e:
            logger.warning(f"No se pudo ordenar la columna {col}: {e}")
            messagebox.showwarning("Ordenamiento", f"No se pudo ordenar por esta columna: {e}", parent=self)
    
    def _exportar_vista_actual(self):
        """Exporta los datos actualmente visibles en el Treeview a Excel"""
        if not self.report_data:
            messagebox.showwarning("Sin Datos", "No hay datos en la vista previa para exportar.", parent=self)
            return
        
        columnas_visibles = self.tree["columns"]
        
        if not columnas_visibles:
            messagebox.showwarning("Sin Columnas", "No hay columnas visibles para exportar.", parent=self)
            return
        
        try:
            # Obtener datos en el orden actual del Treeview (respetando ordenamiento)
            ordered_data = []
            for child in self.tree.get_children():
                item_data = {}
                for col in columnas_visibles:
                    item_data[col] = self.tree.set(child, col)
                ordered_data.append(item_data)
            
            # Usar el método de exportación del ReportManager con datos ordenados
            success = self.report_manager._export_to_xlsx(ordered_data, columnas_visibles)
            
            if success:
                # Actualizar estadísticas
                self.stats_label.config(text=f"📊 {len(ordered_data)} casos exportados")
            
        except Exception as e:
            logger.error(f"Error al exportar a Excel: {e}")
            messagebox.showerror("Error de Exportación", f"Ocurrió un error al exportar el archivo: {e}", parent=self)
    
    def _get_selected_columns(self):
        """Obtiene las columnas seleccionadas por el usuario"""
        return [key for key, var in self.columnas_vars.items() if var.get()]
    
    def _copiar_datos_clipboard(self):
        """Copia los datos visibles al clipboard"""
        if not self.report_data:
            messagebox.showwarning("Sin Datos", "No hay datos para copiar.", parent=self)
            return
        
        try:
            # Obtener encabezados
            columnas_visibles = self.tree["columns"]
            all_columns = {**self.report_manager.COLUMNAS_BASICAS, **self.report_manager.COLUMNAS_ENRIQUECIDAS, 'nombre_cliente': 'Cliente'}
            headers = [all_columns.get(col, col) for col in columnas_visibles]
            
            # Crear texto para clipboard
            clipboard_text = "\t".join(headers) + "\n"
            
            # Obtener datos en el orden actual del Treeview
            for child in self.tree.get_children():
                values = []
                for col in columnas_visibles:
                    value = self.tree.set(child, col)
                    values.append(str(value))
                clipboard_text += "\t".join(values) + "\n"
            
            # Copiar al clipboard
            self.clipboard_clear()
            self.clipboard_append(clipboard_text)
            
            messagebox.showinfo("Copiado", f"Se copiaron {len(self.tree.get_children())} filas al clipboard.", parent=self)
            
        except Exception as e:
            logger.error(f"Error al copiar datos: {e}")
            messagebox.showerror("Error", f"Error al copiar datos: {e}", parent=self)