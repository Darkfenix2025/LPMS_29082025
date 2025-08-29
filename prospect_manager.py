"""
Prospect Manager - Gestor de Prospectos para el CRM Legal
Maneja toda la lógica relacionada con la gestión de prospectos y su interfaz
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import crm_database as db
import datetime
import date_utils
from prospect_service import ProspectService


class ProspectManager:
    """Clase que maneja toda la lógica de prospectos"""

    def __init__(self, app_controller):
        self.app_controller = app_controller
        self.db = db
        self.selected_prospect = None
        
        # Crear servicio de prospectos para lógica de negocio
        self.prospect_service = ProspectService()

    def validar_datos_prospecto(self, datos: dict) -> tuple[bool, str]:
        """
        Valida los datos de un prospecto antes de guardar.
        
        Args:
            datos (dict): Diccionario con los datos del prospecto
            
        Returns:
            tuple[bool, str]: (es_valido, mensaje_error)
        """
        # Validar nombre obligatorio
        nombre = datos.get('nombre', '').strip()
        if not nombre:
            return False, "El nombre del prospecto no puede estar vacío."
        
        # Validar longitud del nombre
        if len(nombre) > 255:
            return False, "El nombre del prospecto es demasiado largo (máximo 255 caracteres)."
        
        # Validar contacto si se proporciona
        contacto = datos.get('contacto', '').strip()
        if contacto and len(contacto) > 255:
            return False, "La información de contacto es demasiado larga (máximo 255 caracteres)."
        
        # Validar notas generales si se proporcionan
        notas_generales = datos.get('notas_generales', '').strip()
        if notas_generales and len(notas_generales) > 2000:
            return False, "Las notas generales son demasiado largas (máximo 2000 caracteres)."
        
        # Validar estado si se proporciona
        estado = datos.get('estado', '')
        estados_validos = ["Consulta Inicial", "En Análisis", "Convertido", "Desestimado"]
        if estado and estado not in estados_validos:
            return False, f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
        
        return True, ""

    # ========================================
    # GRUPO 1: FUNCIONES CRUD PRINCIPALES
    # ========================================

    def cargar_prospectos(self):
        """Carga la lista de prospectos en el TreeView"""
        # Limpiar lista actual
        for i in self.app_controller.prospect_tree.get_children():
            self.app_controller.prospect_tree.delete(i)

        # Usar el servicio para obtener prospectos
        prospects = self.prospect_service.obtener_todos_los_prospectos()
        for prospect in prospects:
            # Formatear fecha para mostrar usando utilidades argentinas
            fecha_str = self.prospect_service.formatear_fecha_para_mostrar(
                prospect.get("fecha_primera_consulta")
            )

            # Insertar en el TreeView (adaptado para la nueva ventana con 4 columnas)
            if hasattr(self.app_controller, "window"):  # Es la ventana de prospectos
                values = (
                    prospect["id"],
                    prospect["nombre"],
                    prospect["estado"],
                    fecha_str,
                )
            else:  # Es la ventana principal (compatibilidad)
                values = (prospect["id"], prospect["nombre"], prospect["estado"])

            self.app_controller.prospect_tree.insert(
                "", tk.END, values=values, iid=str(prospect["id"])
            )

        # Limpiar selección y detalles
        self.selected_prospect = None
        if hasattr(self.app_controller, "clear_selection"):
            self.app_controller.clear_selection()
        else:
            self.limpiar_detalles_prospecto()
            self.deshabilitar_botones_prospecto()

    def al_seleccionar_prospecto(self, event):
        """Maneja la selección de un prospecto en el TreeView"""
        selected_items = self.app_controller.prospect_tree.selection()
        if selected_items:
            try:
                prospect_id = int(selected_items[0])
                prospect_data = self.prospect_service.obtener_prospecto(prospect_id)
                if prospect_data:
                    self.selected_prospect = prospect_data
                    self.mostrar_detalles_prospecto(prospect_data)
                    self.habilitar_botones_prospecto()
                else:
                    print(f"Error: No se encontró prospecto con ID {prospect_id}")
                    self.selected_prospect = None
                    self.limpiar_detalles_prospecto()
                    self.deshabilitar_botones_prospecto()
            except (ValueError, IndexError) as e:
                print(f"Error seleccionando prospecto: {e}")
                self.selected_prospect = None
                self.limpiar_detalles_prospecto()
                self.deshabilitar_botones_prospecto()
        else:
            self.selected_prospect = None
            self.limpiar_detalles_prospecto()
            self.deshabilitar_botones_prospecto()

    def mostrar_detalles_prospecto(self, prospect_data):
        """Muestra los detalles del prospecto seleccionado"""
        if prospect_data:
            self.app_controller.prospect_detail_name_lbl.config(
                text=prospect_data.get("nombre", "N/A")
            )
            self.app_controller.prospect_detail_contact_lbl.config(
                text=prospect_data.get("contacto", "N/A")
            )
            self.app_controller.prospect_detail_status_lbl.config(
                text=prospect_data.get("estado", "N/A")
            )

            # Formatear fecha de primera consulta
            fecha_consulta = prospect_data.get("fecha_primera_consulta")
            if fecha_consulta:
                if isinstance(fecha_consulta, str):
                    fecha_str = fecha_consulta
                else:
                    fecha_str = date_utils.DateFormatter.to_display_format(fecha_consulta)
                self.app_controller.prospect_detail_date_lbl.config(text=fecha_str)
            else:
                self.app_controller.prospect_detail_date_lbl.config(text="N/A")

            # Mostrar información de conversión si aplica
            if prospect_data.get("estado") == "Convertido" and prospect_data.get(
                "cliente_convertido_nombre"
            ):
                conversion_text = (
                    f"Convertido a: {prospect_data['cliente_convertido_nombre']}"
                )
                if prospect_data.get("fecha_conversion"):
                    fecha_conv = prospect_data["fecha_conversion"]
                    if isinstance(fecha_conv, str):
                        fecha_conv_str = fecha_conv
                    else:
                        fecha_conv_str = date_utils.DateFormatter.to_display_format(fecha_conv)
                    conversion_text += f" ({fecha_conv_str})"
                self.app_controller.prospect_detail_conversion_lbl.config(
                    text=conversion_text
                )
            else:
                self.app_controller.prospect_detail_conversion_lbl.config(text="")
        else:
            self.limpiar_detalles_prospecto()

    def limpiar_detalles_prospecto(self):
        """Limpia los detalles del prospecto"""
        self.app_controller.prospect_detail_name_lbl.config(text="")
        self.app_controller.prospect_detail_contact_lbl.config(text="")
        self.app_controller.prospect_detail_status_lbl.config(text="")
        self.app_controller.prospect_detail_date_lbl.config(text="")
        self.app_controller.prospect_detail_conversion_lbl.config(text="")

    def habilitar_botones_prospecto(self):
        """Habilita los botones de prospecto"""
        self.app_controller.new_consultation_btn.config(state=tk.NORMAL)
        self.app_controller.view_consultation_btn.config(state=tk.NORMAL)
        self.app_controller.convert_to_client_btn.config(state=tk.NORMAL)

    def deshabilitar_botones_prospecto(self):
        """Deshabilita los botones de prospecto"""
        self.app_controller.new_consultation_btn.config(state=tk.DISABLED)
        self.app_controller.view_consultation_btn.config(state=tk.DISABLED)
        self.app_controller.convert_to_client_btn.config(state=tk.DISABLED)

    def open_new_prospect_dialog(self):
        """Abre el diálogo para agregar un nuevo prospecto"""
        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title("Agregar Nuevo Prospecto")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Variables de Tkinter
        name_var = tk.StringVar()
        contact_var = tk.StringVar()
        notes_var = tk.StringVar()

        # Layout de los widgets
        row_idx = 0
        ttk.Label(frame, text="Nombre Completo:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
        name_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Contacto:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        contact_entry = ttk.Entry(frame, textvariable=contact_var, width=40)
        contact_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Notas Generales:").grid(
            row=row_idx, column=0, sticky=tk.NW, pady=3, padx=5
        )
        notes_text = tk.Text(frame, width=40, height=4)
        notes_text.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=15)

        def save_prospect():
            nombre = name_var.get().strip()
            contacto = contact_var.get().strip()
            notas = notes_text.get("1.0", tk.END).strip()

            # Preparar datos del prospecto
            datos_prospecto = {
                'nombre': nombre,
                'contacto': contacto,
                'notas_generales': notas
            }
            
            # Usar el servicio para crear el prospecto
            success, mensaje, prospecto_id = self.prospect_service.crear_prospecto(datos_prospecto)
            
            if success:
                messagebox.showinfo(
                    "Éxito",
                    mensaje,
                    parent=self.app_controller.root,
                )
                dialog.destroy()
                self.cargar_prospectos()
            else:
                messagebox.showerror(
                    "Error", mensaje, parent=dialog
                )

        ttk.Button(button_frame, text="Guardar", command=save_prospect).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

        name_entry.focus_set()
        self.app_controller.root.wait_window(dialog)

    def open_new_consultation_dialog(self):
        """Abre el diálogo para crear una nueva consulta"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return

        # Importar aquí para evitar dependencias circulares
        from prospect_dialog_manager import ProspectDialogManager

        dialog_manager = ProspectDialogManager(self.app_controller)
        dialog_manager.open_consultation_dialog(self.selected_prospect)

    def open_view_consultation_dialog(self):
        """Abre el diálogo para ver/editar consultas existentes"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return

        # Obtener consultas del prospecto
        consultas = self.db.get_consultas_by_prospecto_id(self.selected_prospect["id"])

        if not consultas:
            # Si no hay consultas, ofrecer crear una nueva
            if messagebox.askyesno(
                "Sin Consultas",
                f"El prospecto '{self.selected_prospect['nombre']}' no tiene consultas registradas.\n\n¿Desea crear una nueva consulta?",
                parent=self.app_controller.root,
            ):
                self.open_new_consultation_dialog()
            return

        # Si hay consultas, mostrar lista para seleccionar
        self._show_consultation_list_dialog(consultas)

    def _show_consultation_list_dialog(self, consultas):
        """Muestra una ventana mejorada con lista de consultas y análisis IA"""
        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title(f"Consultas de {self.selected_prospect['nombre']} - Análisis IA")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.geometry("1000x700")
        dialog.resizable(True, True)

        # Frame principal
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid
        main_frame.columnconfigure(0, weight=4)  # Lista de consultas (40%)
        main_frame.columnconfigure(1, weight=6)  # Detalles y análisis (60%)
        main_frame.rowconfigure(0, weight=1)

        # --- Panel izquierdo: Lista de consultas ---
        left_frame = ttk.LabelFrame(main_frame, text="Lista de Consultas", padding="10")
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)

        # TreeView para consultas
        columns = ("ID", "Fecha", "Estado")
        consultation_tree = ttk.Treeview(
            left_frame, columns=columns, show="headings", selectmode="browse"
        )
        consultation_tree.heading("ID", text="ID")
        consultation_tree.heading("Fecha", text="Fecha")
        consultation_tree.heading("Estado", text="Estado IA")
        consultation_tree.column("ID", width=40, stretch=tk.NO)
        consultation_tree.column("Fecha", width=80, stretch=tk.NO)
        consultation_tree.column("Estado", width=80, stretch=tk.YES)

        # Scrollbar para TreeView
        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=consultation_tree.yview)
        consultation_tree.configure(yscrollcommand=scrollbar.set)
        
        consultation_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Botones de acción para consultas
        buttons_frame = ttk.Frame(left_frame)
        buttons_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        edit_consultation_btn = ttk.Button(
            buttons_frame, text="Editar Consulta", 
            command=lambda: self._edit_selected_consultation(consultation_tree, dialog),
            state=tk.DISABLED
        )
        edit_consultation_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_consultation_btn = ttk.Button(
            buttons_frame, text="Eliminar Consulta", 
            command=lambda: self._delete_selected_consultation(consultation_tree, dialog),
            state=tk.DISABLED
        )
        delete_consultation_btn.pack(side=tk.LEFT, padx=5)
        
        export_consultation_btn = ttk.Button(
            buttons_frame, text="Exportar a Word", 
            command=lambda: self._export_selected_consultation(consultation_tree, dialog),
            state=tk.DISABLED
        )
        export_consultation_btn.pack(side=tk.RIGHT)

        # --- Panel derecho: Detalles de la consulta ---
        right_frame = ttk.LabelFrame(main_frame, text="Detalles de la Consulta", padding="10")
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        right_frame.rowconfigure(3, weight=2)

        # Información básica
        info_frame = ttk.Frame(right_frame)
        info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        info_frame.columnconfigure(1, weight=1)
        
        ttk.Label(info_frame, text="Fecha:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        date_label = ttk.Label(info_frame, text="", font=("TkDefaultFont", 9, "bold"))
        date_label.grid(row=0, column=1, sticky="w")
        
        ttk.Label(info_frame, text="Estado IA:").grid(row=1, column=0, sticky="w", padx=(0, 10))
        status_label = ttk.Label(info_frame, text="")
        status_label.grid(row=1, column=1, sticky="w")

        # Relato original
        ttk.Label(right_frame, text="Relato Original del Cliente:").grid(row=2, column=0, sticky="w", pady=(0, 5))
        relato_text = scrolledtext.ScrolledText(right_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        relato_text.grid(row=3, column=0, sticky="nsew", pady=(0, 10))

        # Análisis de IA
        ttk.Label(right_frame, text="Análisis Legal Profesional (IA):").grid(row=4, column=0, sticky="w", pady=(0, 5))
        analisis_text = scrolledtext.ScrolledText(right_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        analisis_text.grid(row=5, column=0, sticky="nsew")

        # Llenar TreeView con consultas
        for consulta in consultas:
            fecha_str = date_utils.DateFormatter.to_display_format(consulta['fecha_consulta']) or "N/A"
            
            # Determinar estado del análisis IA
            if consulta.get('hechos_reformulados_ia') and consulta['hechos_reformulados_ia'].strip():
                estado_ia = "🟢 Con IA"
            else:
                estado_ia = "🔴 Sin IA"
            
            consultation_tree.insert("", tk.END, values=(
                consulta['id'], 
                fecha_str, 
                estado_ia
            ), iid=str(consulta['id']))

        # Función para mostrar detalles de consulta seleccionada
        def on_consultation_select(event):
            selection = consultation_tree.selection()
            if not selection:
                # Limpiar detalles
                date_label.config(text="")
                status_label.config(text="")
                relato_text.config(state=tk.NORMAL)
                relato_text.delete("1.0", tk.END)
                relato_text.config(state=tk.DISABLED)
                analisis_text.config(state=tk.NORMAL)
                analisis_text.delete("1.0", tk.END)
                analisis_text.config(state=tk.DISABLED)
                
                # Deshabilitar botones
                edit_consultation_btn.config(state=tk.DISABLED)
                delete_consultation_btn.config(state=tk.DISABLED)
                export_consultation_btn.config(state=tk.DISABLED)
                return
            
            # Obtener consulta seleccionada
            consulta_id = int(selection[0])
            consulta = next((c for c in consultas if c['id'] == consulta_id), None)
            
            if consulta:
                # Mostrar información básica
                fecha_str = date_utils.DateFormatter.to_display_format(consulta['fecha_consulta']) or "N/A"
                date_label.config(text=fecha_str)
                
                if consulta.get('hechos_reformulados_ia') and consulta['hechos_reformulados_ia'].strip():
                    status_label.config(text="🟢 Análisis IA Completo", foreground="green")
                else:
                    status_label.config(text="🔴 Sin Análisis IA", foreground="red")
                
                # Mostrar relato original
                relato_text.config(state=tk.NORMAL)
                relato_text.delete("1.0", tk.END)
                relato_original = consulta.get('relato_original_cliente', 'No registrado')
                relato_text.insert("1.0", relato_original)
                relato_text.config(state=tk.DISABLED)
                
                # Mostrar análisis IA
                analisis_text.config(state=tk.NORMAL)
                analisis_text.delete("1.0", tk.END)
                analisis_ia = consulta.get('hechos_reformulados_ia', '')
                if analisis_ia and analisis_ia.strip():
                    analisis_text.insert("1.0", analisis_ia)
                else:
                    analisis_text.insert("1.0", "No se ha generado análisis de IA para esta consulta.")
                analisis_text.config(state=tk.DISABLED)
                
                # Habilitar botones
                edit_consultation_btn.config(state=tk.NORMAL)
                delete_consultation_btn.config(state=tk.NORMAL)
                if analisis_ia and analisis_ia.strip():
                    export_consultation_btn.config(state=tk.NORMAL)
                else:
                    export_consultation_btn.config(state=tk.DISABLED)

        consultation_tree.bind("<<TreeviewSelect>>", on_consultation_select)

        # Botón cerrar
        close_frame = ttk.Frame(main_frame)
        close_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        ttk.Button(close_frame, text="Cerrar", command=dialog.destroy).pack()

        # Seleccionar primera consulta si existe
        if consultas:
            first_item = consultation_tree.get_children()[0]
            consultation_tree.selection_set(first_item)
            consultation_tree.focus(first_item)
            on_consultation_select(None)



    def convert_prospect_to_client(self):
        """Convierte un prospecto a cliente"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return

        # Verificar que el prospecto no esté ya convertido
        if self.selected_prospect.get("estado") == "Convertido":
            messagebox.showinfo(
                "Información",
                f"Este prospecto ya fue convertido al cliente: {self.selected_prospect.get('cliente_convertido_nombre', 'N/A')}",
            )
            return

        # Confirmar conversión
        if not messagebox.askyesno(
            "Confirmar Conversión",
            f"¿Está seguro de que desea convertir el prospecto '{self.selected_prospect['nombre']}' a cliente?\n\n"
            "Esta acción abrirá el diálogo de creación de cliente con los datos del prospecto pre-rellenados.",
            parent=self.app_controller.root,
        ):
            return

        # Llamar al método de conversión en ClientManager
        self.app_controller.client_manager.convert_prospect_to_client(
            self.selected_prospect
        )

    def update_prospect_status(self, prospect_id, new_status):
        """Actualiza el estado de un prospecto y refresca la lista"""
        success, mensaje = self.prospect_service.cambiar_estado_prospecto(prospect_id, new_status)
        if success:
            self.cargar_prospectos()
            # Si el prospecto actualizado es el seleccionado, actualizar detalles
            if self.selected_prospect and self.selected_prospect["id"] == prospect_id:
                updated_prospect = self.prospect_service.obtener_prospecto(prospect_id)
                if updated_prospect:
                    self.selected_prospect = updated_prospect
                    self.mostrar_detalles_prospecto(updated_prospect)
        return success

    def get_prospect_statistics(self):
        """Obtiene estadísticas de prospectos"""
        return self.prospect_service.obtener_estadisticas_prospectos()

    def filter_prospects_by_status(self, status):
        """Filtra prospectos por estado"""
        return self.prospect_service.obtener_prospectos_por_estado(status)

    def refresh_prospect_list(self):
        """Refresca la lista de prospectos"""
        self.cargar_prospectos()

    def show_prospect_context_menu(self, event):
        """Muestra menú contextual para prospectos"""
        if not self.selected_prospect:
            return

        context_menu = tk.Menu(self.app_controller.root, tearoff=0)

        # Opciones básicas
        context_menu.add_command(
            label="Nueva Consulta", command=self.open_new_consultation_dialog
        )
        context_menu.add_command(
            label="Ver Consultas", command=self.open_view_consultation_dialog
        )
        context_menu.add_separator()

        # Cambio de estado
        status_menu = tk.Menu(context_menu, tearoff=0)
        current_status = self.selected_prospect.get("estado", "")

        estados_disponibles = [
            "Consulta Inicial",
            "En Análisis",
            "Convertido",
            "Desestimado",
        ]
        for estado in estados_disponibles:
            if estado != current_status:
                status_menu.add_command(
                    label=estado,
                    command=lambda s=estado: self.change_prospect_status(s),
                )

        context_menu.add_cascade(label="Cambiar Estado", menu=status_menu)
        context_menu.add_separator()

        # Conversión
        if current_status != "Convertido":
            context_menu.add_command(
                label="Convertir a Cliente", command=self.convert_prospect_to_client
            )

        # Mostrar menú
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def change_prospect_status(self, new_status):
        """Cambia el estado de un prospecto"""
        if not self.selected_prospect:
            return

        prospect_id = self.selected_prospect["id"]
        prospect_name = self.selected_prospect["nombre"]

        # Confirmar cambio de estado
        if messagebox.askyesno(
            "Confirmar Cambio de Estado",
            f"¿Cambiar el estado del prospecto '{prospect_name}' a '{new_status}'?",
            parent=self.app_controller.root,
        ):

            success = self.update_prospect_status(prospect_id, new_status)
            if success:
                messagebox.showinfo(
                    "Éxito",
                    f"Estado cambiado a '{new_status}'",
                    parent=self.app_controller.root,
                )
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo cambiar el estado",
                    parent=self.app_controller.root,
                )

    def open_status_filter_dialog(self):
        """Abre diálogo para filtrar prospectos por estado"""
        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title("Filtrar Prospectos por Estado")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Seleccione los estados a mostrar:").pack(
            anchor=tk.W, pady=(0, 10)
        )

        # Variables para checkboxes
        estados_vars = {}
        estados_disponibles = [
            "Consulta Inicial",
            "En Análisis",
            "Convertido",
            "Desestimado",
        ]

        for estado in estados_disponibles:
            var = tk.BooleanVar(value=True)  # Por defecto todos seleccionados
            estados_vars[estado] = var
            ttk.Checkbutton(frame, text=estado, variable=var).pack(anchor=tk.W, pady=2)

        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))

        def apply_filter():
            selected_states = [
                estado for estado, var in estados_vars.items() if var.get()
            ]
            if not selected_states:
                messagebox.showwarning(
                    "Advertencia", "Seleccione al menos un estado.", parent=dialog
                )
                return

            self.apply_status_filter(selected_states)
            dialog.destroy()

        def select_all():
            for var in estados_vars.values():
                var.set(True)

        def select_none():
            for var in estados_vars.values():
                var.set(False)

        ttk.Button(button_frame, text="Seleccionar Todo", command=select_all).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Deseleccionar Todo", command=select_none).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Aplicar Filtro", command=apply_filter).pack(
            side=tk.RIGHT, padx=(5, 0)
        )
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(
            side=tk.RIGHT
        )

        self.app_controller.root.wait_window(dialog)

    def apply_status_filter(self, selected_states):
        """Aplica filtro de estados a la lista de prospectos"""
        # Limpiar lista actual
        for i in self.app_controller.prospect_tree.get_children():
            self.app_controller.prospect_tree.delete(i)

        # Cargar prospectos filtrados usando el servicio
        filtros = {'estados': selected_states}
        prospects = self.prospect_service.buscar_prospectos(filtros)
        
        for prospect in prospects:
            # Formatear fecha para mostrar usando utilidades argentinas
            fecha_str = self.prospect_service.formatear_fecha_para_mostrar(
                prospect.get("fecha_primera_consulta")
            )

            # Insertar en el TreeView
            if hasattr(self.app_controller, "window"):  # Es la ventana de prospectos
                values = (
                    prospect["id"],
                    prospect["nombre"],
                    prospect["estado"],
                    fecha_str,
                )
            else:  # Es la ventana principal (compatibilidad)
                values = (prospect["id"], prospect["nombre"], prospect["estado"])

            self.app_controller.prospect_tree.insert(
                "", tk.END, values=values, iid=str(prospect["id"])
            )

        # Limpiar selección
        self.selected_prospect = None
        if hasattr(self.app_controller, "clear_selection"):
            self.app_controller.clear_selection()
        else:
            self.limpiar_detalles_prospecto()
            self.deshabilitar_botones_prospecto()

    def show_prospect_statistics(self):
        """Muestra estadísticas de prospectos"""
        stats = self.get_prospect_statistics()
        
        if not stats:
            messagebox.showinfo("Estadísticas", "No hay datos estadísticos disponibles.", 
                              parent=self.app_controller.root)
            return
        
        # Crear ventana de estadísticas
        stats_dialog = tk.Toplevel(self.app_controller.root)
        stats_dialog.title("Estadísticas de Prospectos")
        stats_dialog.transient(self.app_controller.root)
        stats_dialog.grab_set()
        stats_dialog.resizable(False, False)
        
        frame = ttk.Frame(stats_dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Estadísticas de Prospectos", 
                 font=("TkDefaultFont", 12, "bold")).pack(pady=(0, 15))
        
        # Mostrar estadísticas
        for key, value in stats.items():
            ttk.Label(frame, text=f"{key}: {value}").pack(anchor=tk.W, pady=2)
        
        ttk.Button(frame, text="Cerrar", command=stats_dialog.destroy).pack(pady=(15, 0))
        
        self.app_controller.root.wait_window(stats_dialog)

    def export_prospect_consultations(self):
        """Exporta todas las consultas del prospecto seleccionado usando el servicio unificado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return
        
        # Usar el servicio para exportar consultas (integrado con WordExportManager)
        success, mensaje, filepath = self.prospect_service.exportar_consultas_prospecto(
            self.selected_prospect, 
            self.app_controller.root
        )
        
        if success:
            messagebox.showinfo("Éxito", mensaje, parent=self.app_controller.root)
            
            # Preguntar si quiere abrir el archivo
            if filepath and messagebox.askyesno("Abrir Archivo", 
                                              "¿Desea abrir el archivo exportado?", 
                                              parent=self.app_controller.root):
                try:
                    import os
                    os.startfile(filepath)  # Windows
                except:
                    try:
                        import subprocess
                        subprocess.run(['xdg-open', filepath])  # Linux
                    except:
                        try:
                            subprocess.run(['open', filepath])  # macOS
                        except:
                            pass  # Si no puede abrir, no hacer nada
        else:
            messagebox.showerror("Error", mensaje, parent=self.app_controller.root)

    def show_ai_analysis_history(self):
        """Muestra el historial de análisis de IA del prospecto seleccionado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return
        
        # Obtener consultas con análisis IA
        consultas = self.prospect_service.obtener_consultas_prospecto(self.selected_prospect["id"])
        consultas_con_ia = [c for c in consultas if c.get('hechos_reformulados_ia') and c['hechos_reformulados_ia'].strip()]
        
        if not consultas_con_ia:
            messagebox.showinfo("Sin Análisis IA", 
                              f"El prospecto '{self.selected_prospect['nombre']}' no tiene consultas con análisis de IA.",
                              parent=self.app_controller.root)
            return
        
        # Mostrar diálogo con historial
        self._show_consultation_list_dialog(consultas_con_ia)

    def delete_prospect(self):
        """Elimina el prospecto seleccionado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return
        
        # Confirmar eliminación
        if not messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el prospecto '{self.selected_prospect['nombre']}'?\n\n"
            "Esta acción también eliminará todas las consultas asociadas y no se puede deshacer.",
            parent=self.app_controller.root,
        ):
            return
        
        # Usar el servicio para eliminar
        success, mensaje = self.prospect_service.eliminar_prospecto(self.selected_prospect["id"])
        
        if success:
            messagebox.showinfo("Éxito", mensaje, parent=self.app_controller.root)
            self.cargar_prospectos()  # Recargar lista
        else:
            messagebox.showerror("Error", mensaje, parent=self.app_controller.root)

    def open_edit_prospect_dialog(self):
        """Abre el diálogo para editar un prospecto existente"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return
        
        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title(f"Editar Prospecto - {self.selected_prospect['nombre']}")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Variables de Tkinter con valores actuales
        name_var = tk.StringVar(value=self.selected_prospect.get('nombre', ''))
        contact_var = tk.StringVar(value=self.selected_prospect.get('contacto', ''))

        # Layout de los widgets
        row_idx = 0
        ttk.Label(frame, text="Nombre Completo:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
        name_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Contacto:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        contact_entry = ttk.Entry(frame, textvariable=contact_var, width=40)
        contact_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Notas Generales:").grid(
            row=row_idx, column=0, sticky=tk.NW, pady=3, padx=5
        )
        notes_text = tk.Text(frame, width=40, height=4)
        notes_text.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        
        # Cargar notas actuales
        if self.selected_prospect.get('notas_generales'):
            notes_text.insert("1.0", self.selected_prospect['notas_generales'])
        
        row_idx += 1

        frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=15)

        def save_changes():
            nombre = name_var.get().strip()
            contacto = contact_var.get().strip()
            notas = notes_text.get("1.0", tk.END).strip()

            # Preparar datos del prospecto
            datos_prospecto = {
                'nombre': nombre,
                'contacto': contacto,
                'notas_generales': notas
            }
            
            # Usar el servicio para editar el prospecto
            success, mensaje = self.prospect_service.editar_prospecto(
                self.selected_prospect["id"], 
                datos_prospecto
            )
            
            if success:
                messagebox.showinfo("Éxito", mensaje, parent=self.app_controller.root)
                dialog.destroy()
                self.cargar_prospectos()  # Recargar lista
            else:
                messagebox.showerror("Error", mensaje, parent=dialog)

        ttk.Button(button_frame, text="Guardar Cambios", command=save_changes).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

        name_entry.focus_set()
        self.app_controller.root.wait_window(dialog)

    # ========================================
    # FUNCIONES DE EXPORTACIÓN UNIFICADAS
    # ========================================

    def _export_selected_consultation(self, tree_widget, parent_dialog):
        """Exporta la consulta seleccionada a Word usando el servicio unificado"""
        selection = tree_widget.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una consulta primero.", parent=parent_dialog)
            return
        
        try:
            consulta_id = int(selection[0])
            # Obtener consultas del prospecto
            consultas = self.prospect_service.obtener_consultas_prospecto(self.selected_prospect["id"])
            consulta = next((c for c in consultas if c['id'] == consulta_id), None)
            
            if not consulta:
                messagebox.showerror("Error", "No se pudo encontrar la consulta seleccionada.", parent=parent_dialog)
                return
            
            # Usar el servicio para exportar consulta individual
            success, mensaje, filepath = self.prospect_service.exportar_consulta_individual(
                self.selected_prospect,
                consulta,
                parent_dialog
            )
            
            if success:
                messagebox.showinfo("Éxito", mensaje, parent=parent_dialog)
                
                # Preguntar si quiere abrir el archivo
                if filepath and messagebox.askyesno("Abrir Archivo", 
                                                  "¿Desea abrir el archivo exportado?", 
                                                  parent=parent_dialog):
                    try:
                        import os
                        os.startfile(filepath)  # Windows
                    except:
                        try:
                            import subprocess
                            subprocess.run(['xdg-open', filepath])  # Linux
                        except:
                            try:
                                subprocess.run(['open', filepath])  # macOS
                            except:
                                pass  # Si no puede abrir, no hacer nada
            else:
                messagebox.showerror("Error", mensaje, parent=parent_dialog)
                
        except (ValueError, IndexError) as e:
            messagebox.showerror("Error", f"Error al procesar la consulta seleccionada: {e}", parent=parent_dialog)

    def _edit_selected_consultation(self, tree_widget, parent_dialog):
        """Edita la consulta seleccionada"""
        selection = tree_widget.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una consulta primero.", parent=parent_dialog)
            return
        
        try:
            consulta_id = int(selection[0])
            # Obtener consultas del prospecto
            consultas = self.prospect_service.obtener_consultas_prospecto(self.selected_prospect["id"])
            consulta = next((c for c in consultas if c['id'] == consulta_id), None)
            
            if not consulta:
                messagebox.showerror("Error", "No se pudo encontrar la consulta seleccionada.", parent=parent_dialog)
                return
            
            # Cerrar diálogo actual y abrir editor
            parent_dialog.destroy()
            
            # Importar aquí para evitar dependencias circulares
            from prospect_dialog_manager import ProspectDialogManager
            dialog_manager = ProspectDialogManager(self.app_controller)
            dialog_manager.open_consultation_dialog(self.selected_prospect, consulta)
            
        except (ValueError, IndexError) as e:
            messagebox.showerror("Error", f"Error al procesar la consulta seleccionada: {e}", parent=parent_dialog)

    def _delete_selected_consultation(self, tree_widget, parent_dialog):
        """Elimina la consulta seleccionada"""
        selection = tree_widget.selection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una consulta primero.", parent=parent_dialog)
            return
        
        try:
            consulta_id = int(selection[0])
            # Obtener consultas del prospecto
            consultas = self.prospect_service.obtener_consultas_prospecto(self.selected_prospect["id"])
            consulta = next((c for c in consultas if c['id'] == consulta_id), None)
            
            if not consulta:
                messagebox.showerror("Error", "No se pudo encontrar la consulta seleccionada.", parent=parent_dialog)
                return
            
            # Confirmar eliminación
            fecha_str = self.prospect_service.formatear_fecha_para_mostrar(consulta.get('fecha_consulta'))
            if not messagebox.askyesno(
                "Confirmar Eliminación",
                f"¿Está seguro de que desea eliminar la consulta del {fecha_str}?\n\n"
                "Esta acción no se puede deshacer.",
                parent=parent_dialog,
            ):
                return
            
            # Eliminar consulta
            success = self.db.delete_consulta(consulta_id)
            
            if success:
                messagebox.showinfo("Éxito", "Consulta eliminada exitosamente.", parent=parent_dialog)
                parent_dialog.destroy()
                # Reabrir diálogo de consultas actualizado
                self.open_view_consultation_dialog()
            else:
                messagebox.showerror("Error", "No se pudo eliminar la consulta.", parent=parent_dialog)
                
        except (ValueError, IndexError) as e:
            messagebox.showerror("Error", f"Error al procesar la consulta seleccionada: {e}", parent=parent_dialog)
            for prospect in prospects:
                # Formatear fecha para mostrar
                fecha_consulta = prospect.get("fecha_primera_consulta")
                if fecha_consulta:
                    if isinstance(fecha_consulta, str):
                        fecha_str = fecha_consulta
                    else:
                        fecha_str = date_utils.DateFormatter.to_display_format(fecha_consulta)
                else:
                    fecha_str = "N/A"

                # Insertar en el TreeView (adaptado para la nueva ventana)
                if hasattr(
                    self.app_controller, "window"
                ):  # Es la ventana de prospectos
                    values = (
                        prospect["id"],
                        prospect["nombre"],
                        prospect["estado"],
                        fecha_str,
                    )
                else:  # Es la ventana principal (compatibilidad)
                    values = (prospect["id"], prospect["nombre"], prospect["estado"])

                self.app_controller.prospect_tree.insert(
                    "", tk.END, values=values, iid=str(prospect["id"])
                )

        # Limpiar selección
        self.selected_prospect = None
        if hasattr(self.app_controller, "clear_selection"):
            self.app_controller.clear_selection()
        else:
            self.limpiar_detalles_prospecto()
            self.deshabilitar_botones_prospecto()

    def show_prospect_statistics(self):
        """Muestra estadísticas detalladas de prospectos"""
        stats = self.get_prospect_statistics()

        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title("Estadísticas de Prospectos")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.geometry("400x300")

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Estadísticas generales
        ttk.Label(
            frame, text="Estadísticas Generales", font=("TkDefaultFont", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(frame, text=f"Total de Prospectos: {stats['total_prospectos']}").pack(
            anchor=tk.W, pady=2
        )
        ttk.Label(
            frame, text=f"Convertidos este mes: {stats['convertidos_mes_actual']}"
        ).pack(anchor=tk.W, pady=2)
        ttk.Label(
            frame, text=f"Consultas este mes: {stats['consultas_mes_actual']}"
        ).pack(anchor=tk.W, pady=2)

        # Estadísticas por estado
        ttk.Label(frame, text="Por Estado", font=("TkDefaultFont", 12, "bold")).pack(
            anchor=tk.W, pady=(15, 10)
        )

        for estado, cantidad in stats["por_estado"].items():
            ttk.Label(frame, text=f"{estado}: {cantidad}").pack(anchor=tk.W, pady=2)

        # Botón cerrar
        ttk.Button(frame, text="Cerrar", command=dialog.destroy).pack(pady=(20, 0))

        self.app_controller.root.wait_window(dialog)

    def open_edit_prospect_dialog(self):
        """Abre el diálogo para editar un prospecto existente"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return

        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title(f"Editar Prospecto - {self.selected_prospect['nombre']}")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)

        # Variables de Tkinter pre-rellenadas
        name_var = tk.StringVar(value=self.selected_prospect.get("nombre", ""))
        contact_var = tk.StringVar(value=self.selected_prospect.get("contacto", ""))
        notes_var = tk.StringVar(
            value=self.selected_prospect.get("notas_generales", "")
        )

        # Layout de los widgets
        row_idx = 0
        ttk.Label(frame, text="Nombre Completo:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
        name_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Contacto:").grid(
            row=row_idx, column=0, sticky=tk.W, pady=3, padx=5
        )
        contact_entry = ttk.Entry(frame, textvariable=contact_var, width=40)
        contact_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Notas Generales:").grid(
            row=row_idx, column=0, sticky=tk.NW, pady=3, padx=5
        )
        notes_text = tk.Text(frame, width=40, height=4)
        notes_text.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        notes_text.insert("1.0", notes_var.get())
        row_idx += 1

        frame.columnconfigure(1, weight=1)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=15)

        def save_changes():
            nombre = name_var.get().strip()
            contacto = contact_var.get().strip()
            notas = notes_text.get("1.0", tk.END).strip()

            # Validar datos usando función centralizada
            datos_prospecto = {
                'nombre': nombre,
                'contacto': contacto,
                'notas_generales': notas
            }
            
            es_valido, mensaje_error = self.validar_datos_prospecto(datos_prospecto)
            if not es_valido:
                messagebox.showwarning(
                    "Advertencia",
                    mensaje_error,
                    parent=dialog,
                )
                return

            # Actualizar prospecto
            success = self.db.update_prospecto(
                self.selected_prospect["id"],
                nombre=nombre,
                contacto=contacto,
                notas_generales=notas,
            )

            if success:
                messagebox.showinfo(
                    "Éxito",
                    "Prospecto actualizado con éxito.",
                    parent=self.app_controller.root,
                )
                dialog.destroy()
                self.cargar_prospectos()
                # Actualizar datos del prospecto seleccionado
                updated_prospect = self.db.get_prospecto_by_id(
                    self.selected_prospect["id"]
                )
                if updated_prospect:
                    self.selected_prospect = updated_prospect
                    self.mostrar_detalles_prospecto(updated_prospect)
            else:
                messagebox.showerror(
                    "Error", "No se pudo actualizar el prospecto.", parent=dialog
                )

        ttk.Button(button_frame, text="Guardar Cambios", command=save_changes).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(
            side=tk.LEFT, padx=5
        )

        name_entry.focus_set()
        self.app_controller.root.wait_window(dialog)

    def delete_prospect(self):
        """Elimina el prospecto seleccionado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return

        prospect_name = self.selected_prospect["nombre"]
        prospect_id = self.selected_prospect["id"]

        # Verificar si tiene consultas
        consultas = self.db.get_consultas_by_prospecto_id(prospect_id)

        warning_msg = (
            f"¿Está seguro de que desea eliminar el prospecto '{prospect_name}'?"
        )
        if consultas:
            warning_msg += (
                f"\n\nEsto también eliminará {len(consultas)} consulta(s) asociada(s)."
            )
        warning_msg += "\n\nEsta acción no se puede deshacer."

        if messagebox.askyesno(
            "Confirmar Eliminación",
            warning_msg,
            parent=self.app_controller.root,
            icon="warning",
        ):

            success = self.db.delete_prospecto(prospect_id)
            if success:
                messagebox.showinfo(
                    "Éxito",
                    f"Prospecto '{prospect_name}' eliminado correctamente.",
                    parent=self.app_controller.root,
                )
                self.cargar_prospectos()
                self.selected_prospect = None
                self.limpiar_detalles_prospecto()
                self.deshabilitar_botones_prospecto()
            else:
                messagebox.showerror(
                    "Error",
                    "No se pudo eliminar el prospecto.",
                    parent=self.app_controller.root,
                )
    
    def export_prospect_consultations(self):
        """Exporta todas las consultas del prospecto seleccionado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return
        
        # Obtener consultas
        consultas = self.db.get_consultas_by_prospecto_id(self.selected_prospect['id'])
        
        if not consultas:
            messagebox.showinfo("Información", "Este prospecto no tiene consultas registradas.")
            return
        
        # Usar WordExportManager para exportar
        from word_export_manager import WordExportManager
        export_manager = WordExportManager()
        
        # Exportar múltiples consultas
        filepath = export_manager.export_multiple_consultations(
            self.selected_prospect, 
            consultas, 
            self.app_controller.root
        )
        
        if filepath:
            print(f"Consultas exportadas exitosamente: {filepath}")
        else:
            print("Error al exportar consultas")
    
    def show_ai_analysis_history(self):
        """Muestra el historial de análisis de IA del prospecto seleccionado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.")
            return
        
        # Obtener consultas con análisis IA
        consultas_ia = self.db.get_consultas_with_ai_analysis(self.selected_prospect['id'])
        
        if not consultas_ia:
            messagebox.showinfo("Sin Análisis IA", 
                              "Este prospecto no tiene consultas con análisis de IA.")
            return
        
        # Crear ventana de historial
        history_window = tk.Toplevel(self.app_controller.root)
        history_window.title(f"Historial de Análisis IA - {self.selected_prospect['nombre']}")
        history_window.geometry("800x600")
        history_window.transient(self.app_controller.root)
        
        # Frame principal
        main_frame = ttk.Frame(history_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, 
                               text=f"Historial de Análisis IA - {self.selected_prospect['nombre']}", 
                               font=("TkDefaultFont", 12, "bold"))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Lista de consultas
        list_frame = ttk.LabelFrame(main_frame, text="Consultas con Análisis IA", padding="5")
        list_frame.pack(fill=tk.BOTH, expand=True)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # TreeView
        columns = ("ID", "Fecha", "Exportado", "Estado")
        history_tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        history_tree.heading("ID", text="ID")
        history_tree.heading("Fecha", text="Fecha")
        history_tree.heading("Exportado", text="Exportado")
        history_tree.heading("Estado", text="Estado")
        
        history_tree.column("ID", width=50, stretch=tk.NO)
        history_tree.column("Fecha", width=100, stretch=tk.NO)
        history_tree.column("Exportado", width=80, stretch=tk.NO)
        history_tree.column("Estado", width=150, stretch=tk.YES)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=history_tree.yview)
        history_tree.configure(yscrollcommand=scrollbar.set)
        
        history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Llenar la lista
        for consulta in consultas_ia:
            fecha_str = date_utils.DateFormatter.to_display_format(consulta['fecha_consulta']) or "N/A"
            exportado = "Sí" if consulta.get('exportado') else "No"
            
            # Determinar estado basado en contenido
            tiene_relato = bool(consulta.get('relato_original_cliente', '').strip())
            tiene_analisis = bool(consulta.get('hechos_reformulados_ia', '').strip())
            
            if tiene_relato and tiene_analisis:
                estado = "✅ Completo"
            elif tiene_analisis:
                estado = "🟡 Solo análisis IA"
            elif tiene_relato:
                estado = "🔴 Solo relato"
            else:
                estado = "❌ Vacío"
            
            history_tree.insert("", tk.END, 
                              values=(consulta['id'], fecha_str, exportado, estado),
                              iid=str(consulta['id']))
        
        # Frame de detalles
        details_frame = ttk.LabelFrame(main_frame, text="Vista Previa del Análisis", padding="10")
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        
        # Área de texto para mostrar el análisis
        analysis_text = tk.Text(details_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        analysis_scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=analysis_text.yview)
        analysis_text.configure(yscrollcommand=analysis_scrollbar.set)
        
        analysis_text.grid(row=0, column=0, sticky="nsew")
        analysis_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Función para mostrar detalles
        def on_select(event):
            selected_items = history_tree.selection()
            if selected_items:
                consulta_id = int(selected_items[0])
                consulta_seleccionada = next((c for c in consultas_ia if c['id'] == consulta_id), None)
                
                if consulta_seleccionada:
                    analysis_text.config(state=tk.NORMAL)
                    analysis_text.delete("1.0", tk.END)
                    
                    # Mostrar información completa
                    content = f"CONSULTA ID: {consulta_seleccionada['id']}\n"
                    content += f"FECHA: {consulta_seleccionada['fecha_consulta']}\n"
                    content += f"EXPORTADO: {'Sí' if consulta_seleccionada.get('exportado') else 'No'}\n"
                    if consulta_seleccionada.get('fecha_exportacion'):
                        content += f"FECHA EXPORTACIÓN: {consulta_seleccionada['fecha_exportacion']}\n"
                    content += "\n" + "="*50 + "\n\n"
                    
                    if consulta_seleccionada.get('relato_original_cliente'):
                        content += "RELATO ORIGINAL:\n"
                        content += consulta_seleccionada['relato_original_cliente'] + "\n\n"
                    
                    if consulta_seleccionada.get('hechos_reformulados_ia'):
                        content += "ANÁLISIS DE IA:\n"
                        content += consulta_seleccionada['hechos_reformulados_ia']
                    
                    analysis_text.insert("1.0", content)
                    analysis_text.config(state=tk.DISABLED)
        
        history_tree.bind("<<TreeviewSelect>>", on_select)
        
        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def export_selected():
            selected_items = history_tree.selection()
            if not selected_items:
                messagebox.showwarning("Advertencia", "Seleccione una consulta.", parent=history_window)
                return
            
            consulta_id = int(selected_items[0])
            consulta_seleccionada = next((c for c in consultas_ia if c['id'] == consulta_id), None)
            
            if consulta_seleccionada:
                from word_export_manager import WordExportManager
                export_manager = WordExportManager()
                
                filepath = export_manager.export_consultation_to_word(
                    self.selected_prospect,
                    consulta_seleccionada,
                    history_window
                )
                
                if filepath:
                    # Marcar consulta como exportada en la base de datos
                    export_success = self.db.mark_consulta_as_exported(consulta_seleccionada['id'], filepath)
                    if not export_success:
                        print(f"Advertencia: No se pudo marcar la consulta {consulta_seleccionada['id']} como exportada")
                    
                    # Actualizar la lista
                    updated_consultas = self.db.get_consultas_with_ai_analysis(self.selected_prospect['id'])
                    # Refrescar TreeView
                    for item in history_tree.get_children():
                        history_tree.delete(item)
                    
                    for consulta in updated_consultas:
                        fecha_str = date_utils.DateFormatter.to_display_format(consulta['fecha_consulta']) or "N/A"
                        exportado = "Sí" if consulta.get('exportado') else "No"
                        
                        tiene_relato = bool(consulta.get('relato_original_cliente', '').strip())
                        tiene_analisis = bool(consulta.get('hechos_reformulados_ia', '').strip())
                        
                        if tiene_relato and tiene_analisis:
                            estado = "✅ Completo"
                        elif tiene_analisis:
                            estado = "🟡 Solo análisis IA"
                        elif tiene_relato:
                            estado = "🔴 Solo relato"
                        else:
                            estado = "❌ Vacío"
                        
                        history_tree.insert("", tk.END, 
                                          values=(consulta['id'], fecha_str, exportado, estado),
                                          iid=str(consulta['id']))
                    
                    # Actualizar la variable para futuras referencias
                    consultas_ia[:] = updated_consultas
        
        ttk.Button(button_frame, text="Exportar Seleccionada", command=export_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cerrar", command=history_window.destroy).pack(side=tk.RIGHT)
        
        # Seleccionar la primera consulta si existe
        if consultas_ia:
            first_item = history_tree.get_children()[0]
            history_tree.selection_set(first_item)
            history_tree.focus(first_item)
            # Trigger the selection event
            on_select(None)
    
    def _edit_selected_consultation(self, tree_widget, parent_dialog):
        """Edita la consulta seleccionada"""
        selection = tree_widget.selection()
        if not selection:
            return
        
        consulta_id = int(selection[0])
        consulta = self.db.get_consulta_by_id(consulta_id)
        
        if not consulta:
            messagebox.showerror("Error", "No se pudo cargar la consulta seleccionada.")
            return
        
        # Cerrar diálogo actual y abrir editor
        parent_dialog.destroy()
        
        # Abrir diálogo de edición
        from prospect_dialog_manager import ProspectDialogManager
        dialog_manager = ProspectDialogManager(self.app_controller)
        dialog_manager.open_consultation_dialog(self.selected_prospect, consulta)
    
    def _delete_selected_consultation(self, tree_widget, parent_dialog):
        """Elimina la consulta seleccionada"""
        selection = tree_widget.selection()
        if not selection:
            return
        
        consulta_id = int(selection[0])
        consulta = self.db.get_consulta_by_id(consulta_id)
        
        if not consulta:
            messagebox.showerror("Error", "No se pudo cargar la consulta seleccionada.")
            return
        
        # Confirmar eliminación
        fecha_str = date_utils.DateFormatter.to_display_format(consulta['fecha_consulta']) or "N/A"
        if messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar la consulta del {fecha_str}?\n\nEsta acción no se puede deshacer.",
            parent=parent_dialog,
            icon="warning"
        ):
            success = self.db.delete_consulta(consulta_id)
            if success:
                messagebox.showinfo("Éxito", "Consulta eliminada correctamente.", parent=parent_dialog)
                parent_dialog.destroy()
                # Reabrir la ventana de consultas actualizada
                self.open_view_consultation_dialog()
            else:
                messagebox.showerror("Error", "No se pudo eliminar la consulta.", parent=parent_dialog)
    
    def _export_selected_consultation(self, tree_widget, parent_dialog):
        """Exporta la consulta seleccionada a Word"""
        selection = tree_widget.selection()
        if not selection:
            return
        
        consulta_id = int(selection[0])
        consulta = self.db.get_consulta_by_id(consulta_id)
        
        if not consulta:
            messagebox.showerror("Error", "No se pudo cargar la consulta seleccionada.")
            return
        
        # Verificar que tenga análisis IA
        if not consulta.get('hechos_reformulados_ia') or not consulta['hechos_reformulados_ia'].strip():
            messagebox.showwarning("Advertencia", "Esta consulta no tiene análisis de IA para exportar.")
            return
        
        # Exportar usando WordExportManager
        from word_export_manager import WordExportManager
        export_manager = WordExportManager()
        
        filepath = export_manager.export_consultation_to_word(
            self.selected_prospect,
            consulta,
            parent_dialog
        )
        
        if filepath:
            # Marcar consulta como exportada en la base de datos
            export_success = self.db.mark_consulta_as_exported(consulta['id'], filepath)
            if export_success:
                print(f"Consulta individual exportada y marcada: {filepath}")
            else:
                print(f"Consulta exportada pero no se pudo marcar en BD: {filepath}")

    # ========================================
    # ALIASES DE COMPATIBILIDAD
    # ========================================
    
    # Mantener nombres originales para compatibilidad con el resto del CRM
    load_prospects = cargar_prospectos
    on_prospect_select = al_seleccionar_prospecto
    display_prospect_details = mostrar_detalles_prospecto
    clear_prospect_details = limpiar_detalles_prospecto
    enable_prospect_buttons = habilitar_botones_prospecto
    disable_prospect_buttons = deshabilitar_botones_prospecto


# Funciones de compatibilidad para mantener la interfaz existente
def create_prospect_manager(app_controller):
    """Función de compatibilidad para crear un ProspectManager"""
    return ProspectManager(app_controller)
