# seguimiento_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
import datetime

class SeguimientoTab(ttk.Frame):
    def __init__(self, parent, app_controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app_controller = app_controller
        self.db_crm = self.app_controller.db_crm
        self.selected_actividad_id = None
        
        # --- Variables de la UI ---
        # Variable para guardar el rol seleccionado en los radio buttons
        self.rol_seleccionado_var = tk.StringVar(value="")

        # --- Construir la Interfaz ---
        self._create_widgets()

    # En seguimiento_ui.py, dentro de la clase SeguimientoTab
    def _iniciar_depuracion_ia_wrapper(self):
    # Este método pasa el control al app_controller (main_app) para la depuración
        rol_seleccionado = self.rol_seleccionado_var.get()
        if self.app_controller and rol_seleccionado:
            self.app_controller.iniciar_depuracion_ia(
                status_label_widget=self.ia_status_label,
                result_text_widget=self.ia_result_text,
                button_widget=self.debug_ia_btn,
                rol_usuario=rol_seleccionado # <--- Pasar el rol
            )

    # En seguimiento_ui.py, añade este método a la clase SeguimientoTab

    def _actualizar_estado_botones_ia(self):
        """Habilita o deshabilita los botones de análisis de IA basado en la selección de rol."""
        ruta_asignada = self.movimientos_folder_path_lbl.cget("text")
        carpeta_valida = ruta_asignada and ruta_asignada not in ["...", "Carpeta no asignada"]
        rol_seleccionado = self.rol_seleccionado_var.get()

        if carpeta_valida and rol_seleccionado:
            self.analizar_ia_btn.config(state=tk.NORMAL)
            self.debug_ia_btn.config(state=tk.NORMAL)
            self.ia_status_label.config(text="Estado: Listo para analizar")
        elif not carpeta_valida:
            self.analizar_ia_btn.config(state=tk.DISABLED)
            self.debug_ia_btn.config(state=tk.DISABLED)
            self.ia_status_label.config(text="Estado: Asigne una carpeta de movimientos")
        elif not rol_seleccionado:
            self.analizar_ia_btn.config(state=tk.DISABLED)
            self.debug_ia_btn.config(state=tk.DISABLED)
            self.ia_status_label.config(text="Estado: Seleccione un rol")

    def _iniciar_analisis_ia_wrapper(self):
        # Este método pasa el control al app_controller (main_app)
        # y le pasa los widgets que necesita actualizar.
        rol_seleccionado = self.rol_seleccionado_var.get()
        if self.app_controller and rol_seleccionado:
            self.app_controller.iniciar_analisis_ia(
                status_label_widget=self.ia_status_label,
                result_text_widget=self.ia_result_text,
                button_widget=self.analizar_ia_btn,
                rol_usuario=rol_seleccionado # <--- Pasar el rol
            )

    def _create_widgets(self):
        # Configuración de la grilla principal
        self.columnconfigure(0, weight=1) # Panel izquierdo
        self.columnconfigure(1, weight=2) # Panel derecho
        self.rowconfigure(0, weight=0)    # Fila para la gestión de etapa procesal
        self.rowconfigure(1, weight=1)    # Fila para el historial de actividades
        self.rowconfigure(2, weight=0)    # Fila para el panel de análisis de IA

        # --- Panel de Etapa Procesal (Row 0) ---
        etapa_frame = ttk.Frame(self)
        etapa_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 10), padx=5)
        etapa_frame.columnconfigure(1, weight=1)
        etapa_frame.columnconfigure(2, weight=0)

        ttk.Label(etapa_frame, text="Etapa Procesal Actual:").grid(
            row=0, column=0, sticky=tk.W, pady=3, padx=(0, 5)
        )
        
        self.etapa_combo = ttk.Combobox(etapa_frame, state="readonly")
        self.etapa_combo.grid(row=0, column=1, sticky=tk.EW, pady=3, padx=(0, 10))
        self.etapa_combo.bind("<<ComboboxSelected>>", self._on_etapa_changed)
        
        self.context_buttons_frame = ttk.Frame(etapa_frame)
        self.context_buttons_frame.grid(row=0, column=2, sticky=tk.W, pady=3)

        # --- Panel Izquierdo (Historial de actividades) ---
        left_panel = ttk.Frame(self)
        left_panel.grid(row=1, column=0, sticky='nsew', padx=(0, 5))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)
        left_panel.rowconfigure(1, weight=0)

        # Treeview para el historial
        tree_frame = ttk.Frame(left_panel)
        tree_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 5))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        actividad_cols = ('ID', 'Fecha/Hora', 'Tipo', 'Descripción Resumida')
        self.actividad_tree = ttk.Treeview(tree_frame, columns=actividad_cols, show='headings', selectmode='browse')
        self.actividad_tree.heading('ID', text='ID')
        self.actividad_tree.heading('Fecha/Hora', text='Fecha y Hora')
        self.actividad_tree.heading('Tipo', text='Tipo Actividad')
        self.actividad_tree.heading('Descripción Resumida', text='Descripción')

        self.actividad_tree.column('ID', width=40, stretch=tk.NO, anchor=tk.CENTER)
        self.actividad_tree.column('Fecha/Hora', width=140, stretch=tk.NO)
        self.actividad_tree.column('Tipo', width=120, stretch=tk.NO)
        self.actividad_tree.column('Descripción Resumida', width=300, stretch=True) # Ajustar ancho si es necesario

        actividad_scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.actividad_tree.yview)
        self.actividad_tree.configure(yscrollcommand=actividad_scrollbar_y.set)
        actividad_scrollbar_y.grid(row=0, column=1, sticky='ns')

        actividad_scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.actividad_tree.xview)
        self.actividad_tree.configure(xscrollcommand=actividad_scrollbar_x.set)
        actividad_scrollbar_x.grid(row=1, column=0, sticky='ew')

        self.actividad_tree.grid(row=0, column=0, sticky='nsew')
        self.actividad_tree.bind('<<TreeviewSelect>>', self.on_actividad_select_treeview)
        self.actividad_tree.bind("<Double-1>", self._on_double_click_editar)

        # --- Actions Frame (dentro del panel izquierdo) ---
        actions_frame = ttk.Frame(left_panel) # Cambiado el parent a left_panel
        actions_frame.grid(row=1, column=0, sticky='ew', pady=5)

        self.add_actividad_btn = ttk.Button(actions_frame, text="Agregar Nueva Actividad",
                                            command=self._open_add_actividad_dialog_wrapper, state=tk.DISABLED)
        self.add_actividad_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.edit_actividad_btn = ttk.Button(actions_frame, text="Editar",
                                            command=self._open_edit_actividad_dialog_wrapper, state=tk.DISABLED)
        self.edit_actividad_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.delete_actividad_btn = ttk.Button(actions_frame, text="Eliminar",
                                            command=self._delete_selected_actividad_wrapper, state=tk.DISABLED)
        self.delete_actividad_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.generar_escrito_btn = ttk.Button(actions_frame, text="Generar Escrito Genérico...",
                                            command=self._generar_escrito_generico_wrapper, state=tk.DISABLED)
        self.generar_escrito_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # --- Panel Derecho (Detalles completos de la actividad) ---
        self.details_text_frame = ttk.LabelFrame(self, text="Detalle Completo de Actividad", padding="10")
        # Colocar en la columna 1 de la grilla principal de SeguimientoTab
        self.details_text_frame.grid(row=1, column=1, sticky='nsew', pady=0, padx=(5,0))
        self.details_text_frame.columnconfigure(0, weight=1)
        self.details_text_frame.rowconfigure(0, weight=1)

        try:
            root_bg_color = self.app_controller.root.cget('bg')
        except tk.TclError:
            print("Advertencia: No se pudo obtener el color de fondo del root. Usando color por defecto para Text.")
            root_bg_color = 'SystemButtonFace'

        self.actividad_detail_text = tk.Text(
            self.details_text_frame,
            height=5, # La altura se gestionará por el peso de la fila del frame contenedor
            wrap=tk.WORD,
            state=tk.DISABLED,
            relief=tk.FLAT,
            background=root_bg_color
        )
        self.actividad_detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll = ttk.Scrollbar(self.details_text_frame, orient=tk.VERTICAL, command=self.actividad_detail_text.yview)
        self.actividad_detail_text.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.grid(row=0, column=1, sticky="ns")

        self.details_text_frame.grid_remove() # Ocultar inicialmente

         # -------------------------------------------------------------------
        # --- PANEL DE ANÁLISIS CON IA (RESTAURADO Y CORREGIDO) ---
        # -------------------------------------------------------------------
        self.ia_frame = ttk.LabelFrame(self, text="Análisis con Asistente IA", padding="10")
        self.ia_frame.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=(10, 0))
        self.ia_frame.columnconfigure(0, weight=1)
        self.ia_frame.rowconfigure(2, weight=1) # Fila 2 para el resultado, se expandirá

        # Fila 0: Gestión de la Carpeta
        folder_frame = ttk.Frame(self.ia_frame)
        folder_frame.grid(row=0, column=0, sticky=tk.EW, pady=(0, 10))
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Carpeta de Movimientos:").grid(row=0, column=0, sticky=tk.W)
        self.movimientos_folder_path_lbl = ttk.Label(folder_frame, text="...", relief=tk.SUNKEN, anchor=tk.W)
        self.movimientos_folder_path_lbl.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.select_movimientos_folder_btn = ttk.Button(folder_frame, text="Asignar Carpeta", command=self._select_movimientos_folder_wrapper)
        self.select_movimientos_folder_btn.grid(row=0, column=2, sticky=tk.E)

        # Fila 1: Acciones (Rol y Botones de Análisis)
        ia_actions_frame = ttk.Frame(self.ia_frame)
        ia_actions_frame.grid(row=1, column=0, sticky='ew', pady=(0, 5))
        
        rol_label = ttk.Label(ia_actions_frame, text="Mi Rol:")
        rol_label.pack(side=tk.LEFT, padx=(0, 5))
        
        actora_radio = ttk.Radiobutton(ia_actions_frame, text="Parte Actora", variable=self.rol_seleccionado_var, value="Parte Actora", command=self._actualizar_estado_botones_ia)
        actora_radio.pack(side=tk.LEFT)
        demandada_radio = ttk.Radiobutton(ia_actions_frame, text="Parte Demandada", variable=self.rol_seleccionado_var, value="Parte Demandada", command=self._actualizar_estado_botones_ia)
        demandada_radio.pack(side=tk.LEFT, padx=(5, 15))
        
        self.analizar_ia_btn = ttk.Button(ia_actions_frame, text="Analizar con IA", command=self._iniciar_analisis_ia_wrapper, state=tk.DISABLED)
        self.analizar_ia_btn.pack(side=tk.LEFT, padx=(0, 5))
        self.debug_ia_btn = ttk.Button(ia_actions_frame, text="Depurar (Sin Costo)", command=self._iniciar_depuracion_ia_wrapper, state=tk.DISABLED)
        self.debug_ia_btn.pack(side=tk.LEFT, padx=(0, 10))

        # Botón del Agente IA para generación de acuerdos
        self.agente_ia_btn = ttk.Button(ia_actions_frame, text="🤖 Agente IA - Acuerdos", command=self._abrir_agente_ia_wrapper, state=tk.DISABLED)
        self.agente_ia_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.ia_status_label = ttk.Label(ia_actions_frame, text="Estado: Asigne una carpeta y seleccione un rol")
        self.ia_status_label.pack(side=tk.LEFT)

        # Fila 2: Resultado del Análisis
        ia_result_text_frame = ttk.Frame(self.ia_frame)
        ia_result_text_frame.grid(row=2, column=0, sticky='nsew')
        ia_result_text_frame.columnconfigure(0, weight=1)
        ia_result_text_frame.rowconfigure(0, weight=1)

        self.ia_result_text = tk.Text(ia_result_text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, relief=tk.SUNKEN, borderwidth=1, padx=5, pady=5)
        self.ia_result_text.grid(row=0, column=0, sticky="nsew")
        ia_result_scroll = ttk.Scrollbar(ia_result_text_frame, orient=tk.VERTICAL, command=self.ia_result_text.yview)
        self.ia_result_text.configure(yscrollcommand=ia_result_scroll.set)
        ia_result_scroll.grid(row=0, column=1, sticky="ns")


    # --------------------------------------------------------------------
    # SECCIÓN 3: Métodos "Wrapper" que llaman al Controlador Principal
    # --------------------------------------------------------------------
    def _select_movimientos_folder_wrapper(self):
        if self.app_controller:
            nueva_ruta = self.app_controller.select_and_update_movimientos_folder()
            if nueva_ruta:
                self.movimientos_folder_path_lbl.config(text=nueva_ruta)
                self._actualizar_estado_botones_ia()


    def _open_add_actividad_dialog_wrapper(self):
        if self.app_controller.selected_case:
            self.app_controller.case_manager.open_actividad_dialog(
            self.app_controller.selected_case['id']
            )
        else:
            messagebox.showwarning("Advertencia", "No hay un caso seleccionado para agregar actividad.", parent=self)

    def _open_edit_actividad_dialog_wrapper(self):
        if self.selected_actividad_id and self.app_controller.selected_case:
        # LLAMADA CORRECTA AL MÉTODO DE EDICIÓN
            self.app_controller.case_manager.open_actividad_dialog(
                self.app_controller.selected_case['id'],
                self.selected_actividad_id
            )
        else:
            messagebox.showwarning("Advertencia", "Selecciona una actividad para editar.", parent=self)

    def _delete_selected_actividad_wrapper(self):
        if self.selected_actividad_id and self.app_controller.selected_case:
            self.app_controller.delete_selected_actividad(self.selected_actividad_id, self.app_controller.selected_case['id'])
        else:
            messagebox.showwarning("Advertencia", "Selecciona una actividad para eliminar.", parent=self)

    def _generar_escrito_generico_wrapper(self):
        if self.app_controller.selected_case:
            self.app_controller.case_manager.abrir_dialogo_escrito_generico()
        else:
            messagebox.showwarning("Advertencia", "No hay un caso seleccionado para generar el escrito.", parent=self)

    def _abrir_agente_ia_wrapper(self):
        """Abre la interfaz del agente IA para generación de acuerdos con el caso actual"""
        if not self.app_controller.selected_case:
            messagebox.showwarning("Advertencia", "No hay un caso seleccionado para usar el agente IA.", parent=self)
            return

        try:
            # Importar y abrir la interfaz del agente
            from agent_interface import open_agent_interface
            case_id = self.app_controller.selected_case['id']
            case_caratula = self.app_controller.selected_case.get('caratula', f'ID {case_id}')

            # Abrir interfaz del agente con contexto del caso
            agent_window = open_agent_interface(self.app_controller.root, case_id=case_id, case_caratula=case_caratula)
            if agent_window:
                print(f"[INFO] Interfaz del agente IA abierta para caso {case_id}: {case_caratula}")
        except Exception as e:
            messagebox.showerror(
                "Error",
                f"No se pudo abrir la interfaz del agente IA:\n{str(e)}",
                parent=self
            )
            print(f"[ERROR] Error abriendo interfaz del agente desde seguimiento: {e}")

    def _on_double_click_editar(self, event=None):
        item_id_str = self.actividad_tree.identify_row(event.y)
        if item_id_str:
            if self.selected_actividad_id:
                self._open_edit_actividad_dialog_wrapper()

    # --------------------------------------------------------------------
    # SECCIÓN 2: Métodos de Carga y Actualización de Datos
    # --------------------------------------------------------------------
    def load_actividades(self, caso_id):
        # Limpiar Treeview
        for i in self.actividad_tree.get_children():
            self.actividad_tree.delete(i)
        
        self.selected_actividad_id = None
        self.limpiar_detalle_completo_actividad()

        # Cargar actividades desde la BD
        if caso_id:
            actividades = self.db_crm.get_actividades_by_caso_id(caso_id, order_desc=True)
            for act in actividades:
                try:
                    # Manejar tanto objetos datetime como strings
                    if isinstance(act['fecha_hora'], datetime.datetime):
                        fecha_hora_dt = act['fecha_hora']
                    else:
                        fecha_hora_dt = datetime.datetime.strptime(act['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                    fecha_hora_display = fecha_hora_dt.strftime("%d-%m-%Y %H:%M")
                except (ValueError, TypeError):
                    fecha_hora_display = str(act['fecha_hora'])

                desc_completa = act.get('descripcion', '')
                desc_resumida = (desc_completa[:75] + '...') if len(desc_completa) > 75 else desc_completa
                item_iid = f"act_{act['id']}"
                self.actividad_tree.insert('', tk.END, values=(act['id'], fecha_hora_display, act.get('tipo_actividad', 'N/A'), desc_resumida), iid=item_iid)
        
        # --- CARGAR DATOS DEL CASO Y CONFIGURAR ETAPA PROCESAL ---
        caso_data = self.db_crm.get_case_by_id(caso_id)
        if caso_data:
            # Cargar ruta de carpeta de movimientos
            ruta_guardada = caso_data.get('ruta_carpeta_movimientos', '')
            self.movimientos_folder_path_lbl.config(text=ruta_guardada if ruta_guardada else "Carpeta no asignada")
            
            # Poblar el combobox de etapas procesales
            lista_etapas = self.db_crm.get_todas_las_etapas()
            self.etapa_combo['values'] = lista_etapas
            
            # Establecer el valor actual de la etapa procesal
            etapa_actual = caso_data.get('etapa_procesal', '')
            try:
                if etapa_actual and etapa_actual in lista_etapas:
                    self.etapa_combo.set(etapa_actual)
                elif lista_etapas:
                    self.etapa_combo.set(lista_etapas[0])  # Set to first available option
            except Exception as e:
                print(f"Error setting etapa combo: {e}")
                # Set to empty if there's an error
                if hasattr(self.etapa_combo, 'set'):
                    try:
                        self.etapa_combo.set('')
                    except:
                        pass
            
            # Actualizar botones contextuales basados en la etapa actual
            self._update_contextual_buttons(etapa_actual)
        
        self._update_action_buttons_state()
        self._update_etapa_controls_state()
        self._actualizar_estado_botones_ia()



    def on_actividad_select_treeview(self, event=None):
        selected_items = self.actividad_tree.selection()
        if selected_items:
            item_iid = selected_items[0]
            try:
                if item_iid.startswith("act_"):
                    self.selected_actividad_id = int(item_iid.split('_')[1])
                else:
                    self.selected_actividad_id = int(item_iid) # Fallback por si el iid no tiene prefijo
            except (IndexError, ValueError):
                print(f"Error: No se pudo extraer el ID numérico del iid: {item_iid}")
                self.selected_actividad_id = None

            if self.selected_actividad_id:
                self.mostrar_detalle_completo_actividad(self.selected_actividad_id)
                print(f"Actividad seleccionada en SeguimientoTab: ID {self.selected_actividad_id}")
            else:
                self.limpiar_detalle_completo_actividad()
        else:
            self.selected_actividad_id = None
            self.limpiar_detalle_completo_actividad()

        self._update_action_buttons_state()
        self._update_etapa_controls_state()

    def set_add_button_state(self, state_ignored):
        self._update_action_buttons_state()
        self._update_etapa_controls_state()

    def _update_action_buttons_state(self):
        case_selected = self.app_controller.selected_case is not None
        activity_selected = self.selected_actividad_id is not None

        add_state = tk.NORMAL if case_selected else tk.DISABLED
        edit_delete_state = tk.NORMAL if case_selected and activity_selected else tk.DISABLED

        if hasattr(self, 'add_actividad_btn'):
            self.add_actividad_btn.config(state=add_state)
        if hasattr(self, 'edit_actividad_btn'):
            self.edit_actividad_btn.config(state=edit_delete_state)
        if hasattr(self, 'delete_actividad_btn'):
            self.delete_actividad_btn.config(state=edit_delete_state)
        if hasattr(self, 'generar_escrito_btn'):
            self.generar_escrito_btn.config(state=add_state)
        if hasattr(self, 'agente_ia_btn'):
            self.agente_ia_btn.config(state=add_state)

    def mostrar_detalle_completo_actividad(self, actividad_id):
        if not hasattr(self, 'actividad_detail_text'): return

        if not actividad_id:
            self.limpiar_detalle_completo_actividad()
            return

        self.details_text_frame.grid() # Asegurarse que es visible
        self.actividad_detail_text.config(state=tk.NORMAL)
        self.actividad_detail_text.delete('1.0', tk.END)

        act_details = self.db_crm.get_actividad_by_id(actividad_id)
        if act_details:
            try:
                # Manejar tanto objetos datetime como strings
                if isinstance(act_details['fecha_hora'], datetime.datetime):
                    fecha_hora_dt = act_details['fecha_hora']
                else:
                    fecha_hora_dt = datetime.datetime.strptime(act_details['fecha_hora'], "%Y-%m-%d %H:%M:%S")
                fecha_hora_display = fecha_hora_dt.strftime("%d-%m-%Y %H:%M")
            except (ValueError, TypeError):
                fecha_hora_display = str(act_details['fecha_hora'])

            texto = f"ID de Actividad: {act_details['id']}\n"
            texto += f"Fecha y Hora: {fecha_hora_display}\n"
            texto += f"Tipo de Actividad: {act_details.get('tipo_actividad', 'N/A')}\n"
            if act_details.get('referencia_documento'):
                texto += f"Referencia Documento: {act_details['referencia_documento']}\n"
            texto += f"-------------------------\nDescripción Detallada:\n{act_details.get('descripcion', 'Sin descripción.')}"
            self.actividad_detail_text.insert('1.0', texto)
        else:
            self.actividad_detail_text.insert('1.0', "Detalles de la actividad no encontrados o no disponibles.")

        self.actividad_detail_text.config(state=tk.DISABLED)

    def limpiar_detalle_completo_actividad(self):
        if not hasattr(self, 'actividad_detail_text'): return
        self.actividad_detail_text.config(state=tk.NORMAL)
        self.actividad_detail_text.delete('1.0', tk.END)
        self.actividad_detail_text.config(state=tk.DISABLED)
        if hasattr(self, 'details_text_frame'):
            self.details_text_frame.grid_remove() # Ocultar si no hay nada que mostrar

    def _on_etapa_changed(self, event=None):
        """Handles process stage changes and updates contextual buttons"""
        if not self.app_controller.selected_case:
            return
            
        nueva_etapa = self.etapa_combo.get()
        case_id = self.app_controller.selected_case['id']
        
        # Store previous value for potential reversion
        previous_value = self.app_controller.selected_case.get('etapa_procesal', '')
        
        try:
            # Update database
            success = self.db_crm.update_etapa_procesal(case_id, nueva_etapa)
            
            if success:
                # Update the selected case data
                self.app_controller.selected_case['etapa_procesal'] = nueva_etapa
                # Update contextual buttons
                self._update_contextual_buttons(nueva_etapa)
            else:
                # Revert combobox value on failure
                self.etapa_combo.set(previous_value)
                messagebox.showerror(
                    "Error", 
                    "No se pudo actualizar la etapa procesal. Inténtelo nuevamente.",
                    parent=self
                )
        except Exception as e:
            # Revert combobox value on exception
            self.etapa_combo.set(previous_value)
            messagebox.showerror(
                "Error", 
                f"Error inesperado al actualizar la etapa procesal: {e}",
                parent=self
            )

    def _update_contextual_buttons(self, nueva_etapa):
        """Updates contextual action buttons based on process stage"""
        # Clear existing widgets from context_buttons_frame
        for widget in self.context_buttons_frame.winfo_children():
            widget.destroy()
        
        # Check if stage contains "mediación" and show appropriate button
        if nueva_etapa and "mediación" in nueva_etapa.lower():
            case_id = self.app_controller.selected_case['id']
            btn_generar_acuerdo = ttk.Button(
                self.context_buttons_frame,
                text="Generar Acuerdo...",
                command=lambda: self.app_controller.case_manager.generar_escrito_mediacion(case_id)
            )
            btn_generar_acuerdo.pack(side=tk.LEFT, padx=5)
        
        # Future extensions can be added here with elif statements
        # elif "producción de prueba" in nueva_etapa.lower():
        #     # Show "Generar Oficio..." button
        # elif "alegatos" in nueva_etapa.lower():
        #     # Show "Generar Alegato..." button

    def _update_etapa_controls_state(self):
        """Updates the state of process stage controls based on case selection"""
        case_selected = self.app_controller.selected_case is not None
        
        if case_selected:
            self.etapa_combo.config(state="readonly")
        else:
            self.etapa_combo.config(state="disabled")
            self.etapa_combo.set("")
            # Clear contextual buttons when no case is selected
            for widget in self.context_buttons_frame.winfo_children():
                widget.destroy()