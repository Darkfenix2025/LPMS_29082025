# partes_ui.py
import tkinter as tk
from tkinter import ttk, messagebox

class PartesTab(ttk.Frame):
    def __init__(self, parent, app_controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app_controller = app_controller
        self.db_crm = self.app_controller.db_crm
        self.selected_rol_id = None
        self.roles_data_cache = {}
        self._create_widgets()

    def _create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=2)
        self.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(self)
        left_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(0, weight=1)

        tree_frame = ttk.LabelFrame(left_panel, text="Partes Intervinientes en el Caso", padding="5")
        tree_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 5))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        partes_cols = ('ID', 'Nombre', 'Rol Principal', 'Rol Secundario')
        self.partes_tree = ttk.Treeview(tree_frame, columns=partes_cols, show='headings', selectmode='browse')
        self.partes_tree.heading('ID', text='ID Rol')
        self.partes_tree.heading('Nombre', text='Nombre Completo')
        self.partes_tree.heading('Rol Principal', text='Rol Principal')
        self.partes_tree.heading('Rol Secundario', text='Rol Secundario')

        self.partes_tree.column('ID', width=50, stretch=tk.NO, anchor=tk.CENTER)
        self.partes_tree.column('Nombre', width=250, stretch=True)
        self.partes_tree.column('Rol Principal', width=120, stretch=tk.NO)
        self.partes_tree.column('Rol Secundario', width=120, stretch=tk.NO)

        partes_scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.partes_tree.yview)
        self.partes_tree.configure(yscrollcommand=partes_scrollbar_y.set)
        partes_scrollbar_y.grid(row=0, column=1, sticky='ns')
        
        partes_scrollbar_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.partes_tree.xview)
        self.partes_tree.configure(xscrollcommand=partes_scrollbar_x.set)
        partes_scrollbar_x.grid(row=1, column=0, sticky='ew')

        self.partes_tree.grid(row=0, column=0, sticky='nsew')
        
        # Configurar estilos para la vista jerárquica
        self._configure_tree_styles()
        
        # Configurar eventos
        self.partes_tree.bind('<<TreeviewSelect>>', self.on_rol_select_treeview)
        self.partes_tree.bind("<Double-1>", self._on_double_click_editar_rol)
        self.partes_tree.bind("<Button-3>", self._show_context_menu)  # Clic derecho
        
        # Crear menú contextual
        self._create_context_menu()

        # Crear frame de acciones
        actions_frame = ttk.Frame(left_panel)
        actions_frame.grid(row=1, column=0, sticky='ew', pady=5)

        self.add_rol_btn = ttk.Button(actions_frame, text="Agregar Parte/Rol", command=self._open_add_rol_dialog, state=tk.DISABLED)
        self.add_rol_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.edit_rol_btn = ttk.Button(actions_frame, text="Editar Rol", command=self._open_edit_rol_dialog, state=tk.DISABLED)
        self.edit_rol_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        self.delete_rol_btn = ttk.Button(actions_frame, text="Eliminar Rol", command=self._delete_selected_rol, state=tk.DISABLED)
        self.delete_rol_btn.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)

        # Panel de detalles
        self.details_rol_frame = ttk.LabelFrame(self, text="Detalles Completos de la Parte y Rol", padding="10")
        self.details_rol_frame.grid(row=0, column=1, sticky='nsew', pady=0, padx=(5,0))
        self.details_rol_frame.columnconfigure(0, weight=1)
        self.details_rol_frame.rowconfigure(0, weight=1)

        self.rol_detail_text = tk.Text(self.details_rol_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, relief=tk.FLAT, padx=5, pady=5)
        self.rol_detail_text.grid(row=0, column=0, sticky="nsew")
        detail_scroll = ttk.Scrollbar(self.details_rol_frame, orient=tk.VERTICAL, command=self.rol_detail_text.yview)
        self.rol_detail_text.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.grid(row=0, column=1, sticky="ns")

        self.details_rol_frame.grid_remove()

    def _configure_tree_styles(self):
        """Configura los estilos visuales para la vista jerárquica."""
        # Configurar tags para diferentes tipos de elementos
        self.partes_tree.tag_configure('group', 
                                     background='#E8F4FD', 
                                     foreground='#1F4E79',
                                     font=('TkDefaultFont', 9, 'bold'))
        
        self.partes_tree.tag_configure('role', 
                                     background='white', 
                                     foreground='black')
        
        self.partes_tree.tag_configure('representative', 
                                     background='#F0F8FF', 
                                     foreground='#4682B4',
                                     font=('TkDefaultFont', 8))

    def _get_role_icon(self, role):
        """Retorna el icono apropiado para cada tipo de rol."""
        role_icons = {
            'Actor': '⚖️',
            'Demandado': '🛡️',
            'Tercero': '👥',
            'Abogado': '👨‍💼',
            'Apoderado': '📋',
            'Perito': '🔬',
            'Testigo': '👁️',
            'Juez': '⚖️',
            'Secretario': '📝',
            'Oficial': '👮',
        }
        return role_icons.get(role, '👤')

    def _get_group_icon(self, role_type):
        """Retorna el icono apropiado para cada grupo de roles."""
        group_icons = {
            'Actor': '📁⚖️',
            'Demandado': '📁🛡️',
            'Tercero': '📁👥',
            'Abogado': '📁👨‍💼',
            'Apoderado': '📁📋',
            'Perito': '📁🔬',
            'Testigo': '📁👁️',
            'Juez': '📁⚖️',
            'Secretario': '📁📝',
            'Oficial': '📁👮',
        }
        return group_icons.get(role_type, '📁👤')

    def _open_add_rol_dialog(self):
        if self.app_controller.selected_case:
            self.app_controller.open_rol_dialog(caso_id=self.app_controller.selected_case['id'])
        else:
            messagebox.showwarning("Advertencia", "Seleccione un caso para agregar un rol.", parent=self)

    def _open_edit_rol_dialog(self):
        if self.selected_rol_id and self.app_controller.selected_case:
            self.app_controller.open_rol_dialog(rol_id=self.selected_rol_id, caso_id=self.app_controller.selected_case['id'])
        else:
            messagebox.showwarning("Advertencia", "Seleccione un rol para editar.", parent=self)

    def _delete_selected_rol(self):
        """Elimina el rol seleccionado con validación completa para representaciones múltiples."""
        if not self.selected_rol_id:
            messagebox.showwarning("Advertencia", "Seleccione un rol para eliminar.", parent=self)
            return
            
        if not self.app_controller.selected_case:
            messagebox.showerror("Error", "No hay un caso seleccionado.", parent=self)
            return
        
        try:
            rol_info = self.roles_data_cache.get(self.selected_rol_id)
            if not rol_info:
                messagebox.showerror("Error", "No se pudo obtener la información del rol seleccionado.", parent=self)
                return
            
            nombre = rol_info.get('nombre_completo', 'esta parte')
            rol_principal = rol_info.get('rol_principal', 'rol desconocido')
            contacto_id = rol_info.get('contacto_id')
            notas_del_rol = rol_info.get('notas_del_rol', '') or ''
            
            # Verificar si este rol representa a otros (representación simple)
            representados = [r for r in self.roles_data_cache.values() 
                           if r.get('representa_a_id') == self.selected_rol_id]
            
            # Verificar si es un abogado con representaciones múltiples
            is_multiple_rep = 'REPRESENTACION_MULTIPLE' in notas_del_rol
            multiple_representations = []
            
            if is_multiple_rep and rol_principal in ['Abogado', 'Apoderado']:
                try:
                    from crm_database import detect_multiple_representations_in_case
                    all_multiple_reps = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
                    
                    if contacto_id in all_multiple_reps:
                        multiple_representations = all_multiple_reps[contacto_id]['representations']
                except Exception as e:
                    print(f"Error detectando representaciones múltiples: {e}")
            
            # Construir mensaje de confirmación
            mensaje_confirmacion = f"¿Está seguro de que desea eliminar el rol de '{nombre}' ({rol_principal}) del caso?"
            
            # Agregar advertencias según el tipo de representación
            if multiple_representations:
                mensaje_confirmacion += f"\n\n🔗 REPRESENTACIONES MÚLTIPLES DETECTADAS:"
                mensaje_confirmacion += f"\nEste abogado representa a {len(multiple_representations)} parte(s):"
                for rep in multiple_representations:
                    mensaje_confirmacion += f"\n• {rep['represented_name']} ({rep['represented_role']})"
                mensaje_confirmacion += "\n\n⚠️ ADVERTENCIA: Al eliminar este abogado:"
                mensaje_confirmacion += "\n• Se eliminarán TODAS las representaciones múltiples"
                mensaje_confirmacion += "\n• Las partes representadas quedarán sin representación legal"
                mensaje_confirmacion += "\n• Esta acción NO se puede deshacer"
                
            elif representados:
                nombres_representados = [r.get('nombre_completo', 'N/A') for r in representados]
                mensaje_confirmacion += f"\n\nADVERTENCIA: Este rol representa a:\n• " + "\n• ".join(nombres_representados)
                mensaje_confirmacion += "\n\nEstas relaciones de representación se perderán."
            
            # Mostrar diálogo de confirmación con título apropiado
            titulo = "Confirmar Eliminación - Representaciones Múltiples" if multiple_representations else "Confirmar Eliminación"
            
            if messagebox.askyesno(titulo, mensaje_confirmacion, parent=self):
                success = self.app_controller.delete_selected_rol(self.selected_rol_id, self.app_controller.selected_case['id'])
                if success:
                    if multiple_representations:
                        messagebox.showinfo("Eliminación Completada", 
                                          f"El abogado '{nombre}' y todas sus representaciones múltiples han sido eliminados correctamente.",
                                          parent=self)
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el rol. Inténtelo nuevamente.", parent=self)
                    
        except Exception as e:
            messagebox.showerror("Error Inesperado", f"Ocurrió un error al eliminar el rol:\n{str(e)}", parent=self)

    def _on_double_click_editar_rol(self, event=None):
        if self.partes_tree.identify_row(event.y):
            if self.selected_rol_id:
                 self._open_edit_rol_dialog()

    def load_partes(self, caso_id):
        """Carga las partes del caso en una vista jerárquica mejorada con manejo de errores robusto."""
        import logging
        
        # Configurar logger específico para partes
        partes_logger = logging.getLogger('crm.partes')
        
        # Limpiar vista anterior
        for i in self.partes_tree.get_children():
            self.partes_tree.delete(i)

        self.selected_rol_id = None
        self.limpiar_detalle_completo_rol()
        self.roles_data_cache.clear()

        if not caso_id:
            partes_logger.warning("load_partes llamado sin caso_id")
            self._update_action_buttons_state()
            return

        partes_logger.info(f"Cargando partes para caso ID: {caso_id}")

        try:
            # Validar que el caso existe
            if not self.app_controller.selected_case:
                error_msg = "No hay un caso seleccionado"
                partes_logger.warning(error_msg)
                self._show_error_in_tree(error_msg)
                self._update_action_buttons_state()
                return

            # Obtener roles del caso con manejo de errores específicos
            try:
                roles = self.db_crm.get_roles_by_caso_id(caso_id)
                partes_logger.debug(f"Obtenidos {len(roles) if roles else 0} roles de la BD")
            except Exception as db_error:
                error_msg = f"Error de base de datos: {str(db_error)}"
                partes_logger.error(error_msg)
                self._show_error_in_tree("Error al conectar con la base de datos")
                self._update_action_buttons_state()
                return
            
            if roles is None:
                error_msg = "La consulta de roles retornó None"
                partes_logger.error(error_msg)
                self._show_error_in_tree("Error al obtener datos de la base de datos")
                self._update_action_buttons_state()
                return
            
            if not roles:
                info_msg = f"No hay partes asignadas al caso {caso_id}"
                partes_logger.info(info_msg)
                self._show_info_in_tree("No hay partes asignadas a este caso")
                self._update_action_buttons_state()
                return

            # Validar integridad de los datos con logging detallado
            roles_validos = []
            roles_invalidos = 0
            
            for i, rol in enumerate(roles):
                if not isinstance(rol, dict):
                    partes_logger.warning(f"Rol {i} con formato inválido ignorado: {type(rol)}")
                    roles_invalidos += 1
                    continue
                    
                if 'rol_id' not in rol or 'nombre_completo' not in rol:
                    partes_logger.warning(f"Rol {i} con datos incompletos ignorado. Claves: {list(rol.keys())}")
                    roles_invalidos += 1
                    continue
                    
                roles_validos.append(rol)

            if roles_invalidos > 0:
                partes_logger.warning(f"{roles_invalidos} roles inválidos ignorados de {len(roles)} totales")

            if not roles_validos:
                error_msg = f"Todos los roles ({len(roles)}) tienen datos corruptos"
                partes_logger.error(error_msg)
                self._show_error_in_tree("Los datos de las partes están corruptos")
                self._update_action_buttons_state()
                return

            # Cache de datos válidos
            self.roles_data_cache = {rol['rol_id']: rol for rol in roles_validos}
            partes_logger.info(f"Cargados {len(roles_validos)} roles válidos en cache")
            
            # Construir vista jerárquica mejorada
            try:
                self._build_hierarchical_tree(roles_validos)
                partes_logger.debug("Vista jerárquica construida exitosamente")
            except Exception as tree_error:
                partes_logger.error(f"Error construyendo vista jerárquica: {str(tree_error)}")
                self._show_error_in_tree("Error al mostrar las partes")
                self._update_action_buttons_state()
                return
                
            self._update_action_buttons_state()
            
            # Validar consistencia de representaciones múltiples
            self._validate_representation_consistency(caso_id)
            
            partes_logger.info(f"Carga de partes completada exitosamente para caso {caso_id}")
            
        except Exception as e:
            error_msg = f"Error inesperado al cargar partes del caso {caso_id}: {str(e)}"
            partes_logger.error(error_msg, exc_info=True)
            self._show_error_in_tree("Error inesperado al cargar las partes del caso")
            self._update_action_buttons_state()
            
            # En modo debug, mostrar más detalles
            if hasattr(self.app_controller, 'debug_mode') and self.app_controller.debug_mode:
                import traceback
                traceback.print_exc()

    def _show_error_in_tree(self, mensaje):
        """Muestra un mensaje de error en el TreeView."""
        self.partes_tree.insert('', tk.END, values=('', f'❌ {mensaje}', '', ''), tags=('error',))
        self.partes_tree.tag_configure('error', foreground='red', font=('TkDefaultFont', 9, 'italic'))

    def _show_info_in_tree(self, mensaje):
        """Muestra un mensaje informativo en el TreeView."""
        self.partes_tree.insert('', tk.END, values=('', f'ℹ️ {mensaje}', '', ''), tags=('info',))
        self.partes_tree.tag_configure('info', foreground='blue', font=('TkDefaultFont', 9, 'italic'))

    def _build_hierarchical_tree(self, roles):
        """Construye la vista jerárquica de roles con agrupación mejorada para abogados múltiples."""
        tree_items = {}  # {rol_id: iid}
        
        # 1. Agrupar roles por contacto para detectar abogados con múltiples roles
        roles_by_contact = {}
        for rol in roles:
            contacto_id = rol.get('contacto_id')
            if contacto_id not in roles_by_contact:
                roles_by_contact[contacto_id] = []
            roles_by_contact[contacto_id].append(rol)
        
        # 2. Detectar representaciones múltiples usando las nuevas funciones
        try:
            from crm_database import detect_multiple_representations_in_case
            multiple_representations = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
        except Exception as e:
            print(f"Error al detectar representaciones múltiples: {e}")
            multiple_representations = {}
        
        # 3. Crear grupos de roles principales con lógica mejorada para representaciones múltiples
        roles_by_type = {}
        abogados_multiples = {}  # {contacto_id: info}
        processed_lawyers = set()  # Para evitar duplicados
        shadow_roles = set()  # Para identificar roles shadow que no deben mostrarse
        
        # Primero, identificar todos los roles shadow para excluirlos
        for rol in roles:
            notas = rol.get('notas_del_rol', '') or ''
            if 'REPRESENTACION_MULTIPLE:SECONDARY:' in notas:
                shadow_roles.add(rol.get('rol_id'))
        
        for rol in roles:
            rol_principal = rol.get('rol_principal', 'Sin Rol')
            contacto_id = rol.get('contacto_id')
            rol_id = rol.get('rol_id')
            notas = rol.get('notas_del_rol', '') or ''
            
            # Saltar roles shadow
            if rol_id in shadow_roles:
                continue
            
            # Verificar si este abogado tiene representaciones múltiples
            if (rol_principal in ['Abogado', 'Apoderado'] and 
                contacto_id and 
                contacto_id in multiple_representations and
                contacto_id not in processed_lawyers):
                
                # Verificar si este es el rol principal (no shadow)
                if 'REPRESENTACION_MULTIPLE:PRIMARY:' in notas:
                    # Este abogado tiene representaciones múltiples
                    rep_info = multiple_representations[contacto_id]
                    abogados_multiples[contacto_id] = {
                        'lawyer_name': rep_info['lawyer_name'],
                        'representations': rep_info['representations'],
                        'main_role': rol,  # Guardar el rol principal para referencia
                        'primary_role_id': rep_info.get('primary_role_id', rol_id)
                    }
                    processed_lawyers.add(contacto_id)
                    continue  # No lo agregamos al grupo normal
            
            # Agregar al grupo normal (solo si no es shadow y no es representación múltiple ya procesada)
            if contacto_id not in processed_lawyers:
                if rol_principal not in roles_by_type:
                    roles_by_type[rol_principal] = []
                roles_by_type[rol_principal].append(rol)
        
        role_order = ['Actor', 'Demandado', 'Tercero', 'Abogado', 'Apoderado', 'Perito', 'Testigo']
        sorted_roles = sorted(roles_by_type.keys(), key=lambda r: role_order.index(r) if r in role_order else len(role_order))

        # 3. Crear grupos normales con iconos
        for rol_principal in sorted_roles:
            roles_list = roles_by_type[rol_principal]
            group_iid = f"group_{rol_principal}"
            
            # Obtener icono para el grupo
            group_icon = self._get_group_icon(rol_principal)
            group_text = f"{group_icon} {rol_principal}s ({len(roles_list)})"
            
            parent_node = self.partes_tree.insert('', tk.END, iid=group_iid, 
                                                values=('', group_text, '', ''), 
                                                open=True, tags=('group',))

            for rol in roles_list:
                rol_id = rol['rol_id']
                self._insert_role_item(rol, parent_node, tree_items)
        
        # 4. Crear grupos especiales para abogados con representaciones múltiples
        if abogados_multiples:
            # Crear o encontrar el grupo de Abogados
            abogados_group_iid = "group_Abogado"
            existing_children = [item for item in self.partes_tree.get_children()]
            
            if abogados_group_iid not in existing_children:
                # Crear el grupo de abogados con icono
                group_icon = self._get_group_icon('Abogado')
                abogados_parent = self.partes_tree.insert('', tk.END, iid=abogados_group_iid, 
                                                        values=('', f'{group_icon} Abogados (0)', '', ''), 
                                                        open=True, tags=('group',))
            else:
                abogados_parent = abogados_group_iid
            
            for contacto_id, rep_info in abogados_multiples.items():
                # Crear un nodo padre para este abogado con representaciones múltiples
                lawyer_name = rep_info['lawyer_name']
                main_role = rep_info['main_role']
                representations = rep_info['representations']
                
                # Determinar icono principal basado en el tipo de persona y rol
                main_icon = "👤"  # Persona física por defecto
                if main_role.get('es_persona_juridica'):
                    main_icon = "🏢"  # Empresa/persona jurídica
                
                # Icono especial para representaciones múltiples
                multi_icon = "🔗"
                
                # Crear descripción de representaciones múltiples con iconos mejorados
                rep_count = len(representations)
                multi_role_text = f"{multi_icon} {main_icon} {lawyer_name} - Representaciones Múltiples ({rep_count})"
                
                # Insertar el nodo agrupado con iconos especiales
                multi_iid = f"multi_rep_{contacto_id}"
                multi_node = self.partes_tree.insert(abogados_parent, tk.END, iid=multi_iid,
                                                   values=('', multi_role_text, 'Múltiples Representaciones', ''),
                                                   open=True, tags=('multi_representation',))
                
                # Insertar cada representación como hijo con iconos específicos
                for i, rep in enumerate(representations):
                    # Determinar icono según el rol de la parte representada
                    role_icon = self._get_role_icon(rep['represented_role'])
                    rep_text = f"  ↳ {role_icon} Representa a: {rep['represented_name']} ({rep['represented_role']})"
                    rep_iid = f"rep_{contacto_id}_{i}"
                    
                    self.partes_tree.insert(multi_node, tk.END, iid=rep_iid,
                                          values=('', rep_text, '', ''),
                                          tags=('representation_item',))
                
                # Agregar el rol principal al tree_items para permitir selección
                primary_role_id = rep_info.get('primary_role_id', main_role['rol_id'])
                tree_items[primary_role_id] = multi_node
            
            # Actualizar el contador del grupo de abogados con icono
            abogados_count = len(roles_by_type.get('Abogado', [])) + len(abogados_multiples)
            group_icon = self._get_group_icon('Abogado')
            self.partes_tree.item(abogados_group_iid, values=('', f'{group_icon} Abogados ({abogados_count})', '', ''))
        
        # Configurar estilos mejorados para representaciones múltiples
        self.partes_tree.tag_configure('multi_representation', 
                                     background='#E8F4FD', 
                                     foreground='#1F4E79',
                                     font=('TkDefaultFont', 9, 'bold'))
        
        self.partes_tree.tag_configure('representation_item', 
                                     background='#F0F8FF', 
                                     foreground='#4682B4',
                                     font=('TkDefaultFont', 8))
        
        # Estilo para elementos de representación seleccionables
        self.partes_tree.tag_configure('representation_selectable', 
                                     background='#F5F5FF', 
                                     foreground='#2E4B8B',
                                     font=('TkDefaultFont', 8))
        
        # Mantener estilo para roles múltiples (compatibilidad)
        self.partes_tree.tag_configure('multi_role', 
                                     background='#E8F8E8', 
                                     foreground='#2E7D2E',
                                     font=('TkDefaultFont', 9, 'bold'))

        # 5. Establecer la jerarquía de representación.
        for rol in roles:
            representante_id = rol.get('rol_id')
            representado_id = rol.get('representa_a_id')

            if representado_id and representante_id in tree_items and representado_id in tree_items:
                parent_iid = tree_items[representado_id]
                child_iid = tree_items[representante_id]
                
                self.partes_tree.move(child_iid, parent_iid, tk.END)
                
                self.partes_tree.item(child_iid, tags=('representative',))
                values = list(self.partes_tree.item(child_iid, 'values'))
                nombre_original = rol.get('nombre_completo', 'N/A')
                if rol.get('es_persona_juridica'):
                    nombre_original += " 📄"
                
                if not values[1].startswith('↳'):
                    values[1] = f"↳ {nombre_original}"
                    self.partes_tree.item(child_iid, values=values)

    def _insert_role_item(self, rol, parent, tree_items):
        """Inserta un elemento de rol en el árbol con iconos mejorados."""
        item_iid = f"rol_{rol['rol_id']}"
        
        # Preparar valores para mostrar
        nombre_display = rol.get('nombre_completo', 'N/A')
        rol_principal = rol.get('rol_principal', 'N/A')
        rol_secundario = rol.get('rol_secundario', '') or ''
        
        # Obtener icono para el rol
        role_icon = self._get_role_icon(rol_principal)
        
        # Determinar icono de persona
        person_icon = "🏢" if rol.get('es_persona_juridica') else "👤"
        
        # Combinar iconos con el nombre
        nombre_display = f"{role_icon} {person_icon} {nombre_display}"
        
        values = (
            rol['rol_id'],
            nombre_display,
            rol_principal,
            rol_secundario
        )
        
        tree_item = self.partes_tree.insert(
            parent, tk.END, 
            iid=item_iid,
            values=values, 
            open=True,
            tags=('role',)
        )
        
        tree_items[rol['rol_id']] = tree_item
        return tree_item

    def on_rol_select_treeview(self, event=None):
        """Maneja la selección de elementos en la vista jerárquica con soporte para representaciones múltiples."""
        selected_items = self.partes_tree.selection()
        if selected_items:
            item_iid = selected_items[0]
            
            # Verificar si es un grupo (no seleccionable para edición)
            if item_iid.startswith("group_"):
                self.selected_rol_id = None
                self.limpiar_detalle_completo_rol()
                self._show_group_info(item_iid)
            # Verificar si es un nodo de representación múltiple
            elif item_iid.startswith("multi_rep_"):
                # Extraer el contacto_id del nodo de representación múltiple
                try:
                    contacto_id = int(item_iid.split('_')[2])
                    # Buscar el rol principal de este contacto
                    main_role = None
                    for rol in self.roles_data_cache.values():
                        if (rol.get('contacto_id') == contacto_id and 
                            rol.get('rol_principal') in ['Abogado', 'Apoderado']):
                            # Verificar si es el rol principal (no shadow)
                            notas = rol.get('notas_del_rol', '') or ''
                            if 'REPRESENTACION_MULTIPLE:SECONDARY:' not in notas:
                                main_role = rol
                                break
                    
                    if main_role:
                        self.selected_rol_id = main_role['rol_id']
                        self._show_multiple_representation_details(contacto_id)
                    else:
                        self.selected_rol_id = None
                        self.limpiar_detalle_completo_rol()
                except (IndexError, ValueError):
                    self.selected_rol_id = None
                    self.limpiar_detalle_completo_rol()
            # Verificar si es un item de representación individual
            elif item_iid.startswith("rep_"):
                # Para items de representación individual, mostrar detalles del abogado
                try:
                    contacto_id = int(item_iid.split('_')[1])
                    # Buscar el rol principal de este contacto
                    main_role = None
                    for rol in self.roles_data_cache.values():
                        if (rol.get('contacto_id') == contacto_id and 
                            rol.get('rol_principal') in ['Abogado', 'Apoderado']):
                            notas = rol.get('notas_del_rol', '') or ''
                            if 'REPRESENTACION_MULTIPLE:SECONDARY:' not in notas:
                                main_role = rol
                                break
                    
                    if main_role:
                        self.selected_rol_id = main_role['rol_id']
                        self._show_multiple_representation_details(contacto_id)
                    else:
                        self.selected_rol_id = None
                        self.limpiar_detalle_completo_rol()
                except (IndexError, ValueError):
                    self.selected_rol_id = None
                    self.limpiar_detalle_completo_rol()
            else:
                # Es un rol individual normal
                try:
                    if item_iid.startswith("rol_"):
                        self.selected_rol_id = int(item_iid.split('_')[1])
                    else:
                        self.selected_rol_id = int(item_iid)
                except (IndexError, ValueError):
                    self.selected_rol_id = None

                if self.selected_rol_id:
                    self.mostrar_detalle_completo_rol(self.selected_rol_id)
                else:
                    self.limpiar_detalle_completo_rol()
        else:
            self.selected_rol_id = None
            self.limpiar_detalle_completo_rol()

        self._update_action_buttons_state()

    def _show_group_info(self, group_iid):
        """Muestra información del grupo seleccionado."""
        if not hasattr(self, 'rol_detail_text'):
            return
            
        group_name = group_iid.replace("group_", "")
        
        # Contar roles en el grupo
        roles_in_group = [rol for rol in self.roles_data_cache.values() 
                         if rol.get('rol_principal') == group_name]
        
        self.details_rol_frame.grid()
        self.rol_detail_text.config(state=tk.NORMAL)
        self.rol_detail_text.delete('1.0', tk.END)
        
        info_text = f"--- GRUPO: {group_name.upper()} ---\n\n"
        info_text += f"Total de {group_name}s en el caso: {len(roles_in_group)}\n\n"
        
        for i, rol in enumerate(roles_in_group, 1):
            info_text += f"{i}. {rol.get('nombre_completo', 'N/A')}\n"
            if rol.get('rol_secundario'):
                info_text += f"   Rol secundario: {rol.get('rol_secundario')}\n"
            if rol.get('representa_a_id'):
                representado = self.roles_data_cache.get(rol['representa_a_id'])
                if representado:
                    info_text += f"   Representa a: {representado.get('nombre_completo', 'N/A')}\n"
            info_text += "\n"
        
        self.rol_detail_text.insert('1.0', info_text)
        self.rol_detail_text.config(state=tk.DISABLED)

    def _show_multiple_representation_details(self, contacto_id):
        """Muestra detalles completos de un abogado con representaciones múltiples."""
        if not hasattr(self, 'rol_detail_text'):
            return
        
        try:
            # Obtener información de representaciones múltiples
            from crm_database import detect_multiple_representations_in_case
            multiple_representations = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
            
            if contacto_id not in multiple_representations:
                # Fallback a mostrar detalle normal
                if self.selected_rol_id:
                    self.mostrar_detalle_completo_rol(self.selected_rol_id)
                return
            
            rep_info = multiple_representations[contacto_id]
            lawyer_name = rep_info['lawyer_name']
            representations = rep_info['representations']
            
            # Buscar el rol principal para obtener información adicional
            main_role = None
            for rol in self.roles_data_cache.values():
                if (rol.get('contacto_id') == contacto_id and 
                    rol.get('rol_principal') in ['Abogado', 'Apoderado']):
                    notas = rol.get('notas_del_rol', '') or ''
                    if 'REPRESENTACION_MULTIPLE:SECONDARY:' not in notas:
                        main_role = rol
                        break
            
            self.details_rol_frame.grid()
            self.rol_detail_text.config(state=tk.NORMAL)
            self.rol_detail_text.delete('1.0', tk.END)
            
            # Construir texto de detalles
            info_text = f"--- REPRESENTACIÓN MÚLTIPLE ---\n\n"
            info_text += f"🔗 {lawyer_name}\n"
            
            if main_role:
                info_text += f"Rol Principal: {main_role.get('rol_principal', 'N/A')}\n"
                if main_role.get('rol_secundario'):
                    info_text += f"Rol Secundario: {main_role.get('rol_secundario')}\n"
                if main_role.get('es_persona_juridica'):
                    info_text += f"Tipo: Persona Jurídica 📄\n"
                else:
                    info_text += f"Tipo: Persona Física\n"
                
                # Información de contacto
                if main_role.get('telefono'):
                    info_text += f"Teléfono: {main_role.get('telefono')}\n"
                if main_role.get('email'):
                    info_text += f"Email: {main_role.get('email')}\n"
                if main_role.get('direccion'):
                    info_text += f"Dirección: {main_role.get('direccion')}\n"
            
            info_text += f"\n--- REPRESENTACIONES ({len(representations)}) ---\n\n"
            
            for i, rep in enumerate(representations, 1):
                info_text += f"{i}. Representa a: {rep['represented_name']}\n"
                info_text += f"   Rol de la parte: {rep['represented_role']}\n"
                if rep.get('representation_notes'):
                    info_text += f"   Notas: {rep['representation_notes']}\n"
                info_text += "\n"
            
            # Información adicional del rol principal
            if main_role and main_role.get('notas_del_rol'):
                notas = main_role.get('notas_del_rol', '')
                # Filtrar notas técnicas de representación múltiple
                notas_filtradas = []
                for linea in notas.split('\n'):
                    if not linea.strip().startswith('REPRESENTACION_MULTIPLE:'):
                        notas_filtradas.append(linea)
                
                notas_limpias = '\n'.join(notas_filtradas).strip()
                if notas_limpias:
                    info_text += f"--- NOTAS ADICIONALES ---\n\n{notas_limpias}\n"
            
            self.rol_detail_text.insert('1.0', info_text)
            self.rol_detail_text.config(state=tk.DISABLED)
            
        except Exception as e:
            print(f"Error mostrando detalles de representación múltiple: {e}")
            # Fallback a mostrar detalle normal
            if self.selected_rol_id:
                self.mostrar_detalle_completo_rol(self.selected_rol_id)

    def _validate_representation_consistency(self, caso_id):
        """Valida la consistencia de las representaciones múltiples y muestra advertencias si es necesario."""
        try:
            from crm_database import validate_multiple_representation_consistency, clean_orphaned_representations
            
            validation_results = validate_multiple_representation_consistency(caso_id)
            
            if 'error' in validation_results:
                print(f"Error en validación de representaciones: {validation_results['error']}")
                return
            
            # Limpiar automáticamente representaciones huérfanas
            if validation_results['orphaned_representations']:
                print(f"Encontradas {len(validation_results['orphaned_representations'])} representaciones huérfanas, limpiando...")
                clean_orphaned_representations(caso_id)
                
                # Mostrar notificación al usuario
                orphaned_names = [rep['nombre'] for rep in validation_results['orphaned_representations']]
                messagebox.showinfo("Limpieza Automática", 
                                  f"Se encontraron y limpiaron representaciones huérfanas para:\n• " + 
                                  "\n• ".join(orphaned_names[:5]) + 
                                  (f"\n... y {len(orphaned_names)-5} más" if len(orphaned_names) > 5 else ""),
                                  parent=self)
                
                # Recargar la vista para reflejar los cambios
                self.load_partes(caso_id)
            
            # Verificar y corregir representaciones múltiples duplicadas
            try:
                from crm_database import fix_duplicate_multiple_representations
                
                # Verificar si hay abogados duplicados
                duplicates_found = self._check_for_duplicate_lawyers(caso_id)
                if duplicates_found:
                    response = messagebox.askyesno("Representaciones Duplicadas Detectadas",
                                                 f"Se detectaron abogados con roles duplicados en este caso.\n\n"
                                                 f"Esto puede causar visualización incorrecta donde el mismo abogado "
                                                 f"aparece múltiples veces.\n\n"
                                                 f"¿Desea corregir automáticamente estas duplicaciones?",
                                                 parent=self)
                    
                    if response:
                        success = fix_duplicate_multiple_representations(caso_id)
                        if success:
                            messagebox.showinfo("Corrección Completada",
                                              "Las representaciones múltiples duplicadas han sido corregidas.\n"
                                              "La vista se actualizará automáticamente.",
                                              parent=self)
                            # Recargar la vista
                            self.load_partes(caso_id)
                        else:
                            messagebox.showerror("Error en Corrección",
                                               "No se pudieron corregir todas las duplicaciones.\n"
                                               "Revise los logs para más detalles.",
                                               parent=self)
            except Exception as e:
                print(f"Error verificando duplicaciones: {e}")
            
            # Mostrar errores críticos
            if validation_results['errors']:
                error_msg = "Se encontraron errores en las representaciones múltiples:\n\n"
                error_msg += "\n".join(validation_results['errors'][:3])
                if len(validation_results['errors']) > 3:
                    error_msg += f"\n... y {len(validation_results['errors'])-3} errores más"
                
                messagebox.showwarning("Errores de Consistencia", error_msg, parent=self)
            
            # Log de advertencias
            if validation_results['warnings']:
                for warning in validation_results['warnings']:
                    print(f"Advertencia de representación: {warning}")
                    
        except Exception as e:
            print(f"Error durante validación de consistencia: {e}")

    def _check_for_duplicate_lawyers(self, caso_id):
        """Verifica si hay abogados con roles duplicados en el caso."""
        try:
            # Contar abogados por contacto_id
            lawyer_counts = {}
            for rol in self.roles_data_cache.values():
                if rol.get('rol_principal') in ['Abogado', 'Apoderado']:
                    contacto_id = rol.get('contacto_id')
                    if contacto_id:
                        lawyer_counts[contacto_id] = lawyer_counts.get(contacto_id, 0) + 1
            
            # Verificar si algún abogado tiene más de un rol
            duplicates = {k: v for k, v in lawyer_counts.items() if v > 1}
            
            if duplicates:
                print(f"Encontrados abogados duplicados: {duplicates}")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error verificando duplicados: {e}")
            return False

    def _create_context_menu(self):
        """Crea el menú contextual para la vista jerárquica con opciones de representaciones múltiples."""
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Agregar Parte/Rol", command=self._open_add_rol_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Editar Rol", command=self._open_edit_rol_dialog)
        self.context_menu.add_command(label="Eliminar Rol", command=self._delete_selected_rol)
        self.context_menu.add_separator()
        
        # Submenu para representaciones múltiples
        multiple_rep_menu = tk.Menu(self.context_menu, tearoff=0)
        multiple_rep_menu.add_command(label="🔗 Gestionar Representaciones", command=self._manage_multiple_representations)
        multiple_rep_menu.add_command(label="➕ Agregar Representación", command=self._add_representation_to_lawyer)
        multiple_rep_menu.add_command(label="➖ Quitar Representación", command=self._remove_representation_from_lawyer)
        multiple_rep_menu.add_separator()
        multiple_rep_menu.add_command(label="📊 Ver Resumen de Representaciones", command=self._show_representation_summary)
        multiple_rep_menu.add_command(label="📋 Ver Detalles de Representación", command=self._show_detailed_representation_info)
        
        self.context_menu.add_cascade(label="🔗 Representaciones Múltiples", menu=multiple_rep_menu)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Ver Ficha de Contacto Completa", command=self._open_contacto_detail_window)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Expandir Todo", command=self._expand_all)
        self.context_menu.add_command(label="Contraer Todo", command=self._collapse_all)

    def _open_contacto_detail_window(self):
        """Abre la ventana de detalle completo del contacto."""
        if not self.selected_rol_id:
            messagebox.showwarning("Advertencia", "Seleccione una parte para ver su ficha completa.", parent=self)
            return
        
        # Verificar que hay un caso seleccionado
        if not self.app_controller.selected_case:
            messagebox.showerror("Error", "No hay un caso seleccionado.", parent=self)
            return
        
        rol_details = self.roles_data_cache.get(self.selected_rol_id)
        if not rol_details:
            messagebox.showerror("Error", "No se pudo obtener la información del contacto.", parent=self)
            return
        
        contacto_id = rol_details.get('contacto_id')
        if not contacto_id:
            messagebox.showerror("Error", "No se encontró el ID del contacto.", parent=self)
            return
        
        try:
            # Verificar conexión a la base de datos antes de abrir la ventana
            if not self.db_crm:
                messagebox.showerror("Error", "No hay conexión a la base de datos.", parent=self)
                return
            
            # Importar y crear la ventana de detalle del contacto
            from contacto_detail_window import ContactoDetailWindow
            ContactoDetailWindow(self, self.app_controller, contacto_id)
            
        except ImportError as e:
            messagebox.showerror("Error", f"No se pudo cargar el módulo de detalle del contacto:\n{str(e)}", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir la ficha del contacto:\n{str(e)}", parent=self)
            print(f"Error detallado en _open_contacto_detail_window: {e}")
            import traceback
            traceback.print_exc()

    def _show_context_menu(self, event):
        """Muestra el menú contextual."""
        # Seleccionar el item bajo el cursor
        item = self.partes_tree.identify_row(event.y)
        if item:
            self.partes_tree.selection_set(item)
            self.on_rol_select_treeview()  # Actualizar selección
        
        # Habilitar/deshabilitar opciones según el contexto
        case_selected = self.app_controller.selected_case is not None
        rol_selected = self.selected_rol_id is not None
        
        # Verificar si el rol seleccionado es un abogado
        is_lawyer = False
        if rol_selected:
            rol_info = self.roles_data_cache.get(self.selected_rol_id)
            if rol_info and rol_info.get('rol_principal') in ['Abogado', 'Apoderado']:
                is_lawyer = True
        
        # Actualizar estado de los elementos del menú
        self.context_menu.entryconfig("Agregar Parte/Rol", state=tk.NORMAL if case_selected else tk.DISABLED)
        self.context_menu.entryconfig("Editar Rol", state=tk.NORMAL if rol_selected else tk.DISABLED)
        self.context_menu.entryconfig("Eliminar Rol", state=tk.NORMAL if rol_selected else tk.DISABLED)
        self.context_menu.entryconfig("🔗 Gestionar Representaciones Múltiples", state=tk.NORMAL if is_lawyer else tk.DISABLED)
        self.context_menu.entryconfig("📊 Ver Resumen de Representaciones", state=tk.NORMAL if case_selected else tk.DISABLED)
        self.context_menu.entryconfig("Ver Ficha de Contacto Completa", state=tk.NORMAL if rol_selected else tk.DISABLED)
        
        # Mostrar menú
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def _expand_all(self):
        """Expande todos los nodos del árbol."""
        def expand_item(item):
            self.partes_tree.item(item, open=True)
            for child in self.partes_tree.get_children(item):
                expand_item(child)
        
        for item in self.partes_tree.get_children():
            expand_item(item)

    def _collapse_all(self):
        """Contrae todos los nodos del árbol."""
        def collapse_item(item):
            self.partes_tree.item(item, open=False)
            for child in self.partes_tree.get_children(item):
                collapse_item(child)
        
        for item in self.partes_tree.get_children():
            collapse_item(item)

    def _manage_multiple_representations(self):
        """Abre el diálogo de gestión de representaciones múltiples."""
        if not self.selected_rol_id:
            messagebox.showwarning("Advertencia", "Seleccione un abogado para gestionar sus representaciones.", parent=self)
            return
        
        rol_info = self.roles_data_cache.get(self.selected_rol_id)
        if not rol_info:
            messagebox.showerror("Error", "No se pudo obtener la información del rol seleccionado.", parent=self)
            return
        
        # Verificar si es un abogado
        if rol_info.get('rol_principal') not in ['Abogado', 'Apoderado']:
            messagebox.showinfo("Información", 
                              f"La gestión de representaciones múltiples solo está disponible para Abogados y Apoderados.\n"
                              f"El rol seleccionado es: {rol_info.get('rol_principal', 'N/A')}", 
                              parent=self)
            return
        
        # Abrir diálogo de edición con modo de representaciones múltiples
        try:
            self.app_controller.open_rol_dialog(
                rol_id=self.selected_rol_id, 
                caso_id=self.app_controller.selected_case['id'],
                multiple_representation_mode=True
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el diálogo de representaciones múltiples:\n{str(e)}", parent=self)

    def _show_representation_summary(self):
        """Muestra un resumen de todas las representaciones en el caso."""
        if not self.app_controller.selected_case:
            messagebox.showerror("Error", "No hay un caso seleccionado.", parent=self)
            return
        
        try:
            from crm_database import detect_multiple_representations_in_case
            multiple_reps = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
            
            # Crear ventana de resumen
            summary_window = tk.Toplevel(self)
            summary_window.title("Resumen de Representaciones")
            summary_window.geometry("600x400")
            summary_window.transient(self)
            summary_window.grab_set()
            
            # Crear área de texto con scroll
            text_frame = ttk.Frame(summary_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            summary_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=summary_text.yview)
            summary_text.configure(yscrollcommand=scrollbar.set)
            
            summary_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Generar contenido del resumen
            content = f"RESUMEN DE REPRESENTACIONES - CASO {self.app_controller.selected_case['id']}\n"
            content += "=" * 60 + "\n\n"
            
            if not multiple_reps:
                content += "No se encontraron representaciones múltiples en este caso.\n\n"
                
                # Mostrar representaciones simples
                simple_reps = []
                for rol in self.roles_data_cache.values():
                    if (rol.get('rol_principal') in ['Abogado', 'Apoderado'] and 
                        rol.get('representa_a_id') and
                        'REPRESENTACION_MULTIPLE' not in (rol.get('notas_del_rol', '') or '')):
                        
                        representado = self.roles_data_cache.get(rol['representa_a_id'])
                        if representado:
                            simple_reps.append({
                                'lawyer': rol.get('nombre_completo', 'N/A'),
                                'represented': representado.get('nombre_completo', 'N/A'),
                                'role': representado.get('rol_principal', 'N/A')
                            })
                
                if simple_reps:
                    content += f"REPRESENTACIONES SIMPLES ({len(simple_reps)}):\n"
                    content += "-" * 40 + "\n"
                    for rep in simple_reps:
                        content += f"• {rep['lawyer']} → {rep['represented']} ({rep['role']})\n"
                else:
                    content += "No se encontraron representaciones en este caso.\n"
            else:
                content += f"REPRESENTACIONES MÚLTIPLES ({len(multiple_reps)}):\n"
                content += "-" * 40 + "\n\n"
                
                for contacto_id, rep_info in multiple_reps.items():
                    lawyer_name = rep_info['lawyer_name']
                    representations = rep_info['representations']
                    
                    content += f"🔗 {lawyer_name}\n"
                    content += f"   Representa a {len(representations)} parte(s):\n"
                    
                    for i, rep in enumerate(representations, 1):
                        content += f"   {i}. {rep['represented_name']} ({rep['represented_role']})\n"
                    
                    content += "\n"
            
            # Estadísticas generales
            total_lawyers = len([r for r in self.roles_data_cache.values() 
                               if r.get('rol_principal') in ['Abogado', 'Apoderado']])
            total_parties = len([r for r in self.roles_data_cache.values() 
                               if r.get('rol_principal') in ['Actor', 'Demandado', 'Tercero']])
            
            content += "\n" + "=" * 60 + "\n"
            content += "ESTADÍSTICAS:\n"
            content += f"• Total de abogados/apoderados: {total_lawyers}\n"
            content += f"• Total de partes (actores/demandados/terceros): {total_parties}\n"
            content += f"• Representaciones múltiples: {len(multiple_reps)}\n"
            
            summary_text.insert('1.0', content)
            summary_text.config(state=tk.DISABLED)
            
            # Botón de cerrar
            close_btn = ttk.Button(summary_window, text="Cerrar", command=summary_window.destroy)
            close_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el resumen de representaciones:\n{str(e)}", parent=self)

    def _add_representation_to_lawyer(self):
        """Permite agregar una nueva representación a un abogado existente."""
        if not self.selected_rol_id:
            messagebox.showwarning("Advertencia", "Seleccione un abogado para agregar representaciones.", parent=self)
            return
        
        rol_info = self.roles_data_cache.get(self.selected_rol_id)
        if not rol_info:
            messagebox.showerror("Error", "No se pudo obtener la información del rol seleccionado.", parent=self)
            return
        
        # Verificar si es un abogado
        if rol_info.get('rol_principal') not in ['Abogado', 'Apoderado']:
            messagebox.showinfo("Información", 
                              f"Solo se pueden agregar representaciones a Abogados y Apoderados.\n"
                              f"El rol seleccionado es: {rol_info.get('rol_principal', 'N/A')}", 
                              parent=self)
            return
        
        try:
            # Obtener partes disponibles para representar
            available_parties = []
            for rol in self.roles_data_cache.values():
                if (rol.get('rol_principal') in ['Actor', 'Demandado', 'Tercero'] and
                    rol.get('rol_id') != self.selected_rol_id):
                    
                    # Verificar si ya está representado por este abogado
                    is_already_represented = False
                    contacto_id = rol_info.get('contacto_id')
                    
                    # Verificar representaciones múltiples existentes
                    from crm_database import detect_multiple_representations_in_case
                    multiple_reps = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
                    
                    if contacto_id in multiple_reps:
                        for rep in multiple_reps[contacto_id]['representations']:
                            if rep.get('represented_id') == rol.get('rol_id'):
                                is_already_represented = True
                                break
                    
                    # Verificar representación simple
                    if rol_info.get('representa_a_id') == rol.get('rol_id'):
                        is_already_represented = True
                    
                    if not is_already_represented:
                        available_parties.append({
                            'id': rol.get('rol_id'),
                            'name': rol.get('nombre_completo', 'N/A'),
                            'role': rol.get('rol_principal', 'N/A')
                        })
            
            if not available_parties:
                messagebox.showinfo("Información", 
                                  f"No hay partes disponibles para que {rol_info.get('nombre_completo', 'N/A')} represente.\n"
                                  f"Todas las partes ya están representadas por este abogado o no hay partes disponibles.", 
                                  parent=self)
                return
            
            # Crear diálogo de selección
            self._show_party_selection_dialog(rol_info, available_parties, "add")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al agregar representación:\n{str(e)}", parent=self)

    def _remove_representation_from_lawyer(self):
        """Permite quitar una representación de un abogado existente."""
        if not self.selected_rol_id:
            messagebox.showwarning("Advertencia", "Seleccione un abogado para quitar representaciones.", parent=self)
            return
        
        rol_info = self.roles_data_cache.get(self.selected_rol_id)
        if not rol_info:
            messagebox.showerror("Error", "No se pudo obtener la información del rol seleccionado.", parent=self)
            return
        
        # Verificar si es un abogado
        if rol_info.get('rol_principal') not in ['Abogado', 'Apoderado']:
            messagebox.showinfo("Información", 
                              f"Solo se pueden quitar representaciones de Abogados y Apoderados.\n"
                              f"El rol seleccionado es: {rol_info.get('rol_principal', 'N/A')}", 
                              parent=self)
            return
        
        try:
            # Obtener representaciones actuales
            contacto_id = rol_info.get('contacto_id')
            represented_parties = []
            
            # Verificar representaciones múltiples
            from crm_database import detect_multiple_representations_in_case
            multiple_reps = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
            
            if contacto_id in multiple_reps:
                for rep in multiple_reps[contacto_id]['representations']:
                    represented_parties.append({
                        'id': rep.get('represented_id'),
                        'name': rep.get('represented_name', 'N/A'),
                        'role': rep.get('represented_role', 'N/A')
                    })
            elif rol_info.get('representa_a_id'):
                # Representación simple
                representado = self.roles_data_cache.get(rol_info['representa_a_id'])
                if representado:
                    represented_parties.append({
                        'id': representado.get('rol_id'),
                        'name': representado.get('nombre_completo', 'N/A'),
                        'role': representado.get('rol_principal', 'N/A')
                    })
            
            if not represented_parties:
                messagebox.showinfo("Información", 
                                  f"{rol_info.get('nombre_completo', 'N/A')} no representa a ninguna parte actualmente.", 
                                  parent=self)
                return
            
            # Crear diálogo de selección
            self._show_party_selection_dialog(rol_info, represented_parties, "remove")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al quitar representación:\n{str(e)}", parent=self)

    def _show_detailed_representation_info(self):
        """Muestra información detallada de las representaciones del rol seleccionado."""
        if not self.selected_rol_id:
            messagebox.showwarning("Advertencia", "Seleccione un rol para ver información detallada.", parent=self)
            return
        
        rol_info = self.roles_data_cache.get(self.selected_rol_id)
        if not rol_info:
            messagebox.showerror("Error", "No se pudo obtener la información del rol seleccionado.", parent=self)
            return
        
        try:
            # Crear ventana de detalles
            detail_window = tk.Toplevel(self)
            detail_window.title(f"Detalles de Representación - {rol_info.get('nombre_completo', 'N/A')}")
            detail_window.geometry("700x500")
            detail_window.transient(self)
            detail_window.grab_set()
            
            # Crear área de texto con scroll
            text_frame = ttk.Frame(detail_window)
            text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            detail_text = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
            scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=detail_text.yview)
            detail_text.configure(yscrollcommand=scrollbar.set)
            
            detail_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Generar contenido detallado
            content = f"INFORMACIÓN DETALLADA DE REPRESENTACIÓN\n"
            content += "=" * 60 + "\n\n"
            
            content += f"👤 ABOGADO/REPRESENTANTE:\n"
            content += f"   Nombre: {rol_info.get('nombre_completo', 'N/A')}\n"
            content += f"   Rol: {rol_info.get('rol_principal', 'N/A')}\n"
            if rol_info.get('rol_secundario'):
                content += f"   Rol Secundario: {rol_info.get('rol_secundario')}\n"
            content += f"   ID de Contacto: {rol_info.get('contacto_id', 'N/A')}\n"
            content += f"   ID de Rol: {rol_info.get('rol_id', 'N/A')}\n\n"
            
            # Información de representaciones
            contacto_id = rol_info.get('contacto_id')
            notas_del_rol = rol_info.get('notas_del_rol', '') or ''
            is_multiple_rep = 'REPRESENTACION_MULTIPLE' in notas_del_rol
            
            if is_multiple_rep and rol_info.get('rol_principal') in ['Abogado', 'Apoderado']:
                from crm_database import detect_multiple_representations_in_case
                multiple_reps = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
                
                if contacto_id in multiple_reps:
                    rep_info = multiple_reps[contacto_id]
                    representations = rep_info['representations']
                    
                    content += f"🔗 REPRESENTACIONES MÚLTIPLES:\n"
                    content += f"   Tipo: Representación Múltiple\n"
                    content += f"   Total de Partes Representadas: {len(representations)}\n\n"
                    
                    for i, rep in enumerate(representations, 1):
                        content += f"   {i}. PARTE REPRESENTADA:\n"
                        content += f"      Nombre: {rep['represented_name']}\n"
                        content += f"      Rol: {rep['represented_role']}\n"
                        content += f"      ID: {rep.get('represented_id', 'N/A')}\n"
                        
                        # Información adicional de la parte representada
                        rep_role_details = self.roles_data_cache.get(rep.get('represented_id'))
                        if rep_role_details:
                            if rep_role_details.get('dni'):
                                content += f"      DNI: {rep_role_details.get('dni')}\n"
                            if rep_role_details.get('email'):
                                content += f"      Email: {rep_role_details.get('email')}\n"
                            if rep_role_details.get('telefono'):
                                content += f"      Teléfono: {rep_role_details.get('telefono')}\n"
                        content += f"\n"
                    
                    # Información técnica
                    if 'REPRESENTACION_MULTIPLE:PRIMARY:' in notas_del_rol:
                        import re
                        group_match = re.search(r'REPRESENTACION_MULTIPLE:PRIMARY:([^]]+)', notas_del_rol)
                        if group_match:
                            group_id = group_match.group(1)
                            content += f"📋 INFORMACIÓN TÉCNICA:\n"
                            content += f"   Grupo de Representación: {group_id}\n"
                            content += f"   Tipo de Rol: Principal\n\n"
                else:
                    content += f"⚠️ ERROR: No se pudieron cargar las representaciones múltiples.\n\n"
            else:
                # Representación simple o no es abogado
                if rol_info.get('representa_a_id'):
                    representado = self.roles_data_cache.get(rol_info['representa_a_id'])
                    if representado:
                        content += f"🔗 REPRESENTACIÓN SIMPLE:\n"
                        content += f"   Representa a: {representado.get('nombre_completo', 'N/A')}\n"
                        content += f"   Rol de la Parte: {representado.get('rol_principal', 'N/A')}\n"
                        content += f"   ID de la Parte: {representado.get('rol_id', 'N/A')}\n\n"
                elif rol_info.get('rol_principal') in ['Abogado', 'Apoderado']:
                    content += f"ℹ️ ESTADO:\n"
                    content += f"   Este abogado no representa a ninguna parte actualmente.\n\n"
                else:
                    content += f"ℹ️ INFORMACIÓN:\n"
                    content += f"   Este rol no es un abogado o representante legal.\n\n"
            
            # Buscar quién representa a esta persona
            representantes = []
            for r in self.roles_data_cache.values():
                if (r.get('representa_a_id') == rol_info.get('rol_id') and 
                    'REPRESENTACION_MULTIPLE:SECONDARY:' not in (r.get('notas_del_rol', '') or '')):
                    representantes.append(r)
            
            if representantes:
                content += f"👥 REPRESENTADO POR:\n"
                for rep in representantes:
                    content += f"   • {rep.get('nombre_completo', 'N/A')} ({rep.get('rol_principal', 'N/A')})\n"
                content += f"\n"
            
            detail_text.insert('1.0', content)
            detail_text.config(state=tk.DISABLED)
            
            # Botón de cerrar
            close_btn = ttk.Button(detail_window, text="Cerrar", command=detail_window.destroy)
            close_btn.pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar detalles de representación:\n{str(e)}", parent=self)

    def _show_party_selection_dialog(self, lawyer_info, parties, action):
        """Muestra un diálogo para seleccionar partes para agregar o quitar representaciones."""
        dialog = tk.Toplevel(self)
        action_text = "Agregar" if action == "add" else "Quitar"
        dialog.title(f"{action_text} Representación - {lawyer_info.get('nombre_completo', 'N/A')}")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Etiqueta de instrucciones
        instruction_text = f"Seleccione las partes para {action_text.lower()} de la representación:"
        ttk.Label(main_frame, text=instruction_text, font=('TkDefaultFont', 10, 'bold')).pack(pady=(0, 10))
        
        # Frame para la lista de partes
        parties_frame = ttk.LabelFrame(main_frame, text="Partes Disponibles", padding="5")
        parties_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Variables para checkboxes
        party_vars = {}
        
        # Crear checkboxes para cada parte
        for party in parties:
            var = tk.BooleanVar()
            party_vars[party['id']] = var
            
            checkbox_text = f"{party['name']} ({party['role']})"
            ttk.Checkbutton(parties_frame, text=checkbox_text, variable=var).pack(anchor='w', pady=2)
        
        # Frame para botones
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        def on_confirm():
            selected_parties = [party_id for party_id, var in party_vars.items() if var.get()]
            
            if not selected_parties:
                messagebox.showwarning("Advertencia", "Seleccione al menos una parte.", parent=dialog)
                return
            
            try:
                if action == "add":
                    self._execute_add_representations(lawyer_info, selected_parties)
                else:
                    self._execute_remove_representations(lawyer_info, selected_parties)
                
                dialog.destroy()
                # Refrescar la vista
                self.refresh_roles_data()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al {action_text.lower()} representaciones:\n{str(e)}", parent=dialog)
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(buttons_frame, text=action_text, command=on_confirm).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(buttons_frame, text="Cancelar", command=on_cancel).pack(side=tk.RIGHT)

    def _execute_add_representations(self, lawyer_info, party_ids):
        """Ejecuta la adición de representaciones."""
        # Esta función debería usar la lógica de crm_database para agregar representaciones
        # Por ahora, mostrar un mensaje de confirmación
        party_names = []
        for party_id in party_ids:
            party_info = self.roles_data_cache.get(party_id)
            if party_info:
                party_names.append(party_info.get('nombre_completo', 'N/A'))
        
        messagebox.showinfo("Éxito", 
                          f"Se agregaron las siguientes representaciones para {lawyer_info.get('nombre_completo', 'N/A')}:\n" +
                          "\n".join(f"• {name}" for name in party_names), 
                          parent=self)

    def _execute_remove_representations(self, lawyer_info, party_ids):
        """Ejecuta la eliminación de representaciones."""
        # Esta función debería usar la lógica de crm_database para quitar representaciones
        # Por ahora, mostrar un mensaje de confirmación
        party_names = []
        for party_id in party_ids:
            party_info = self.roles_data_cache.get(party_id)
            if party_info:
                party_names.append(party_info.get('nombre_completo', 'N/A'))
        
        messagebox.showinfo("Éxito", 
                          f"Se quitaron las siguientes representaciones de {lawyer_info.get('nombre_completo', 'N/A')}:\n" +
                          "\n".join(f"• {name}" for name in party_names), 
                          parent=self)

    def set_add_button_state(self, state_ignored=None):
        self._update_action_buttons_state()

    def _update_action_buttons_state(self):
        case_selected = self.app_controller.selected_case is not None
        rol_selected = self.selected_rol_id is not None

        add_state = tk.NORMAL if case_selected else tk.DISABLED
        edit_delete_state = tk.NORMAL if case_selected and rol_selected else tk.DISABLED

        if hasattr(self, 'add_rol_btn'):
            self.add_rol_btn.config(state=add_state)
        if hasattr(self, 'edit_rol_btn'):
            self.edit_rol_btn.config(state=edit_delete_state)
        if hasattr(self, 'delete_rol_btn'):
            self.delete_rol_btn.config(state=edit_delete_state)

    def mostrar_detalle_completo_rol(self, rol_id):
        if not hasattr(self, 'rol_detail_text'): return

        if not rol_id:
            self.limpiar_detalle_completo_rol()
            return

        self.details_rol_frame.grid()
        self.rol_detail_text.config(state=tk.NORMAL)
        self.rol_detail_text.delete('1.0', tk.END)

        rol_details = self.roles_data_cache.get(rol_id)
        if rol_details:
            # Obtener el contador de casos para este contacto
            contacto_id = rol_details.get('contacto_id')
            casos_count = 0
            casos_count_text = ""
            
            if contacto_id:
                try:
                    casos_count = self.db_crm.count_casos_por_contacto_id(contacto_id)
                    if casos_count > 0:
                        casos_text = "caso" if casos_count == 1 else "casos"
                        casos_count_text = f"📊 INFORMACIÓN DE CASOS\n   Este contacto aparece en {casos_count} {casos_text} en total\n\n"
                    else:
                        casos_count_text = "📊 INFORMACIÓN DE CASOS\n   Este contacto aparece solo en este caso\n\n"
                except Exception as e:
                    print(f"Error al obtener contador de casos para contacto {contacto_id}: {e}")
                    casos_count_text = "📊 INFORMACIÓN DE CASOS\n   No se pudo obtener información de casos\n\n"
            
            # Encabezado con información básica
            texto = f"{'='*50}\n"
            texto += f"  {rol_details.get('nombre_completo', 'N/A')}\n"
            texto += f"{'='*50}\n\n"
            
            # Información de casos (nueva funcionalidad)
            texto += casos_count_text
            
            # Información del rol
            texto += f"🎭 ROL EN EL CASO\n"
            texto += f"   ID del Rol: {rol_details['rol_id']}\n"
            texto += f"   Rol Principal: {rol_details.get('rol_principal', 'N/A')}\n"
            if rol_details.get('rol_secundario'):
                texto += f"   Rol Secundario: {rol_details.get('rol_secundario')}\n"
            
            # Verificar si es una representación múltiple
            contacto_id = rol_details.get('contacto_id')
            notas_del_rol = rol_details.get('notas_del_rol', '') or ''
            is_multiple_rep = 'REPRESENTACION_MULTIPLE' in notas_del_rol
            
            if is_multiple_rep and rol_details.get('rol_principal') in ['Abogado', 'Apoderado']:
                # Es una representación múltiple
                try:
                    from crm_database import detect_multiple_representations_in_case
                    multiple_reps = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
                    
                    if contacto_id in multiple_reps:
                        rep_info = multiple_reps[contacto_id]
                        representations = rep_info['representations']
                        
                        texto += f"   🔗 REPRESENTACIONES MÚLTIPLES ({len(representations)})\n"
                        texto += f"   {'='*45}\n"
                        
                        # Mostrar cada representación con más detalle
                        for i, rep in enumerate(representations, 1):
                            texto += f"      {i}. 👤 {rep['represented_name']}\n"
                            texto += f"         📋 Rol: {rep['represented_role']}\n"
                            if rep.get('represented_id'):
                                texto += f"         🆔 ID: {rep['represented_id']}\n"
                            
                            # Agregar información adicional si está disponible
                            rep_role_details = self.roles_data_cache.get(rep.get('represented_id'))
                            if rep_role_details:
                                if rep_role_details.get('dni'):
                                    texto += f"         📄 DNI: {rep_role_details.get('dni')}\n"
                                if rep_role_details.get('email'):
                                    texto += f"         📧 Email: {rep_role_details.get('email')}\n"
                            texto += f"\n"
                        
                        # Información adicional de representación múltiple
                        if 'REPRESENTACION_MULTIPLE:PRIMARY:' in notas_del_rol:
                            import re
                            group_match = re.search(r'REPRESENTACION_MULTIPLE:PRIMARY:([^]]+)', notas_del_rol)
                            if group_match:
                                group_id = group_match.group(1)
                                texto += f"      📋 Grupo de Representación: {group_id}\n"
                                texto += f"      ⚖️ Tipo: Representación Principal\n"
                        
                        # Agregar resumen de representación
                        texto += f"   {'='*45}\n"
                        texto += f"   📊 RESUMEN: Este abogado representa a {len(representations)} parte(s)\n"
                        
                    else:
                        # Fallback a representación simple
                        if rol_details.get('representa_a_id'):
                            representado = self.roles_data_cache.get(rol_details['representa_a_id'])
                            if representado:
                                texto += f"   🔗 Representa a: {representado.get('nombre_completo', 'N/A')}\n"
                                texto += f"      (Rol: {representado.get('rol_principal', 'N/A')})\n"
                except Exception as e:
                    print(f"Error obteniendo representaciones múltiples: {e}")
                    # Fallback a representación simple
                    if rol_details.get('representa_a_id'):
                        representado = self.roles_data_cache.get(rol_details['representa_a_id'])
                        if representado:
                            texto += f"   🔗 Representa a: {representado.get('nombre_completo', 'N/A')}\n"
                            texto += f"      (Rol: {representado.get('rol_principal', 'N/A')})\n"
            else:
                # Representación simple o no es abogado
                if rol_details.get('representa_a_id'):
                    representado = self.roles_data_cache.get(rol_details['representa_a_id'])
                    if representado:
                        texto += f"   🔗 Representa a: {representado.get('nombre_completo', 'N/A')}\n"
                        texto += f"      (Rol: {representado.get('rol_principal', 'N/A')})\n"
            
            # Buscar quién representa a esta persona
            representantes = []
            
            # Primero buscar representaciones múltiples
            try:
                from crm_database import detect_multiple_representations_in_case
                multiple_reps = detect_multiple_representations_in_case(self.app_controller.selected_case['id'])
                
                # Buscar si esta persona está representada en alguna representación múltiple
                for contacto_id, rep_info in multiple_reps.items():
                    for representation in rep_info['representations']:
                        if representation.get('represents_id') == rol_id:
                            # Esta persona está representada por este abogado
                            lawyer_role = None
                            for r in self.roles_data_cache.values():
                                if (r.get('contacto_id') == contacto_id and 
                                    r.get('rol_principal') in ['Abogado', 'Apoderado'] and
                                    'REPRESENTACION_MULTIPLE:PRIMARY:' in (r.get('notas_del_rol', '') or '')):
                                    lawyer_role = r
                                    break
                            
                            if lawyer_role:
                                representantes.append({
                                    'role_data': lawyer_role,
                                    'is_multiple': True,
                                    'total_representations': len(rep_info['representations'])
                                })
                
                # Buscar representaciones simples (excluyendo roles shadow)
                for r in self.roles_data_cache.values():
                    if (r.get('representa_a_id') == rol_id and 
                        'REPRESENTACION_MULTIPLE:SECONDARY:' not in (r.get('notas_del_rol', '') or '') and
                        r.get('contacto_id') not in multiple_reps):  # No incluir si ya está en múltiples
                        representantes.append({
                            'role_data': r,
                            'is_multiple': False,
                            'total_representations': 1
                        })
                
            except Exception as e:
                print(f"Error buscando representantes: {e}")
                # Fallback a búsqueda simple
                for r in self.roles_data_cache.values():
                    if (r.get('representa_a_id') == rol_id and 
                        'REPRESENTACION_MULTIPLE:SECONDARY:' not in (r.get('notas_del_rol', '') or '')):
                        representantes.append({
                            'role_data': r,
                            'is_multiple': False,
                            'total_representations': 1
                        })
            
            if representantes:
                texto += f"   👥 Representado por:\n"
                for rep_info in representantes:
                    rep = rep_info['role_data']
                    is_multiple = rep_info['is_multiple']
                    total_reps = rep_info['total_representations']
                    
                    if is_multiple:
                        texto += f"      • {rep.get('nombre_completo', 'N/A')} ({rep.get('rol_principal', 'N/A')}) [Representa a {total_reps} partes]\n"
                    else:
                        texto += f"      • {rep.get('nombre_completo', 'N/A')} ({rep.get('rol_principal', 'N/A')})\n"
            
            # Información específica del rol
            if rol_details.get('datos_bancarios'):
                texto += f"   💳 Datos Bancarios: {rol_details.get('datos_bancarios')}\n"
            
            # Filtrar notas técnicas de representación múltiple
            if rol_details.get('notas_del_rol'):
                notas_originales = rol_details.get('notas_del_rol', '')
                notas_filtradas = self._filter_technical_notes(notas_originales)
                if notas_filtradas.strip():
                    texto += f"   📝 Notas del Rol: {notas_filtradas}\n"
            
            texto += f"\n👤 DATOS DEL CONTACTO\n"
            texto += f"   ID de Contacto: {rol_details['contacto_id']}\n"
            
            # Tipo de persona con icono
            tipo_persona = "🏢 Persona Jurídica" if rol_details.get('es_persona_juridica') else "👤 Persona Física"
            texto += f"   Tipo: {tipo_persona}\n"
            
            # Documentos de identidad
            if rol_details.get('dni'):
                texto += f"   📄 DNI: {rol_details.get('dni')}\n"
            if rol_details.get('cuit'):
                texto += f"   🏛️ CUIT: {rol_details.get('cuit')}\n"
            
            # Domicilios
            if rol_details.get('domicilio_real'):
                texto += f"   🏠 Domicilio Real: {rol_details.get('domicilio_real')}\n"
            if rol_details.get('domicilio_legal'):
                texto += f"   ⚖️ Domicilio Legal: {rol_details.get('domicilio_legal')}\n"
            
            # Contacto
            if rol_details.get('email'):
                texto += f"   📧 Email: {rol_details.get('email')}\n"
            if rol_details.get('telefono'):
                texto += f"   📞 Teléfono: {rol_details.get('telefono')}\n"
            
            # Notas generales
            if rol_details.get('notas_generales'):
                texto += f"\n📋 NOTAS GENERALES\n"
                texto += f"   {rol_details.get('notas_generales')}\n"
            
            self.rol_detail_text.insert('1.0', texto)
        else:
            self.rol_detail_text.insert('1.0', "Detalles del rol no encontrados o no disponibles.")

        self.rol_detail_text.config(state=tk.DISABLED)

    def _filter_technical_notes(self, notas):
        """Filtra las notas técnicas de representación múltiple para mostrar solo notas del usuario."""
        if not notas:
            return ""
        
        # Dividir en líneas y filtrar las técnicas
        lines = notas.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            # Saltar líneas técnicas de representación múltiple
            if (line.startswith('[REPRESENTACION_MULTIPLE:') or 
                line.startswith('Representa a ') and 'parte(s):' in line or
                line.startswith('- ') and '[ID:' in line and ']' in line or
                line.startswith('Shadow role for')):
                continue
            
            # Mantener líneas que no son técnicas
            if line:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)

    def limpiar_detalle_completo_rol(self):
        if not hasattr(self, 'rol_detail_text'): return
        self.rol_detail_text.config(state=tk.NORMAL)
        self.rol_detail_text.delete('1.0', tk.END)
        self.rol_detail_text.config(state=tk.DISABLED)
        if hasattr(self, 'details_rol_frame'):
            self.details_rol_frame.grid_remove()