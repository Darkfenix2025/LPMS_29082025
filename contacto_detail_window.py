# contacto_detail_window.py
import tkinter as tk
from tkinter import ttk, messagebox

class ContactoDetailWindow(tk.Toplevel):
    """
    Ventana de detalle completo de un contacto que muestra:
    - Información personal/empresarial del contacto
    - Lista de todos los casos en los que participa con sus roles
    """
    
    def __init__(self, parent, app_controller, contacto_id):
        super().__init__(parent)
        
        self.app_controller = app_controller
        self.db_crm = app_controller.db_crm
        self.contacto_id = contacto_id
        self.contacto_data = None
        self.casos_data = []
        
        # Configuración básica de la ventana
        self._setup_window()
        
        # Crear la interfaz
        self._create_widgets()
        
        # Cargar los datos
        self._load_data()
        
        # Centrar la ventana
        self._center_window()
        
        # Hacer la ventana modal (opcional)
        self.transient(parent)
        self.grab_set()
        
        # Foco en la ventana
        self.focus_set()
    
    def _setup_window(self):
        """Configura las propiedades básicas de la ventana."""
        self.title("Ficha Completa de Contacto")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Configurar el grid principal
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)  # La sección de casos será expandible
        
        # Configurar el protocolo de cierre
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # === SECCIÓN SUPERIOR: INFORMACIÓN DEL CONTACTO ===
        self.info_frame = ttk.LabelFrame(self, text="Información del Contacto", padding="10")
        self.info_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        self.info_frame.columnconfigure(1, weight=1)
        
        # Crear campos de información del contacto
        self._create_contact_info_fields()
        
        # === SECCIÓN MEDIA: INFORMACIÓN DE REPRESENTACIONES ===
        self.representations_frame = ttk.LabelFrame(self, text="Información de Representaciones", padding="10")
        self.representations_frame.grid(row=1, column=0, sticky='ew', padx=10, pady=5)
        self.representations_frame.columnconfigure(0, weight=1)
        
        # Crear área de texto para representaciones
        self._create_representations_display()
        
        # === SECCIÓN INFERIOR: CASOS Y ROLES ===
        self.casos_frame = ttk.LabelFrame(self, text="Casos en los que Participa", padding="10")
        self.casos_frame.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)
        self.casos_frame.columnconfigure(0, weight=1)
        self.casos_frame.rowconfigure(0, weight=1)
        
        # Crear TreeView para los casos
        self._create_casos_treeview()
        
        # === SECCIÓN INFERIOR: BOTONES ===
        self.buttons_frame = ttk.Frame(self)
        self.buttons_frame.grid(row=3, column=0, sticky='ew', padx=10, pady=(5, 10))
        
        # Botón Cerrar
        self.close_btn = ttk.Button(self.buttons_frame, text="Cerrar", command=self._on_close)
        self.close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Botón Actualizar (opcional)
        self.refresh_btn = ttk.Button(self.buttons_frame, text="Actualizar", command=self._refresh_data)
        self.refresh_btn.pack(side=tk.RIGHT, padx=5)
    
    def _create_contact_info_fields(self):
        """Crea los campos de información del contacto."""
        row = 0
        
        # Nombre completo
        ttk.Label(self.info_frame, text="Nombre Completo:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.nombre_label = ttk.Label(self.info_frame, text="Cargando...", foreground='blue')
        self.nombre_label.grid(row=row, column=1, sticky='w', pady=2)
        row += 1
        
        # Tipo de persona
        ttk.Label(self.info_frame, text="Tipo:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.tipo_label = ttk.Label(self.info_frame, text="Cargando...")
        self.tipo_label.grid(row=row, column=1, sticky='w', pady=2)
        row += 1
        
        # DNI
        ttk.Label(self.info_frame, text="DNI:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.dni_label = ttk.Label(self.info_frame, text="Cargando...")
        self.dni_label.grid(row=row, column=1, sticky='w', pady=2)
        row += 1
        
        # CUIT
        ttk.Label(self.info_frame, text="CUIT:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.cuit_label = ttk.Label(self.info_frame, text="Cargando...")
        self.cuit_label.grid(row=row, column=1, sticky='w', pady=2)
        row += 1
        
        # Domicilio Real
        ttk.Label(self.info_frame, text="Domicilio Real:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.domicilio_real_label = ttk.Label(self.info_frame, text="Cargando...")
        self.domicilio_real_label.grid(row=row, column=1, sticky='w', pady=2)
        row += 1
        
        # Domicilio Legal
        ttk.Label(self.info_frame, text="Domicilio Legal:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.domicilio_legal_label = ttk.Label(self.info_frame, text="Cargando...")
        self.domicilio_legal_label.grid(row=row, column=1, sticky='w', pady=2)
        row += 1
        
        # Email
        ttk.Label(self.info_frame, text="Email:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.email_label = ttk.Label(self.info_frame, text="Cargando...")
        self.email_label.grid(row=row, column=1, sticky='w', pady=2)
        row += 1
        
        # Teléfono
        ttk.Label(self.info_frame, text="Teléfono:", font=('TkDefaultFont', 9, 'bold')).grid(
            row=row, column=0, sticky='w', padx=(0, 10), pady=2)
        self.telefono_label = ttk.Label(self.info_frame, text="Cargando...")
        self.telefono_label.grid(row=row, column=1, sticky='w', pady=2)
    
    def _create_representations_display(self):
        """Crea el área de visualización de representaciones múltiples."""
        # Crear área de texto con scroll para representaciones
        self.representations_text = tk.Text(self.representations_frame, height=6, wrap=tk.WORD, 
                                          font=('Consolas', 9), state=tk.DISABLED)
        
        # Scrollbar para el texto de representaciones
        rep_scrollbar = ttk.Scrollbar(self.representations_frame, orient=tk.VERTICAL, 
                                    command=self.representations_text.yview)
        self.representations_text.configure(yscrollcommand=rep_scrollbar.set)
        
        # Posicionar widgets
        self.representations_text.grid(row=0, column=0, sticky='nsew', padx=(0, 5))
        rep_scrollbar.grid(row=0, column=1, sticky='ns')
        
        # Configurar grid
        self.representations_frame.rowconfigure(0, weight=1)
        self.representations_frame.columnconfigure(0, weight=1)
    
    def _create_casos_treeview(self):
        """Crea el TreeView para mostrar los casos."""
        
        # Definir columnas
        columns = ('caso_id', 'caratula', 'numero_expediente', 'rol_principal', 'rol_secundario')
        
        self.casos_tree = ttk.Treeview(self.casos_frame, columns=columns, show='headings', selectmode='browse')
        
        # Configurar encabezados
        self.casos_tree.heading('caso_id', text='ID Caso')
        self.casos_tree.heading('caratula', text='Carátula')
        self.casos_tree.heading('numero_expediente', text='Nº Expediente')
        self.casos_tree.heading('rol_principal', text='Rol Principal')
        self.casos_tree.heading('rol_secundario', text='Rol Secundario')
        
        # Configurar anchos de columna
        self.casos_tree.column('caso_id', width=60, stretch=tk.NO, anchor=tk.CENTER)
        self.casos_tree.column('caratula', width=300, stretch=True)
        self.casos_tree.column('numero_expediente', width=120, stretch=tk.NO)
        self.casos_tree.column('rol_principal', width=100, stretch=tk.NO)
        self.casos_tree.column('rol_secundario', width=100, stretch=tk.NO)
        
        # Scrollbars
        casos_scrollbar_y = ttk.Scrollbar(self.casos_frame, orient=tk.VERTICAL, command=self.casos_tree.yview)
        self.casos_tree.configure(yscrollcommand=casos_scrollbar_y.set)
        casos_scrollbar_y.grid(row=0, column=1, sticky='ns')
        
        casos_scrollbar_x = ttk.Scrollbar(self.casos_frame, orient=tk.HORIZONTAL, command=self.casos_tree.xview)
        self.casos_tree.configure(xscrollcommand=casos_scrollbar_x.set)
        casos_scrollbar_x.grid(row=1, column=0, sticky='ew')
        
        # Posicionar TreeView
        self.casos_tree.grid(row=0, column=0, sticky='nsew')
        
        # Configurar estilos
        self.casos_tree.tag_configure('even', background='#f0f0f0')
        self.casos_tree.tag_configure('odd', background='white')
    
    def _load_data(self):
        """Carga todos los datos del contacto y sus casos."""
        try:
            # Mostrar indicador de carga
            self._show_loading_state()
            
            # Cargar información del contacto
            self._load_contact_info()
            
            # Cargar información de representaciones
            self._load_representations_data()
            
            # Cargar casos y roles
            self._load_casos_data()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar los datos del contacto:\n{str(e)}", parent=self)
            print(f"Error en _load_data: {e}")
            # Mostrar estado de error
            self._show_error_state(str(e))
    
    def _load_contact_info(self):
        """Carga la información básica del contacto."""
        try:
            self.contacto_data = self.db_crm.get_contacto_by_id(self.contacto_id)
            
            if not self.contacto_data:
                raise Exception(f"No se encontró el contacto con ID {self.contacto_id}")
            
            # Actualizar los labels con la información
            self._update_contact_info_display()
            
        except Exception as e:
            # Mostrar error en los campos
            self._show_contact_info_error(str(e))
            raise
    
    def _update_contact_info_display(self):
        """Actualiza la visualización de la información del contacto."""
        if not self.contacto_data:
            return
        
        # Nombre completo
        nombre = self.contacto_data.get('nombre_completo', 'N/A')
        self.nombre_label.config(text=nombre)
        
        # Actualizar título de la ventana
        self.title(f"Ficha Completa - {nombre}")
        
        # Tipo de persona
        es_juridica = self.contacto_data.get('es_persona_juridica', False)
        tipo_text = "🏢 Persona Jurídica" if es_juridica else "👤 Persona Física"
        self.tipo_label.config(text=tipo_text)
        
        # DNI
        dni = self.contacto_data.get('dni', '')
        self.dni_label.config(text=dni if dni else 'No especificado')
        
        # CUIT
        cuit = self.contacto_data.get('cuit', '')
        self.cuit_label.config(text=cuit if cuit else 'No especificado')
        
        # Domicilio Real
        dom_real = self.contacto_data.get('domicilio_real', '')
        self.domicilio_real_label.config(text=dom_real if dom_real else 'No especificado')
        
        # Domicilio Legal
        dom_legal = self.contacto_data.get('domicilio_legal', '')
        self.domicilio_legal_label.config(text=dom_legal if dom_legal else 'No especificado')
        
        # Email
        email = self.contacto_data.get('email', '')
        self.email_label.config(text=email if email else 'No especificado')
        
        # Teléfono
        telefono = self.contacto_data.get('telefono', '')
        self.telefono_label.config(text=telefono if telefono else 'No especificado')
    
    def _show_contact_info_error(self, error_msg):
        """Muestra error en los campos de información del contacto."""
        error_text = f"Error: {error_msg}"
        
        self.nombre_label.config(text=error_text, foreground='red')
        self.tipo_label.config(text="Error al cargar", foreground='red')
        self.dni_label.config(text="Error al cargar", foreground='red')
        self.cuit_label.config(text="Error al cargar", foreground='red')
        self.domicilio_real_label.config(text="Error al cargar", foreground='red')
        self.domicilio_legal_label.config(text="Error al cargar", foreground='red')
        self.email_label.config(text="Error al cargar", foreground='red')
        self.telefono_label.config(text="Error al cargar", foreground='red')
    
    def _load_representations_data(self):
        """Carga y muestra la información de representaciones múltiples."""
        try:
            # Habilitar edición del texto
            self.representations_text.config(state=tk.NORMAL)
            self.representations_text.delete('1.0', tk.END)
            
            # Obtener todos los casos del contacto para analizar representaciones
            if not self.casos_data:
                self.representations_text.insert('1.0', "No hay información de representaciones disponible.")
                self.representations_text.config(state=tk.DISABLED)
                return
            
            content = ""
            has_representations = False
            
            # Analizar cada caso para encontrar representaciones
            for caso in self.casos_data:
                caso_id = caso.get('caso_id')
                rol_principal = caso.get('rol_principal', '')
                
                if rol_principal in ['Abogado', 'Apoderado']:
                    # Es un abogado, verificar representaciones
                    try:
                        from crm_database import detect_multiple_representations_in_case
                        multiple_reps = detect_multiple_representations_in_case(caso_id)
                        
                        if self.contacto_id in multiple_reps:
                            # Tiene representaciones múltiples
                            rep_info = multiple_reps[self.contacto_id]
                            representations = rep_info['representations']
                            
                            if not has_representations:
                                content += "🔗 REPRESENTACIONES MÚLTIPLES:\n"
                                content += "=" * 50 + "\n\n"
                                has_representations = True
                            
                            content += f"📋 Caso: {caso.get('caratula', 'N/A')[:40]}...\n"
                            content += f"   ID: {caso_id} | Expediente: {caso.get('numero_expediente', 'N/A')}\n"
                            content += f"   Representa a {len(representations)} parte(s):\n"
                            
                            for i, rep in enumerate(representations, 1):
                                content += f"   {i}. {rep['represented_name']} ({rep['represented_role']})\n"
                            content += "\n"
                        
                        elif caso.get('representa_a_id'):
                            # Representación simple
                            if not has_representations:
                                content += "🔗 REPRESENTACIONES SIMPLES:\n"
                                content += "=" * 50 + "\n\n"
                                has_representations = True
                            
                            # Buscar información del representado
                            representado_info = None
                            try:
                                representado_info = self.db_crm.get_rol_by_id(caso['representa_a_id'])
                            except:
                                pass
                            
                            content += f"📋 Caso: {caso.get('caratula', 'N/A')[:40]}...\n"
                            content += f"   ID: {caso_id} | Expediente: {caso.get('numero_expediente', 'N/A')}\n"
                            if representado_info:
                                content += f"   Representa a: {representado_info.get('nombre_completo', 'N/A')}\n"
                                content += f"   Rol: {representado_info.get('rol_principal', 'N/A')}\n"
                            else:
                                content += f"   Representa a: ID {caso['representa_a_id']}\n"
                            content += "\n"
                    
                    except Exception as e:
                        print(f"Error analizando representaciones para caso {caso_id}: {e}")
                        continue
                
                elif rol_principal in ['Actor', 'Demandado', 'Tercero']:
                    # Es una parte, verificar si está representada
                    try:
                        # Buscar abogados que representen a esta parte en este caso
                        representantes = []
                        for otro_caso in self.casos_data:
                            if (otro_caso.get('caso_id') == caso_id and 
                                otro_caso.get('rol_principal') in ['Abogado', 'Apoderado'] and
                                otro_caso.get('representa_a_id') == caso.get('rol_id')):
                                representantes.append(otro_caso)
                        
                        if representantes and not has_representations:
                            content += "👥 REPRESENTADO POR:\n"
                            content += "=" * 50 + "\n\n"
                            has_representations = True
                        
                        for rep in representantes:
                            content += f"📋 Caso: {caso.get('caratula', 'N/A')[:40]}...\n"
                            content += f"   Representado por: {rep.get('nombre_completo', 'N/A')}\n"
                            content += f"   Tipo: {rep.get('rol_principal', 'N/A')}\n\n"
                    
                    except Exception as e:
                        print(f"Error analizando representantes para caso {caso_id}: {e}")
                        continue
            
            if not has_representations:
                content = "ℹ️ Este contacto no tiene representaciones activas o no actúa como representante legal."
            
            self.representations_text.insert('1.0', content)
            self.representations_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.representations_text.config(state=tk.NORMAL)
            self.representations_text.delete('1.0', tk.END)
            self.representations_text.insert('1.0', f"❌ Error al cargar información de representaciones:\n{str(e)}")
            self.representations_text.config(state=tk.DISABLED)
            print(f"Error en _load_representations_data: {e}")
    
    def _load_casos_data(self):
        """Carga los casos y roles del contacto."""
        try:
            self.casos_data = self.db_crm.get_casos_y_roles_por_contacto_id(self.contacto_id)
            
            # Actualizar el TreeView
            self._update_casos_display()
            
        except Exception as e:
            self._show_casos_error(str(e))
            raise
    
    def _update_casos_display(self):
        """Actualiza la visualización de los casos en el TreeView."""
        # Limpiar TreeView
        for item in self.casos_tree.get_children():
            self.casos_tree.delete(item)
        
        if not self.casos_data:
            # Mostrar mensaje de "sin casos"
            self.casos_tree.insert('', tk.END, values=('', 'No hay casos registrados para este contacto', '', '', ''), 
                                 tags=('info',))
            self.casos_tree.tag_configure('info', foreground='gray', font=('TkDefaultFont', 9, 'italic'))
            return
        
        # Actualizar el título del frame con el conteo
        casos_count = len(self.casos_data)
        casos_text = "caso" if casos_count == 1 else "casos"
        self.casos_frame.config(text=f"Casos en los que Participa ({casos_count} {casos_text})")
        
        # Insertar casos con información de representaciones múltiples
        for i, caso in enumerate(self.casos_data):
            # Alternar colores de fila
            tag = 'even' if i % 2 == 0 else 'odd'
            
            # Verificar si tiene representaciones múltiples en este caso
            rol_info = ""
            if caso.get('rol_principal') in ['Abogado', 'Apoderado']:
                try:
                    # Verificar representaciones múltiples
                    notas_del_rol = caso.get('notas_del_rol', '') or ''
                    if 'REPRESENTACION_MULTIPLE' in notas_del_rol:
                        # Intentar obtener información de representaciones múltiples
                        from crm_database import detect_multiple_representations_in_case
                        multiple_reps = detect_multiple_representations_in_case(caso.get('caso_id'))
                        
                        if self.contacto_id in multiple_reps:
                            rep_count = len(multiple_reps[self.contacto_id]['representations'])
                            rol_info = f"{caso.get('rol_principal', 'N/A')} (Representa {rep_count} partes)"
                        else:
                            rol_info = caso.get('rol_principal', 'N/A')
                    else:
                        rol_info = caso.get('rol_principal', 'N/A')
                except:
                    rol_info = caso.get('rol_principal', 'N/A')
            else:
                rol_info = caso.get('rol_principal', 'N/A')
            
            values = (
                caso.get('caso_id', ''),
                caso.get('caratula', 'N/A')[:60] + ('...' if len(caso.get('caratula', '')) > 60 else ''),
                caso.get('numero_expediente', 'N/A'),
                rol_info,
                caso.get('rol_secundario', '') or 'N/A'
            )
            
            # Agregar tag especial para representaciones múltiples
            if 'Representa' in rol_info and 'partes' in rol_info:
                tag = f"{tag}_multiple"
                self.casos_tree.tag_configure(f"{tag}", background='#e6f3ff' if 'even' in tag else '#f0f8ff', 
                                            foreground='#0066cc')
            
            self.casos_tree.insert('', tk.END, values=values, tags=(tag,))
    
    def _show_casos_error(self, error_msg):
        """Muestra error en el TreeView de casos."""
        # Limpiar TreeView
        for item in self.casos_tree.get_children():
            self.casos_tree.delete(item)
        
        # Mostrar mensaje de error
        self.casos_tree.insert('', tk.END, values=('', f'❌ Error al cargar casos: {error_msg}', '', '', ''), 
                             tags=('error',))
        self.casos_tree.tag_configure('error', foreground='red', font=('TkDefaultFont', 9, 'italic'))
    
    def _refresh_data(self):
        """Actualiza todos los datos de la ventana."""
        try:
            # Mostrar indicador de carga
            self.nombre_label.config(text="Actualizando...", foreground='blue')
            self.update()
            
            # Recargar datos
            self._load_data()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al actualizar los datos:\n{str(e)}", parent=self)
    
    def _center_window(self):
        """Centra la ventana en la pantalla."""
        self.update_idletasks()
        
        # Obtener dimensiones de la ventana
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        
        # Obtener dimensiones de la pantalla
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # Calcular posición centrada
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Aplicar posición
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def _show_loading_state(self):
        """Muestra indicadores de carga en la interfaz."""
        loading_text = "Cargando..."
        loading_color = "blue"
        
        # Actualizar campos de contacto
        self.nombre_label.config(text=loading_text, foreground=loading_color)
        self.tipo_label.config(text=loading_text, foreground=loading_color)
        self.dni_label.config(text=loading_text, foreground=loading_color)
        self.cuit_label.config(text=loading_text, foreground=loading_color)
        self.domicilio_real_label.config(text=loading_text, foreground=loading_color)
        self.domicilio_legal_label.config(text=loading_text, foreground=loading_color)
        self.email_label.config(text=loading_text, foreground=loading_color)
        self.telefono_label.config(text=loading_text, foreground=loading_color)
        
        # Limpiar TreeView y mostrar mensaje de carga
        for item in self.casos_tree.get_children():
            self.casos_tree.delete(item)
        self.casos_tree.insert('', tk.END, values=('', 'Cargando casos...', '', '', ''), 
                             tags=('loading',))
        self.casos_tree.tag_configure('loading', foreground='blue', font=('TkDefaultFont', 9, 'italic'))
        
        # Forzar actualización de la interfaz
        self.update()
    
    def _show_error_state(self, error_msg):
        """Muestra estado de error en la interfaz."""
        self._show_contact_info_error(error_msg)
        self._show_casos_error(error_msg)
    
    def _on_close(self):
        """Maneja el cierre de la ventana."""
        try:
            # Liberar el grab
            self.grab_release()
            
            # Destruir la ventana
            self.destroy()
            
        except Exception as e:
            print(f"Error al cerrar ContactoDetailWindow: {e}")
            # Forzar destrucción en caso de error
            try:
                self.destroy()
            except:
                pass