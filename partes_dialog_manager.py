# partes_dialog_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
from multiple_representation_widget import MultipleRepresentationWidget

class PartesDialogManager(tk.Toplevel):
    def __init__(self, parent, app_controller, caso_id, rol_id=None):
        super().__init__(parent)
        self.app_controller = app_controller
        self.db_crm = self.app_controller.db_crm
        self.caso_id = caso_id
        self.rol_id = rol_id
        self.selected_contacto_id = None
        self.existing_roles_en_caso = []

        self.title("Gestionar Parte/Rol en el Caso")
        self.geometry("1600x700")
        self.transient(parent)
        self.grab_set()
        
        # Centrar la ventana
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.winfo_screenheight() // 2) - (700 // 2)
        self.geometry(f"1200x500+{x}+{y}")
        
        # Hacer la ventana redimensionable
        self.resizable(True, True)
        self.minsize(800, 300)

        self._create_widgets()
        self._load_initial_data()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        # Frame principal con scroll
        main_canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Layout principal dividido en dos columnas
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid para layout de dos columnas
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # --- COLUMNA IZQUIERDA: Búsqueda y Contacto ---
        left_column = ttk.Frame(main_frame)
        left_column.grid(row=0, column=0, sticky='nsew', padx=(0, 5))

        # --- Sección de Búsqueda de Contacto (más compacta) ---
        search_frame = ttk.LabelFrame(left_column, text="🔍 Buscar Contacto", padding="8")
        search_frame.pack(fill=tk.X, pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)

        # Fila de búsqueda compacta
        search_row = ttk.Frame(search_frame)
        search_row.pack(fill=tk.X, pady=2)
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_row, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Botones más pequeños
        self.search_btn = ttk.Button(search_row, text="🔍", width=3, command=self._search_contactos)
        self.search_btn.pack(side=tk.LEFT, padx=2)
        
        self.clear_search_btn = ttk.Button(search_row, text="✖", width=3, command=self._clear_search)
        self.clear_search_btn.pack(side=tk.LEFT)
        
        # Configurar búsqueda automática con debounce
        self.search_var.trace('w', self._on_search_change)
        self.search_timer = None
        self.search_entry.bind("<Return>", lambda e: self._search_contactos())

        # TreeView compacto para resultados
        tree_frame = ttk.Frame(search_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.search_results_tree = ttk.Treeview(tree_frame, columns=('Nombre', 'Tipo', 'Doc'), show='headings', height=4)
        self.search_results_tree.heading('Nombre', text='Nombre')
        self.search_results_tree.heading('Tipo', text='Tipo')
        self.search_results_tree.heading('Doc', text='DNI/CUIT')
        
        self.search_results_tree.column('Nombre', width=180)
        self.search_results_tree.column('Tipo', width=60, anchor=tk.CENTER)
        self.search_results_tree.column('Doc', width=100)
        
        self.search_results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar compacto
        search_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.search_results_tree.yview)
        self.search_results_tree.configure(yscrollcommand=search_scrollbar.set)
        search_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Eventos
        self.search_results_tree.bind('<<TreeviewSelect>>', self._on_contacto_select_from_search)
        self.search_results_tree.bind('<Double-1>', self._on_contacto_double_click)
        
        # Label de estado más pequeño
        self.search_status_label = ttk.Label(search_frame, text="Escriba para buscar...", foreground='gray')
        self.search_status_label.pack(pady=2)

        # --- Sección de Datos del Contacto (más compacta) ---
        self.contacto_frame = ttk.LabelFrame(left_column, text="👤 Datos del Contacto", padding="8")
        self.contacto_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.contacto_frame.columnconfigure(1, weight=1)

        self.field_vars = {
            'nombre_completo': tk.StringVar(), 'dni': tk.StringVar(), 'cuit': tk.StringVar(),
            'domicilio_real': tk.StringVar(), 'domicilio_legal': tk.StringVar(),
            'email': tk.StringVar(), 'telefono': tk.StringVar(),
            'es_persona_juridica': tk.BooleanVar(),
            'notas_generales': None
        }

        # Layout más compacto con menos espaciado
        row = 0
        
        # Nombre (campo principal)
        ttk.Label(self.contacto_frame, text="Nombre: *").grid(row=row, column=0, sticky=tk.W, padx=3, pady=1)
        self.nombre_entry = ttk.Entry(self.contacto_frame, textvariable=self.field_vars['nombre_completo'])
        self.nombre_entry.grid(row=row, column=1, sticky=tk.EW, padx=3, pady=1)
        self.field_vars['nombre_completo'].trace('w', self._validate_nombre)
        row += 1
        
        # Tipo de persona
        ttk.Checkbutton(self.contacto_frame, text="Persona Jurídica", variable=self.field_vars['es_persona_juridica']).grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=3, pady=1)
        row += 1
        
        # DNI y CUIT en una fila
        doc_frame = ttk.Frame(self.contacto_frame)
        doc_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=3, pady=1)
        doc_frame.columnconfigure(1, weight=1)
        doc_frame.columnconfigure(3, weight=1)
        
        ttk.Label(doc_frame, text="DNI:").grid(row=0, column=0, sticky=tk.W, padx=(0, 3))
        ttk.Entry(doc_frame, textvariable=self.field_vars['dni'], width=12).grid(row=0, column=1, sticky=tk.EW, padx=(0, 5))
        ttk.Label(doc_frame, text="CUIT:").grid(row=0, column=2, sticky=tk.W, padx=(0, 3))
        ttk.Entry(doc_frame, textvariable=self.field_vars['cuit'], width=15).grid(row=0, column=3, sticky=tk.EW)
        row += 1
        
        # Email y Teléfono
        contact_frame = ttk.Frame(self.contacto_frame)
        contact_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, padx=3, pady=1)
        contact_frame.columnconfigure(1, weight=2)
        contact_frame.columnconfigure(3, weight=1)
        
        ttk.Label(contact_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, padx=(0, 3))
        ttk.Entry(contact_frame, textvariable=self.field_vars['email']).grid(row=0, column=1, sticky=tk.EW, padx=(0, 5))
        ttk.Label(contact_frame, text="Tel:").grid(row=0, column=2, sticky=tk.W, padx=(0, 3))
        ttk.Entry(contact_frame, textvariable=self.field_vars['telefono'], width=12).grid(row=0, column=3, sticky=tk.EW)
        row += 1
        
        # Domicilios (colapsables)
        self.show_addresses = tk.BooleanVar()
        address_toggle = ttk.Checkbutton(self.contacto_frame, text="Mostrar domicilios", variable=self.show_addresses, command=self._toggle_addresses)
        address_toggle.grid(row=row, column=0, columnspan=2, sticky=tk.W, padx=3, pady=1)
        row += 1
        
        # Frame para domicilios (inicialmente oculto)
        self.address_frame = ttk.Frame(self.contacto_frame)
        
        ttk.Label(self.address_frame, text="Dom. Real:").grid(row=0, column=0, sticky=tk.W, padx=3, pady=1)
        ttk.Entry(self.address_frame, textvariable=self.field_vars['domicilio_real']).grid(row=0, column=1, sticky=tk.EW, padx=3, pady=1)
        ttk.Label(self.address_frame, text="Dom. Legal:").grid(row=1, column=0, sticky=tk.W, padx=3, pady=1)
        ttk.Entry(self.address_frame, textvariable=self.field_vars['domicilio_legal']).grid(row=1, column=1, sticky=tk.EW, padx=3, pady=1)
        self.address_frame.columnconfigure(1, weight=1)
        
        # Notas (más pequeñas)
        ttk.Label(self.contacto_frame, text="Notas:").grid(row=row+1, column=0, sticky=tk.NW, padx=3, pady=1)
        self.field_vars['notas_generales'] = tk.Text(self.contacto_frame, height=2, wrap=tk.WORD, font=('TkDefaultFont', 8))
        self.field_vars['notas_generales'].grid(row=row+1, column=1, sticky=tk.EW, padx=3, pady=1)

        # --- COLUMNA DERECHA: Rol y Acciones ---
        right_column = ttk.Frame(main_frame)
        right_column.grid(row=0, column=1, sticky='nsew', padx=(5, 0))

        # --- Sección de Rol en el Caso ---
        rol_frame = ttk.LabelFrame(right_column, text="⚖️ Rol en el Caso", padding="8")
        rol_frame.pack(fill=tk.X, pady=(0, 5))
        rol_frame.columnconfigure(1, weight=1)

        self.rol_vars = {
            'rol_principal': tk.StringVar(), 'rol_secundario': tk.StringVar(),
            'representa_a_id': tk.StringVar(), 'datos_bancarios': tk.StringVar(),
            'notas_del_rol': None
        }

        # Rol principal
        ttk.Label(rol_frame, text="Rol Principal: *").grid(row=0, column=0, sticky=tk.W, padx=3, pady=2)
        self.rol_principal_combo = ttk.Combobox(rol_frame, textvariable=self.rol_vars['rol_principal'], 
                                              values=['Actor', 'Demandado', 'Abogado', 'Apoderado', 'Perito', 'Tercero', 'Testigo'],
                                              state='readonly')
        self.rol_principal_combo.grid(row=0, column=1, sticky=tk.EW, padx=3, pady=2)
        self.rol_principal_combo.bind('<<ComboboxSelected>>', self._on_rol_principal_change)

        # Rol secundario
        ttk.Label(rol_frame, text="Rol Secundario:").grid(row=1, column=0, sticky=tk.W, padx=3, pady=1)
        ttk.Entry(rol_frame, textvariable=self.rol_vars['rol_secundario']).grid(row=1, column=1, sticky=tk.EW, padx=3, pady=1)

        # Representa a (dinámico)
        self.representa_label = ttk.Label(rol_frame, text="Representa a:")
        self.representa_combo = ttk.Combobox(rol_frame, textvariable=self.rol_vars['representa_a_id'], state=tk.DISABLED)
        
        # Opciones de representación múltiple
        self.multiple_rep_frame = ttk.Frame(rol_frame)
        
        # Radio buttons para elegir tipo de representación
        self.representation_type = tk.StringVar(value="simple")
        self.simple_rep_radio = ttk.Radiobutton(self.multiple_rep_frame, text="Representación Simple", 
                                              variable=self.representation_type, value="simple",
                                              command=self._on_representation_type_change)
        self.multiple_rep_radio = ttk.Radiobutton(self.multiple_rep_frame, text="Representación Múltiple", 
                                                variable=self.representation_type, value="multiple",
                                                command=self._on_representation_type_change)
        
        # Botón para abrir selector de representación múltiple
        self.multiple_rep_button = ttk.Button(self.multiple_rep_frame, text="Seleccionar Partes...", 
                                            command=self._open_multiple_representation_dialog,
                                            state=tk.DISABLED)
        
        # Label para mostrar resumen de selección múltiple
        self.multiple_rep_summary = ttk.Label(self.multiple_rep_frame, text="", foreground='blue')
        
        # Variables para representación múltiple
        self.selected_multiple_parties = []
        self.multiple_rep_widget = None
        
        # Datos bancarios
        ttk.Label(rol_frame, text="Datos Bancarios:").grid(row=3, column=0, sticky=tk.W, padx=3, pady=1)
        ttk.Entry(rol_frame, textvariable=self.rol_vars['datos_bancarios']).grid(row=3, column=1, sticky=tk.EW, padx=3, pady=1)

        # Notas del rol (más pequeñas)
        ttk.Label(rol_frame, text="Notas del Rol:").grid(row=4, column=0, sticky=tk.NW, padx=3, pady=1)
        self.rol_vars['notas_del_rol'] = tk.Text(rol_frame, height=2, wrap=tk.WORD, font=('TkDefaultFont', 8))
        self.rol_vars['notas_del_rol'].grid(row=4, column=1, sticky=tk.EW, padx=3, pady=1)

        # --- Frame de información adicional ---
        info_frame = ttk.LabelFrame(right_column, text="ℹ️ Información", padding="8")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.info_text = tk.Text(info_frame, height=4, wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, bg='#f0f0f0', font=('TkDefaultFont', 8))
        self.info_text.pack(fill=tk.BOTH, expand=True)
        
        # Configurar scroll para el canvas principal
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Botones de Acción ---
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=1, sticky='e', pady=(10, 0))
        
        self.save_button = ttk.Button(button_frame, text="Guardar", command=self._save)
        self.save_button.pack(side=tk.RIGHT, padx=5)
        
        self.cancel_button = ttk.Button(button_frame, text="Cancelar", command=self._on_close)
        self.cancel_button.pack(side=tk.RIGHT)

    def _load_initial_data(self):
        # Cargar roles existentes en el caso para el combobox de "Representa a"
        self.existing_roles_en_caso = self.db_crm.get_roles_by_caso_id(self.caso_id)
        self._update_representa_combo()

        if self.rol_id:
            # Modo edición: cargar datos del rol y contacto
            rol_data = next((rol for rol in self.existing_roles_en_caso if rol['rol_id'] == self.rol_id), None)
            if rol_data:
                self.selected_contacto_id = rol_data['contacto_id']
                self._fill_contacto_fields(rol_data)
                self._fill_rol_fields(rol_data)
                self.contacto_frame.config(text=f"2. Datos del Contacto (ID: {self.selected_contacto_id})")
        else:
            # Modo creación
            self.title("Agregar Nueva Parte/Rol al Caso")
        
        # Inicializar panel de información
        self._update_info_panel()

    def _on_search_change(self, *args):
        """Maneja cambios en el campo de búsqueda con debounce."""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        
        # Debounce de 500ms
        self.search_timer = self.after(500, self._search_contactos_auto)

    def _search_contactos_auto(self):
        """Búsqueda automática con debounce."""
        termino = self.search_var.get().strip()
        if len(termino) >= 2:  # Buscar solo si hay al menos 2 caracteres
            self._perform_search(termino)
        elif len(termino) == 0:
            self._clear_search_results()

    def _search_contactos(self):
        """Búsqueda manual activada por botón o Enter."""
        termino = self.search_var.get().strip()
        if not termino:
            messagebox.showinfo("Información", "Ingrese un término de búsqueda (nombre, DNI o CUIT).", parent=self)
            return
        
        self._perform_search(termino)

    def _perform_search(self, termino):
        """Ejecuta la búsqueda y actualiza la interfaz."""
        # Limpiar resultados anteriores
        for i in self.search_results_tree.get_children():
            self.search_results_tree.delete(i)

        # Actualizar estado
        self.search_status_label.config(text="Buscando...", foreground='blue')
        self.update()

        try:
            contactos = self.db_crm.search_contactos(termino)
            
            if contactos:
                for c in contactos:
                    tipo_persona = "Jurídica" if c.get('es_persona_juridica') else "Física"
                    dni_cuit = f"{c.get('dni', '') or ''}/{c.get('cuit', '') or ''}".strip('/')
                    
                    self.search_results_tree.insert('', tk.END, 
                                                  values=(c['nombre_completo'], tipo_persona, dni_cuit), 
                                                  iid=f"contact_{c['id']}")
                
                self.search_status_label.config(text=f"✓ {len(contactos)} contacto(s)", foreground='green')
            else:
                self.search_status_label.config(text="No se encontraron contactos", foreground='orange')
                
        except Exception as e:
            self.search_status_label.config(text=f"Error en búsqueda: {str(e)}", foreground='red')

    def _clear_search(self):
        """Limpia la búsqueda y resultados."""
        self.search_var.set('')
        self._clear_search_results()

    def _clear_search_results(self):
        """Limpia solo los resultados de búsqueda."""
        for i in self.search_results_tree.get_children():
            self.search_results_tree.delete(i)
        self.search_status_label.config(text="Ingrese un término de búsqueda", foreground='gray')

    def _on_contacto_select_from_search(self, event=None):
        """Maneja la selección de un contacto desde los resultados de búsqueda."""
        selected_items = self.search_results_tree.selection()
        if selected_items:
            item_iid = selected_items[0]
            try:
                self.selected_contacto_id = int(item_iid.split('_')[1])
                contacto_data = self.db_crm.get_contacto_by_id(self.selected_contacto_id)
                
                if contacto_data:
                    self._fill_contacto_fields(contacto_data)
                    self.contacto_frame.config(text=f"2. Datos del Contacto (ID: {self.selected_contacto_id}) - EXISTENTE")
                    self._highlight_selected_contact()
                else:
                    messagebox.showerror("Error", "No se pudo cargar la información del contacto.", parent=self)
            except (ValueError, IndexError) as e:
                messagebox.showerror("Error", f"Error al seleccionar contacto: {str(e)}", parent=self)

    def _on_contacto_double_click(self, event=None):
        """Maneja doble clic en un contacto para seleccionarlo automáticamente."""
        self._on_contacto_select_from_search(event)
        # Enfocar el primer campo del rol
        self.rol_principal_combo.focus()

    def _highlight_selected_contact(self):
        """Resalta visualmente el contacto seleccionado."""
        # Cambiar color de fondo del frame de contacto para indicar que es existente
        self.contacto_frame.configure(style='Selected.TLabelframe')
        
        # Opcional: deshabilitar algunos campos para contactos existentes
        # (se pueden habilitar si el usuario quiere editarlos)
        pass

    def _fill_contacto_fields(self, data):
        for key, var in self.field_vars.items():
            if key == 'notas_generales':
                # Check if it's a Text widget
                if hasattr(var, 'delete') and hasattr(var, 'insert'):
                    var.delete('1.0', tk.END)
                    # Asegurar que el valor no sea None
                    value = data.get(key, '') or ''
                    var.insert('1.0', str(value))
                else:
                    # It's a StringVar or similar
                    value = data.get(key, '') or ''
                    var.set(str(value))
            elif key == 'es_persona_juridica':
                # Manejar campo booleano específicamente
                value = data.get(key, False)
                # Convertir a booleano si es necesario
                if isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif value is None:
                    value = False
                var.set(bool(value))
            else:
                value = data.get(key, '') or ''
                var.set(str(value))

    def _fill_rol_fields(self, data):
        for key, var in self.rol_vars.items():
            if key == 'notas_del_rol':
                var.delete('1.0', tk.END)
                # Asegurar que el valor no sea None
                value = data.get(key, '') or ''
                var.insert('1.0', str(value))
            elif key == 'representa_a_id':
                # Manejar la representación de forma especial
                representa_id = data.get(key)
                if representa_id:
                    # Buscar el nombre de la parte representada
                    representado = next((r for r in self.existing_roles_en_caso if r['rol_id'] == representa_id), None)
                    if representado:
                        descripcion = f"{representado['nombre_completo']} ({representado['rol_principal']})"
                        var.set(descripcion)

                    else:
                        var.set('')
                        print(f"[DEBUG] No se encontró la parte representada con ID {representa_id}")
                else:
                    var.set('')
            else:
                value = data.get(key, '') or ''
                var.set(str(value))
        
        # Detectar si es representación múltiple existente
        self._detect_and_load_multiple_representation(data)
        
        # Actualizar el combo después de cargar los datos
        self._on_rol_principal_change()

    def _detect_and_load_multiple_representation(self, data):
        """Detecta y carga representaciones múltiples existentes para edición."""
        try:
            # Verificar si es un rol de abogado o apoderado
            rol_principal = data.get('rol_principal', '')
            if rol_principal not in ['Abogado', 'Apoderado']:
                return
            
            # Verificar si las notas contienen marcador de representación múltiple
            notas = data.get('notas_del_rol', '') or ''
            if 'REPRESENTACION_MULTIPLE' in notas:
                # Es representación múltiple - obtener todas las representaciones del grupo
                multiple_reps = self.db_crm.get_multiple_representations(self.rol_id)
                if multiple_reps and multiple_reps.get('is_multiple'):
                    # Configurar para representación múltiple
                    self.representation_type.set("multiple")
                    
                    # Cargar las partes representadas
                    self.selected_multiple_parties = []
                    for party in multiple_reps.get('represented_parties', []):
                        # Buscar la información completa de la parte en existing_roles_en_caso
                        party_info = next((r for r in self.existing_roles_en_caso if r['rol_id'] == party['party_id']), None)
                        if party_info:
                            self.selected_multiple_parties.append({
                                'id': party['party_id'],
                                'rol_id': party['party_id'],
                                'nombre_completo': party['party_name'],
                                'rol_principal': party['party_role']
                            })
                    

                else:
                    # Fallback a representación simple
                    self.representation_type.set("simple")
            else:
                # Es representación simple
                self.representation_type.set("simple")
                
        except Exception as e:

            # En caso de error, usar representación simple
            self.representation_type.set("simple")

    def _toggle_addresses(self):
        """Muestra/oculta los campos de domicilio."""
        if self.show_addresses.get():
            self.address_frame.grid(row=5, column=0, columnspan=2, sticky=tk.EW, padx=3, pady=1)
        else:
            self.address_frame.grid_remove()

    def _update_info_panel(self, message=""):
        """Actualiza el panel de información."""
        if hasattr(self, 'info_text'):
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete('1.0', tk.END)
            if message:
                self.info_text.insert('1.0', message)
            else:
                default_info = "💡 Consejos:\n\n"
                default_info += "• Use la búsqueda para reutilizar contactos existentes\n"
                default_info += "• Los campos marcados con * son obligatorios\n"
                default_info += "• Abogados y Apoderados pueden representar a Actores, Demandados o Terceros\n"
                default_info += "• Cada parte principal puede tener su propio abogado\n"
                default_info += "• Primero agregue las partes principales, luego sus abogados"
                self.info_text.insert('1.0', default_info)
            self.info_text.config(state=tk.DISABLED)

    def _validate_nombre(self, *args):
        """Valida el campo nombre en tiempo real."""
        nombre = self.field_vars['nombre_completo'].get().strip()
        if len(nombre) < 2:
            self.nombre_entry.configure(style='Invalid.TEntry')
        else:
            self.nombre_entry.configure(style='TEntry')

    def _validate_email(self, *args):
        """Valida el formato del email."""
        email = self.field_vars['email'].get().strip()
        if email and '@' not in email:
            # Aquí podrías agregar validación más robusta
            pass

    def _validate_form(self):
        """Valida todo el formulario antes de guardar."""
        errors = []
        
        # Validar nombre obligatorio
        if not self.field_vars['nombre_completo'].get().strip():
            errors.append("El nombre completo es obligatorio")
        
        # Validar rol principal obligatorio
        if not self.rol_vars['rol_principal'].get().strip():
            errors.append("El rol principal es obligatorio")
        
        # Validar que no se duplique el mismo rol para el mismo contacto
        # EXCEPCIÓN: Permitir múltiples roles para Abogados y Apoderados (representación múltiple)
        if self.selected_contacto_id:
            rol_principal = self.rol_vars['rol_principal'].get()
            
            if rol_principal not in ['Abogado', 'Apoderado']:
                # Para otros roles, mantener la validación original
                existing_roles = [r for r in self.existing_roles_en_caso 
                                if r['contacto_id'] == self.selected_contacto_id 
                                and r['rol_principal'] == rol_principal
                                and r['rol_id'] != self.rol_id]  # Excluir el rol actual en edición
                
                if existing_roles:
                    errors.append(f"Este contacto ya tiene el rol '{rol_principal}' en este caso")
            else:
                # Para Abogados y Apoderados, validar solo si no es representación múltiple
                rep_type = getattr(self, 'representation_type', None)
                if rep_type and rep_type.get() == "simple":
                    # En representación simple, verificar duplicados solo si no representa a nadie
                    representa_a = self.rol_vars['representa_a_id'].get()
                    if not representa_a:
                        existing_roles = [r for r in self.existing_roles_en_caso 
                                        if r['contacto_id'] == self.selected_contacto_id 
                                        and r['rol_principal'] == rol_principal
                                        and r['rol_id'] != self.rol_id
                                        and not r.get('representa_a_id')]  # Solo roles sin representación
                        
                        if existing_roles:
                            errors.append(f"Este contacto ya tiene el rol '{rol_principal}' sin representación en este caso")
        
        return errors

    def _on_rol_principal_change(self, event=None):
        """Maneja cambios en el rol principal con lógica dinámica mejorada."""
        rol = self.rol_principal_combo.get()
        
        # Mostrar/ocultar campo de representación según el rol
        if rol in ['Abogado', 'Apoderado']:
            self._show_representation_options()
            
            # Actualizar información contextual
            info_msg = f"ℹ️ Opciones de representación para {rol.lower()}:\n\n"
            info_msg += "• Representación Simple: Seleccione una parte del combo\n"
            info_msg += "• Representación Múltiple: Use el botón para seleccionar varias partes\n"
            info_msg += "• Solo se pueden representar Actores, Demandados y Terceros\n"
            info_msg += "• Si no ve la parte deseada, agréguela primero"
            self._update_info_panel(info_msg)
        else:
            self._hide_representation_options()
            
            # Restaurar información por defecto
            self._update_info_panel()
        
        # Actualizar sugerencias de rol secundario según el rol principal
        self._update_rol_secundario_suggestions(rol)

    def _update_rol_secundario_suggestions(self, rol_principal):
        """Actualiza las sugerencias de rol secundario según el rol principal."""
        suggestions = {
            'Abogado': ['Patrocinante', 'Apoderado', 'Defensor'],
            'Apoderado': ['General', 'Especial', 'Para pleitos'],
            'Actor': ['Principal', 'Coadyuvante'],
            'Demandado': ['Principal', 'Citado en garantía'],
            'Perito': ['Oficial', 'De parte', 'Consultor técnico'],
            'Testigo': ['Presencial', 'De referencia']
        }
        
        # Aquí podrías implementar un combobox con sugerencias para rol_secundario
        # Por ahora solo guardamos las sugerencias para uso futuro
        self.rol_secundario_suggestions = suggestions.get(rol_principal, [])

    def _show_representation_options(self):
        """Muestra las opciones de representación para abogados y apoderados."""
        # Mostrar frame de opciones de representación múltiple
        self.multiple_rep_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, padx=3, pady=5)
        
        # Layout interno del frame
        self.simple_rep_radio.grid(row=0, column=0, sticky=tk.W, padx=5)
        self.multiple_rep_radio.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Mostrar combo para representación simple (inicialmente)
        self.representa_label.grid(row=3, column=0, sticky=tk.W, padx=3, pady=2)
        self.representa_combo.grid(row=3, column=1, sticky=tk.EW, padx=3, pady=2)
        self.representa_combo.config(state='readonly')
        self._update_representa_combo()
        
        # Configurar estado inicial
        self._on_representation_type_change()

    def _hide_representation_options(self):
        """Oculta las opciones de representación."""
        if hasattr(self, 'multiple_rep_frame'):
            self.multiple_rep_frame.grid_remove()
        if hasattr(self, 'representa_label'):
            self.representa_label.grid_remove()
        if hasattr(self, 'representa_combo'):
            self.representa_combo.grid_remove()
            self.representa_combo.set('')
        
        # Limpiar variables
        self.rol_vars['representa_a_id'].set('')
        self.selected_multiple_parties = []
        if hasattr(self, 'multiple_rep_summary'):
            self.multiple_rep_summary.config(text="")

    def _on_representation_type_change(self):
        """Maneja cambios en el tipo de representación (simple vs múltiple)."""
        rep_type = self.representation_type.get()

        if rep_type == "simple":
            # Mostrar combo, ocultar botón múltiple
            self.representa_label.grid(row=3, column=0, sticky=tk.W, padx=3, pady=2)
            self.representa_combo.grid(row=3, column=1, sticky=tk.EW, padx=3, pady=2)
            self.representa_combo.config(state='readonly')

            # Ocultar widgets de representación múltiple
            self.multiple_rep_button.grid_remove()
            self.multiple_rep_summary.grid_remove()

            # Limpiar selección múltiple y convertir a simple si es posible
            if self.selected_multiple_parties:
                # Si hay una sola parte en la selección múltiple, convertirla a simple
                if len(self.selected_multiple_parties) == 1:
                    party = self.selected_multiple_parties[0]
                    party_id = party.get('rol_id') or party.get('id')
                    # Buscar la descripción correspondiente en el mapa
                    for descripcion, rol_id in self.representa_map.items():
                        if rol_id == party_id:
                            self.representa_combo.set(descripcion)
                            break
                # Limpiar la selección múltiple
                self.selected_multiple_parties = []
            elif not self.rol_id:
                # Solo limpiar en modo creación si no hay selección múltiple
                self.selected_multiple_parties = []

        else:  # multiple
            # Ocultar combo, mostrar botón múltiple
            self.representa_label.grid_remove()
            self.representa_combo.grid_remove()

            # Convertir representación simple a múltiple si hay selección
            current_selection = self.representa_combo.get()
            if current_selection and current_selection in self.representa_map and not self.selected_multiple_parties:
                representa_id = self.representa_map[current_selection]
                # Buscar la información de la parte representada
                representado = next((r for r in self.existing_roles_en_caso if r['rol_id'] == representa_id), None)
                if representado:
                    self.selected_multiple_parties = [{
                        'id': representa_id,
                        'rol_id': representa_id,
                        'nombre_completo': representado['nombre_completo'],
                        'rol_principal': representado['rol_principal']
                    }]

            self.representa_combo.set('')

            # Mostrar widgets de representación múltiple
            self.multiple_rep_button.grid(row=3, column=0, columnspan=2, sticky=tk.EW, padx=3, pady=2)
            self.multiple_rep_button.config(state=tk.NORMAL)
            self.multiple_rep_summary.grid(row=4, column=0, columnspan=2, sticky=tk.EW, padx=3, pady=2)

            # Actualizar resumen
            self._update_multiple_rep_summary()

    def _open_multiple_representation_dialog(self):
        """Abre el diálogo para seleccionar múltiples partes a representar."""
        # Obtener partes disponibles para representar
        available_parties = self._get_representable_parties()
        
        if not available_parties:
            messagebox.showinfo("Información", 
                              "No hay partes disponibles para representar.\n"
                              "Agregue primero Actores, Demandados o Terceros al caso.", 
                              parent=self)
            return
        
        # Crear diálogo modal
        dialog = tk.Toplevel(self)
        dialog.title("Seleccionar Partes a Representar")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Centrar diálogo
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"500x400+{x}+{y}")
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear widget de selección múltiple
        self.multiple_rep_widget = MultipleRepresentationWidget(
            main_frame, 
            available_parties,
            on_selection_change=None
        )
        self.multiple_rep_widget.pack(fill=tk.BOTH, expand=True)
        
        # Establecer selección actual si existe
        if self.selected_multiple_parties:
            current_ids = [p.get('rol_id') or p.get('id') for p in self.selected_multiple_parties]
            self.multiple_rep_widget.set_selected_parties(current_ids)
        
        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_accept():
            selected_parties = self.multiple_rep_widget.get_selected_parties()
            is_valid, error_msg = self.multiple_rep_widget.is_valid_selection()
            
            if not is_valid:
                messagebox.showerror("Error de Validación", error_msg, parent=dialog)
                return
            
            self.selected_multiple_parties = selected_parties
            self._update_multiple_rep_summary()
            dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Aceptar", command=on_accept).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=on_cancel).pack(side=tk.RIGHT)
        
        # Enfocar diálogo
        dialog.focus_set()

    def _get_representable_parties(self):
        """Obtiene las partes que pueden ser representadas (Actores, Demandados, Terceros)."""
        representable_parties = []
        
        for rol in self.existing_roles_en_caso:
            # Excluir el rol actual para evitar auto-representación
            if rol['rol_id'] == self.rol_id:
                continue
                
            # Solo permitir representar a partes principales
            if rol.get('rol_principal') in ['Actor', 'Demandado', 'Tercero']:
                representable_parties.append(rol)
        
        return representable_parties

    def _update_multiple_rep_summary(self):
        """Actualiza el resumen de representación múltiple."""
        if not self.selected_multiple_parties:
            self.multiple_rep_summary.config(text="Ninguna parte seleccionada", foreground='gray')
            return
        
        count = len(self.selected_multiple_parties)
        if count == 1:
            party_name = self.selected_multiple_parties[0].get('nombre_completo', 'N/A')
            summary_text = f"Representa a: {party_name}"
        else:
            party_names = [p.get('nombre_completo', 'N/A') for p in self.selected_multiple_parties]
            if count <= 3:
                names_text = ", ".join(party_names)
            else:
                names_text = ", ".join(party_names[:2]) + f" y {count-2} más"
            summary_text = f"Representa a {count} partes: {names_text}"
        
        self.multiple_rep_summary.config(text=summary_text, foreground='green')

    def _update_representa_combo(self):
        """Actualiza el combo de representación con lógica mejorada para distinguir partes principales."""
        # Filtrar roles que pueden ser representados (solo actores, demandados y terceros - NO abogados/apoderados)
        representables = {}
        
        for rol in self.existing_roles_en_caso:
            # Excluir el rol actual para evitar auto-representación
            if rol['rol_id'] == self.rol_id:
                continue
                
            # Solo permitir representar a partes principales (no a otros abogados/apoderados)
            if rol.get('rol_principal') in ['Actor', 'Demandado', 'Tercero']:
                # Crear una descripción más clara que incluya el tipo de parte
                descripcion = f"{rol['nombre_completo']} ({rol['rol_principal']})"
                representables[descripcion] = rol['rol_id']
        
        # Actualizar el combobox con las opciones disponibles
        self.representa_combo['values'] = list(representables.keys())
        self.representa_map = {nombre: rol_id for nombre, rol_id in representables.items()}

    def _save(self):
        """Guarda el contacto y rol con validación completa."""
        
        # 1. Validar formulario completo
        validation_errors = self._validate_form()
        if validation_errors:
            error_msg = "Se encontraron los siguientes errores:\n\n" + "\n".join(f"• {error}" for error in validation_errors)
            messagebox.showerror("Errores de Validación", error_msg, parent=self)
            return

        try:
            # 2. Recolectar datos del contacto
            datos_contacto = {key: var.get() for key, var in self.field_vars.items() if key != 'notas_generales'}
            datos_contacto['notas_generales'] = self.field_vars['notas_generales'].get('1.0', tk.END).strip()

            # 3. Guardar el contacto (crear o actualizar)
            if self.selected_contacto_id:
                success_contacto = self.db_crm.update_contacto(self.selected_contacto_id, datos_contacto)
                if not success_contacto:
                    messagebox.showerror("Error", "No se pudo actualizar el contacto.", parent=self)
                    return
                contacto_id = self.selected_contacto_id
                action_contacto = "actualizado"
            else:
                contacto_id = self.db_crm.add_contacto(datos_contacto)
                if not contacto_id:
                    messagebox.showerror("Error", "No se pudo crear el contacto.", parent=self)
                    return
                action_contacto = "creado"

            # 4. Determinar tipo de representación y procesar según corresponda
            rol_principal = self.rol_vars['rol_principal'].get()
            
            # Verificar si es abogado/apoderado y si se seleccionó representación múltiple
            has_representation_type = hasattr(self, 'representation_type')
            rep_type = self.representation_type.get() if has_representation_type else "simple"
            has_multiple_parties = bool(self.selected_multiple_parties) if hasattr(self, 'selected_multiple_parties') else False
            
            if (rol_principal in ['Abogado', 'Apoderado'] and 
                has_representation_type and 
                rep_type == "multiple" and 
                has_multiple_parties):
                
                # Representación múltiple
                success_rol = self._save_multiple_representation(contacto_id, action_contacto, datos_contacto)
                
            else:
                # Representación simple (comportamiento original)
                success_rol = self._save_simple_representation(contacto_id, action_contacto, datos_contacto)
            
            if not success_rol:
                messagebox.showerror("Error", "No se pudo guardar el rol en el caso.", parent=self)

        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error inesperado:\n{str(e)}", parent=self)

    def _save_simple_representation(self, contacto_id, action_contacto, datos_contacto):
        """Guarda una representación simple (comportamiento original)."""

        try:
            # Recolectar datos del rol
            datos_rol = {key: var.get() for key, var in self.rol_vars.items() if key != 'notas_del_rol'}
            datos_rol['notas_del_rol'] = self.rol_vars['notas_del_rol'].get('1.0', tk.END).strip()
            datos_rol['caso_id'] = self.caso_id
            datos_rol['contacto_id'] = contacto_id

            # Convertir nombre de representado a ID
            nombre_representado = self.rol_vars['representa_a_id'].get()
            if nombre_representado and hasattr(self, 'representa_map') and nombre_representado in self.representa_map:
                datos_rol['representa_a_id'] = self.representa_map[nombre_representado]
                print(f"[DEBUG] Asignando representación simple: {nombre_representado} -> ID {self.representa_map[nombre_representado]}")
            else:
                datos_rol['representa_a_id'] = None

            # Guardar el rol (crear o actualizar)
            if self.rol_id:
                print(f"[DEBUG] Modo edición - verificando tipo de representación actual")
                # En modo edición, verificar si era representación múltiple
                current_role_info = self.db_crm.get_multiple_representations(self.rol_id)
                print(f"[DEBUG] Info de rol actual: {current_role_info}")
                
                if current_role_info and current_role_info.get('is_multiple'):
                    print("[DEBUG] Era representación múltiple, convirtiendo a simple")
                    # Era representación múltiple, convertir a simple
                    # Eliminar todas las representaciones múltiples y crear una simple
                    if datos_rol.get('representa_a_id'):
                        print(f"[DEBUG] Actualizando a representación simple con ID: {datos_rol['representa_a_id']}")
                        success_rol = self.db_crm.update_multiple_representations(self.rol_id, [datos_rol['representa_a_id']])
                    else:
                        print("[DEBUG] Eliminando todas las representaciones múltiples")
                        # Sin representación - eliminar todas las representaciones múltiples
                        success_rol = self.db_crm.update_multiple_representations(self.rol_id, [])
                else:
                    print("[DEBUG] Era representación simple, actualizando normalmente")
                    # Era representación simple, actualizar normalmente
                    success_rol = self.db_crm.update_rol(self.rol_id, datos_rol)
                action_rol = "actualizado"
            else:
                print("[DEBUG] Modo creación - creando nuevo rol")
                success_rol = self.db_crm.add_rol_a_caso(datos_rol)
                action_rol = "creado"
            
            print(f"[DEBUG] Resultado del guardado: {success_rol}")

            if success_rol:
                # Mensaje de éxito
                mensaje = f"✅ Operación exitosa:\n\n"
                mensaje += f"• Contacto {action_contacto}: {datos_contacto['nombre_completo']}\n"
                mensaje += f"• Rol {action_rol}: {datos_rol['rol_principal']}"
                if datos_rol.get('rol_secundario'):
                    mensaje += f" ({datos_rol['rol_secundario']})"
                
                if datos_rol.get('representa_a_id'):
                    # Buscar nombre de la parte representada
                    representado_nombre = next((k for k, v in self.representa_map.items() if v == datos_rol['representa_a_id']), "N/A")
                    mensaje += f"\n• Representa a: {representado_nombre}"
                
                messagebox.showinfo("Éxito", mensaje, parent=self)
                
                # Refrescar vista y cerrar diálogo
                if hasattr(self.app_controller, 'refresh_current_case_view'):
                    self.app_controller.refresh_current_case_view()
                self._on_close()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error en representación simple: {e}")
            return False

    def _save_multiple_representation(self, contacto_id, action_contacto, datos_contacto):
        """Guarda una representación múltiple."""
        print(f"[DEBUG] Guardando representación múltiple - Contacto ID: {contacto_id}, Rol ID: {self.rol_id}")
        try:
            # Recolectar datos base del rol
            datos_rol = {key: var.get() for key, var in self.rol_vars.items() if key != 'notas_del_rol'}
            datos_rol['notas_del_rol'] = self.rol_vars['notas_del_rol'].get('1.0', tk.END).strip()
            
            # Obtener IDs de las partes seleccionadas
            represented_party_ids = [p.get('rol_id') or p.get('id') for p in self.selected_multiple_parties]
            
            if not represented_party_ids:
                messagebox.showerror("Error", "No se han seleccionado partes para representar.", parent=self)
                return False
            
            # Determinar si es creación o edición
            if self.rol_id:
                # Modo edición - actualizar representación múltiple existente
                success = self.db_crm.update_multiple_representations(self.rol_id, represented_party_ids)
                
                if success:
                    mensaje = f"✅ Representación múltiple actualizada exitosamente:\n\n"
                    mensaje += f"• Contacto {action_contacto}: {datos_contacto['nombre_completo']}\n"
                    mensaje += f"• Rol: {datos_rol['rol_principal']}"
                    if datos_rol.get('rol_secundario'):
                        mensaje += f" ({datos_rol['rol_secundario']})"
                    
                    mensaje += f"\n• Total de representaciones: {len(represented_party_ids)}\n"
                    mensaje += "• Partes representadas:\n"
                    
                    for party in self.selected_multiple_parties:
                        mensaje += f"  - {party['nombre_completo']} ({party['rol_principal']})\n"
                    
                    messagebox.showinfo("Éxito", mensaje, parent=self)
                    
                    # Refrescar vista y cerrar diálogo
                    if hasattr(self.app_controller, 'refresh_current_case_view'):
                        self.app_controller.refresh_current_case_view()
                    self._on_close()
                    return True
                else:
                    messagebox.showerror("Error", "No se pudo actualizar la representación múltiple.", parent=self)
                    return False
            else:
                # Modo creación - crear nueva representación múltiple
                result = self.db_crm.create_multiple_representations(
                    contacto_id, 
                    self.caso_id, 
                    datos_rol, 
                    represented_party_ids
                )
                
                if result and result.get('success'):
                    # Mensaje de éxito detallado
                    mensaje = f"✅ Representación múltiple creada exitosamente:\n\n"
                    mensaje += f"• Contacto {action_contacto}: {datos_contacto['nombre_completo']}\n"
                    mensaje += f"• Rol: {datos_rol['rol_principal']}"
                    if datos_rol.get('rol_secundario'):
                        mensaje += f" ({datos_rol['rol_secundario']})"
                    
                    mensaje += f"\n• Total de representaciones: {result['total_representations']}\n"
                    mensaje += "• Partes representadas:\n"
                    
                    for party in result['represented_parties']:
                        mensaje += f"  - {party['party_name']} ({party['party_role']})\n"
                    
                    messagebox.showinfo("Éxito", mensaje, parent=self)
                    
                    # Refrescar vista y cerrar diálogo
                    if hasattr(self.app_controller, 'refresh_current_case_view'):
                        self.app_controller.refresh_current_case_view()
                    self._on_close()
                    return True
                else:
                    messagebox.showerror("Error", "No se pudo crear la representación múltiple.", parent=self)
                    return False
                
        except Exception as e:
            print(f"Error en representación múltiple: {e}")
            messagebox.showerror("Error", f"Error al procesar representación múltiple: {str(e)}", parent=self)
            return False

    def _on_close(self):
        self.destroy()
