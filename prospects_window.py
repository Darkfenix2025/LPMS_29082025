"""
Prospects Window - Ventana dedicada para la gestión de prospectos
Ventana Toplevel independiente para el módulo de triage legal
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import os
from prospect_manager import ProspectManager
from prospect_service import ProspectService
import date_utils


class ProspectsWindow:
    """Ventana principal para la gestión de prospectos"""
    
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.selected_prospect = None
        
        # Crear servicio de prospectos (capa de lógica de negocio)
        self.prospect_service = ProspectService()
        
        # Crear ventana Toplevel
        self.window = tk.Toplevel(parent_app.root)
        self.window.title("Gestión de Prospectos - Triage Legal")
        self.window.geometry("1200x600")  # Tamaño inicial más grande
        self.window.minsize(900, 400)     # Tamaño mínimo
        self.window.transient(parent_app.root)
        
        # Configurar el cierre de la ventana
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Configurar redimensionamiento responsivo
        self.window.bind('<Configure>', self.on_window_resize)
        
        # Crear ProspectManager adaptado para esta ventana
        self.prospect_manager = ProspectManager(self)
        
        self.create_widgets()
        self.prospect_manager.cargar_prospectos()
        
        # Centrar la ventana
        self.center_window()
    
    def center_window(self):
        """Centra la ventana en la pantalla"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_window_resize(self, event):
        """Maneja el redimensionamiento de la ventana para mantener proporciones"""
        if event.widget == self.window:
            # Ajustar anchos de columnas del TreeView según el tamaño de la ventana
            if hasattr(self, 'prospect_tree'):
                window_width = self.window.winfo_width()
                # Calcular anchos proporcionales para las columnas
                available_width = int(window_width * 0.65)  # 65% del ancho total para el TreeView
                
                # Distribución de columnas: ID(8%), Nombre(50%), Estado(22%), Fecha(20%)
                id_width = max(60, int(available_width * 0.08))
                nombre_width = max(200, int(available_width * 0.50))
                estado_width = max(120, int(available_width * 0.22))
                fecha_width = max(100, int(available_width * 0.20))
                
                self.prospect_tree.column("ID", width=id_width)
                self.prospect_tree.column("Nombre", width=nombre_width)
                self.prospect_tree.column("Estado", width=estado_width)
                self.prospect_tree.column("Fecha", width=fecha_width)
    
    def create_widgets(self):
        """Crea la interfaz de la ventana de prospectos"""
        # Frame principal
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid - Distribución mejorada: 70% lista, 30% detalles
        main_frame.columnconfigure(0, weight=7)  # Lista de prospectos (70%)
        main_frame.columnconfigure(1, weight=3)  # Detalles y acciones (30%)
        main_frame.rowconfigure(0, weight=1)
        
        # --- Panel izquierdo: Lista de prospectos ---
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # Título y filtros
        title_frame = ttk.Frame(left_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_frame.columnconfigure(1, weight=1)
        
        ttk.Label(title_frame, text="Lista de Prospectos", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        
        # Botones de filtro y estadísticas
        filter_frame = ttk.Frame(title_frame)
        filter_frame.grid(row=0, column=1, sticky="e")
        
        ttk.Button(filter_frame, text="Filtrar", 
                  command=self.prospect_manager.open_status_filter_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Estadísticas", 
                  command=self.prospect_manager.show_prospect_statistics).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Actualizar", 
                  command=self.prospect_manager.refresh_prospect_list).pack(side=tk.LEFT, padx=2)
        
        # Lista de prospectos
        list_frame = ttk.LabelFrame(left_frame, text="Prospectos", padding="5")
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # TreeView
        self.prospect_tree = ttk.Treeview(
            list_frame,
            columns=("ID", "Nombre", "Estado", "Fecha"),
            show="headings",
            selectmode="browse"
        )
        
        # Configurar columnas - Distribución mejorada
        self.prospect_tree.heading("ID", text="ID")
        self.prospect_tree.heading("Nombre", text="Nombre")
        self.prospect_tree.heading("Estado", text="Estado")
        self.prospect_tree.heading("Fecha", text="Fecha Consulta")
        
        self.prospect_tree.column("ID", width=60, stretch=tk.NO)
        self.prospect_tree.column("Nombre", width=280, stretch=tk.YES)
        self.prospect_tree.column("Estado", width=140, stretch=tk.NO)
        self.prospect_tree.column("Fecha", width=120, stretch=tk.NO)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.prospect_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.prospect_tree.xview)
        self.prospect_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid del TreeView y scrollbars
        self.prospect_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Eventos
        self.prospect_tree.bind("<<TreeviewSelect>>", self.on_prospect_select)
        self.prospect_tree.bind("<Button-3>", self.show_context_menu)
        self.prospect_tree.bind("<Double-1>", self.on_double_click)
        
        # Botones de acción principales
        action_frame = ttk.Frame(left_frame)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(action_frame, text="Nuevo Prospecto", 
                  command=self.prospect_manager.open_new_prospect_dialog).pack(side=tk.LEFT, padx=(0, 5))
        
        self.edit_prospect_btn = ttk.Button(action_frame, text="Editar Prospecto", 
                  command=self.prospect_manager.open_edit_prospect_dialog, state=tk.DISABLED)
        self.edit_prospect_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_prospect_btn = ttk.Button(action_frame, text="Borrar Prospecto", 
                  command=self.prospect_manager.delete_prospect, state=tk.DISABLED)
        self.delete_prospect_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # --- Panel derecho: Detalles y acciones ---
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Detalles del prospecto
        details_frame = ttk.LabelFrame(right_frame, text="Detalles del Prospecto", padding="10")
        details_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        details_frame.columnconfigure(1, weight=1)
        
        # Labels para detalles
        row = 0
        ttk.Label(details_frame, text="Nombre:").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
        self.prospect_detail_name_lbl = ttk.Label(details_frame, text="", font=("TkDefaultFont", 9, "bold"))
        self.prospect_detail_name_lbl.grid(row=row, column=1, sticky="w", pady=2)
        
        row += 1
        ttk.Label(details_frame, text="Contacto:").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
        self.prospect_detail_contact_lbl = ttk.Label(details_frame, text="")
        self.prospect_detail_contact_lbl.grid(row=row, column=1, sticky="w", pady=2)
        
        row += 1
        ttk.Label(details_frame, text="Estado:").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
        self.prospect_detail_status_lbl = ttk.Label(details_frame, text="")
        self.prospect_detail_status_lbl.grid(row=row, column=1, sticky="w", pady=2)
        
        row += 1
        ttk.Label(details_frame, text="Primera Consulta:").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
        self.prospect_detail_date_lbl = ttk.Label(details_frame, text="")
        self.prospect_detail_date_lbl.grid(row=row, column=1, sticky="w", pady=2)
        
        row += 1
        ttk.Label(details_frame, text="Conversión:").grid(row=row, column=0, sticky="w", pady=2, padx=(0, 10))
        self.prospect_detail_conversion_lbl = ttk.Label(details_frame, text="")
        self.prospect_detail_conversion_lbl.grid(row=row, column=1, sticky="w", pady=2)
        
        # Botones de acción
        buttons_frame = ttk.LabelFrame(right_frame, text="Acciones", padding="10")
        buttons_frame.grid(row=1, column=0, sticky="new", pady=(0, 10))
        
        self.new_consultation_btn = ttk.Button(
            buttons_frame, text="Nueva Consulta",
            command=self.prospect_manager.open_new_consultation_dialog,
            state=tk.DISABLED
        )
        self.new_consultation_btn.pack(fill=tk.X, pady=2)
        
        self.view_consultation_btn = ttk.Button(
            buttons_frame, text="Ver Consultas",
            command=self.prospect_manager.open_view_consultation_dialog,
            state=tk.DISABLED
        )
        self.view_consultation_btn.pack(fill=tk.X, pady=2)
        
        self.export_consultation_btn = ttk.Button(
            buttons_frame, text="Exportar Consultas",
            command=self.prospect_manager.export_prospect_consultations,
            state=tk.DISABLED
        )
        self.export_consultation_btn.pack(fill=tk.X, pady=2)
        
        self.ai_history_btn = ttk.Button(
            buttons_frame, text="Historial Análisis IA",
            command=self.prospect_manager.show_ai_analysis_history,
            state=tk.DISABLED
        )
        self.ai_history_btn.pack(fill=tk.X, pady=2)
        
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        self.convert_to_client_btn = ttk.Button(
            buttons_frame, text="Convertir a Cliente",
            command=self.convert_prospect_to_client,
            state=tk.DISABLED
        )
        self.convert_to_client_btn.pack(fill=tk.X, pady=2)
        
        # Botón para revertir conversión (solo visible si es aplicable)
        self.revert_conversion_btn = ttk.Button(
            buttons_frame, text="Revertir Conversión",
            command=self.revert_conversion,
            state=tk.DISABLED
        )
        # No se muestra por defecto, solo cuando sea aplicable
        
        ttk.Separator(buttons_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)
        
        # Cambio de estado
        ttk.Label(buttons_frame, text="Cambiar Estado:").pack(anchor="w", pady=(5, 2))
        
        self.status_var = tk.StringVar()
        self.status_combo = ttk.Combobox(
            buttons_frame, textvariable=self.status_var,
            values=["Consulta Inicial", "En Análisis", "Convertido", "Desestimado"],
            state="readonly"
        )
        self.status_combo.pack(fill=tk.X, pady=2)
        self.status_combo.bind("<<ComboboxSelected>>", self.on_status_change)
        
        # Notas generales
        notes_frame = ttk.LabelFrame(right_frame, text="Notas Generales", padding="10")
        notes_frame.grid(row=2, column=0, sticky="nsew")
        notes_frame.columnconfigure(0, weight=1)
        notes_frame.rowconfigure(0, weight=1)
        
        self.notes_text = tk.Text(notes_frame, height=8, wrap=tk.WORD)
        notes_scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notes_text.yview)
        self.notes_text.configure(yscrollcommand=notes_scrollbar.set)
        
        self.notes_text.grid(row=0, column=0, sticky="nsew")
        notes_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Botones para notas y exportar
        notes_buttons_frame = ttk.Frame(notes_frame)
        notes_buttons_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        notes_buttons_frame.columnconfigure(0, weight=1)
        
        ttk.Button(notes_buttons_frame, text="Exportar Consultas", 
                  command=self.export_prospect_consultations).pack(side=tk.LEFT)
        ttk.Button(notes_buttons_frame, text="Guardar Notas", 
                  command=self.save_notes).pack(side=tk.RIGHT)
    
    def on_prospect_select(self, event):
        """Maneja la selección de un prospecto"""
        selected_items = self.prospect_tree.selection()
        if selected_items:
            try:
                prospect_id = int(selected_items[0])
                prospect_data = self.prospect_service.obtener_prospecto(prospect_id)
                if prospect_data:
                    self.selected_prospect = prospect_data
                    self.prospect_manager.selected_prospect = prospect_data
                    self.display_prospect_details(prospect_data)
                    self.enable_buttons()
                else:
                    self.clear_selection()
            except (ValueError, IndexError):
                self.clear_selection()
        else:
            self.clear_selection()
    
    def display_prospect_details(self, prospect_data):
        """Muestra los detalles del prospecto seleccionado"""
        self.prospect_detail_name_lbl.config(text=prospect_data.get("nombre", "N/A"))
        self.prospect_detail_contact_lbl.config(text=prospect_data.get("contacto", "N/A"))
        self.prospect_detail_status_lbl.config(text=prospect_data.get("estado", "N/A"))
        
        # Formatear fecha
        fecha_consulta = prospect_data.get("fecha_primera_consulta")
        if fecha_consulta:
            if isinstance(fecha_consulta, str):
                fecha_str = fecha_consulta
            else:
                fecha_str = date_utils.DateFormatter.to_display_format(fecha_consulta)
            self.prospect_detail_date_lbl.config(text=fecha_str)
        else:
            self.prospect_detail_date_lbl.config(text="N/A")
        
        # Información de conversión
        if prospect_data.get("estado") == "Convertido" and prospect_data.get("cliente_convertido_nombre"):
            conversion_text = f"Convertido a: {prospect_data['cliente_convertido_nombre']}"
            if prospect_data.get("fecha_conversion"):
                fecha_conv = prospect_data["fecha_conversion"]
                if isinstance(fecha_conv, str):
                    fecha_conv_str = fecha_conv
                else:
                    fecha_conv_str = date_utils.DateFormatter.to_display_format(fecha_conv)
                conversion_text += f" ({fecha_conv_str})"
            self.prospect_detail_conversion_lbl.config(text=conversion_text)
        else:
            self.prospect_detail_conversion_lbl.config(text="No convertido")
        
        # Establecer estado en combo
        self.status_var.set(prospect_data.get("estado", ""))
        
        # Manejar visibilidad del botón de revertir conversión
        self._update_conversion_buttons(prospect_data)
        
        # Cargar notas
        self.notes_text.delete("1.0", tk.END)
        if prospect_data.get("notas_generales"):
            self.notes_text.insert("1.0", prospect_data["notas_generales"])
    
    def clear_selection(self):
        """Limpia la selección y detalles"""
        self.selected_prospect = None
        self.prospect_manager.selected_prospect = None
        self.prospect_detail_name_lbl.config(text="")
        self.prospect_detail_contact_lbl.config(text="")
        self.prospect_detail_status_lbl.config(text="")
        self.prospect_detail_date_lbl.config(text="")
        self.prospect_detail_conversion_lbl.config(text="")
        self.status_var.set("")
        self.notes_text.delete("1.0", tk.END)
        self.disable_buttons()
    
    def enable_buttons(self):
        """Habilita los botones de acción"""
        self.new_consultation_btn.config(state=tk.NORMAL)
        self.view_consultation_btn.config(state=tk.NORMAL)
        self.export_consultation_btn.config(state=tk.NORMAL)
        self.ai_history_btn.config(state=tk.NORMAL)
        self.convert_to_client_btn.config(state=tk.NORMAL)
        self.edit_prospect_btn.config(state=tk.NORMAL)
        self.delete_prospect_btn.config(state=tk.NORMAL)
    
    def disable_buttons(self):
        """Deshabilita los botones de acción"""
        self.new_consultation_btn.config(state=tk.DISABLED)
        self.view_consultation_btn.config(state=tk.DISABLED)
        self.export_consultation_btn.config(state=tk.DISABLED)
        self.ai_history_btn.config(state=tk.DISABLED)
        self.convert_to_client_btn.config(state=tk.DISABLED)
        self.edit_prospect_btn.config(state=tk.DISABLED)
        self.delete_prospect_btn.config(state=tk.DISABLED)
    
    def on_status_change(self, event):
        """Maneja el cambio de estado"""
        if not self.selected_prospect:
            return
        
        new_status = self.status_var.get()
        if new_status and new_status != self.selected_prospect.get("estado"):
            if messagebox.askyesno("Confirmar Cambio", 
                                 f"¿Cambiar el estado a '{new_status}'?", 
                                 parent=self.window):
                success = self.prospect_manager.update_prospect_status(
                    self.selected_prospect["id"], new_status
                )
                if success:
                    if self.selected_prospect:  # Verificar que no sea None
                        self.selected_prospect["estado"] = new_status
                        self.prospect_detail_status_lbl.config(text=new_status)
                    messagebox.showinfo("Éxito", f"Estado cambiado a '{new_status}'", 
                                      parent=self.window)
                else:
                    messagebox.showerror("Error", "No se pudo cambiar el estado", 
                                       parent=self.window)
                    # Revertir combo
                    self.status_var.set(self.selected_prospect.get("estado", ""))
            else:
                # Revertir combo
                self.status_var.set(self.selected_prospect.get("estado", ""))
    
    def save_notes(self):
        """Guarda las notas generales"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.", 
                                 parent=self.window)
            return
        
        notes = self.notes_text.get("1.0", tk.END).strip()
        
        # Preparar datos para editar
        datos_prospecto = {
            'nombre': self.selected_prospect.get('nombre', ''),
            'contacto': self.selected_prospect.get('contacto', ''),
            'notas_generales': notes
        }
        
        # Usar el servicio para editar el prospecto
        success, mensaje = self.prospect_service.editar_prospecto(
            self.selected_prospect["id"], 
            datos_prospecto
        )
        
        if success:
            self.selected_prospect["notas_generales"] = notes
            messagebox.showinfo("Éxito", "Notas guardadas correctamente.", 
                              parent=self.window)
        else:
            messagebox.showerror("Error", mensaje, parent=self.window)
    
    def convert_prospect_to_client(self):
        """Convierte el prospecto seleccionado a cliente usando el servicio unificado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.", 
                                 parent=self.window)
            return
        
        # Verificar que el prospecto no esté ya convertido
        if self.selected_prospect.get("estado") == "Convertido":
            cliente_id = self.selected_prospect.get("convertido_a_cliente_id")
            messagebox.showinfo(
                "Información",
                f"Este prospecto ya fue convertido al cliente con ID: {cliente_id}",
                parent=self.window
            )
            return
        
        # Confirmar conversión
        if not messagebox.askyesno(
            "Confirmar Conversión",
            f"¿Está seguro de que desea convertir el prospecto '{self.selected_prospect['nombre']}' a cliente?\n\n"
            "Esta acción:\n"
            "• Creará un nuevo cliente con los datos del prospecto\n"
            "• Mantendrá el historial de consultas\n"
            "• Marcará el prospecto como 'Convertido'\n"
            "• Permitirá gestionar el nuevo cliente desde el módulo de clientes",
            parent=self.window,
        ):
            return
        
        # Usar el servicio de conversión
        success, mensaje, cliente_id = self.prospect_service.convertir_prospecto_a_cliente(
            self.selected_prospect["id"]
        )
        
        if success:
            messagebox.showinfo("Conversión Exitosa", mensaje, parent=self.window)
            
            # Actualizar la lista de prospectos
            self.prospect_manager.cargar_prospectos()
            
            # Preguntar si quiere abrir la ficha del cliente
            if cliente_id and messagebox.askyesno(
                "Abrir Cliente",
                "¿Desea abrir la ficha del nuevo cliente?",
                parent=self.window
            ):
                self._abrir_ficha_cliente(cliente_id)
        else:
            messagebox.showerror("Error de Conversión", mensaje, parent=self.window)
    
    def revert_conversion(self):
        """Revierte la conversión de un prospecto a cliente si es posible"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.", 
                                 parent=self.window)
            return
        
        # Verificar que el prospecto esté convertido
        if self.selected_prospect.get("estado") != "Convertido":
            messagebox.showwarning(
                "Advertencia",
                "Este prospecto no ha sido convertido a cliente.",
                parent=self.window
            )
            return
        
        # Verificar si la conversión es reversible
        es_reversible, razon = self.prospect_service.verificar_conversion_reversible(
            self.selected_prospect["id"]
        )
        
        if not es_reversible:
            messagebox.showwarning(
                "Conversión No Reversible",
                f"No se puede revertir la conversión:\n\n{razon}",
                parent=self.window
            )
            return
        
        # Confirmar reversión
        cliente_id = self.selected_prospect.get("convertido_a_cliente_id")
        if not messagebox.askyesno(
            "Confirmar Reversión",
            f"¿Está seguro de que desea revertir la conversión?\n\n"
            f"Esta acción:\n"
            f"• Eliminará el cliente creado (ID: {cliente_id})\n"
            f"• Restaurará el prospecto al estado 'En Análisis'\n"
            f"• Mantendrá el historial de consultas del prospecto\n\n"
            f"ADVERTENCIA: Esta acción no se puede deshacer.",
            parent=self.window,
        ):
            return
        
        # Revertir la conversión
        success, mensaje = self.prospect_service.revertir_conversion(
            self.selected_prospect["id"]
        )
        
        if success:
            messagebox.showinfo("Reversión Exitosa", mensaje, parent=self.window)
            
            # Actualizar la lista de prospectos
            self.prospect_manager.cargar_prospectos()
        else:
            messagebox.showerror("Error de Reversión", mensaje, parent=self.window)
    
    def _abrir_ficha_cliente(self, cliente_id: int):
        """Abre la ficha del cliente en el módulo de clientes"""
        try:
            # Intentar abrir la ficha del cliente usando el parent_app
            if hasattr(self.parent_app, 'client_manager'):
                # Método específico para abrir cliente por ID (si existe)
                if hasattr(self.parent_app.client_manager, 'open_client_by_id'):
                    self.parent_app.client_manager.open_client_by_id(cliente_id)
                else:
                    # Método alternativo: abrir ventana de clientes y seleccionar
                    messagebox.showinfo(
                        "Cliente Creado",
                        f"Cliente creado exitosamente con ID: {cliente_id}\n\n"
                        "Puede encontrarlo en el módulo de Clientes.",
                        parent=self.window
                    )
            else:
                messagebox.showinfo(
                    "Cliente Creado",
                    f"Cliente creado exitosamente con ID: {cliente_id}",
                    parent=self.window
                )
        except Exception as e:
            print(f"Error abriendo ficha del cliente: {e}")
            messagebox.showinfo(
                "Cliente Creado",
                f"Cliente creado exitosamente con ID: {cliente_id}",
                parent=self.window
            )
    
    def show_context_menu(self, event):
        """Muestra menú contextual"""
        if not self.selected_prospect:
            return
        
        context_menu = tk.Menu(self.window, tearoff=0)
        
        context_menu.add_command(label="Nueva Consulta", 
                               command=self.prospect_manager.open_new_consultation_dialog)
        context_menu.add_command(label="Ver Consultas", 
                               command=self.prospect_manager.open_view_consultation_dialog)
        context_menu.add_separator()
        
        context_menu.add_command(label="Editar Prospecto", 
                               command=self.prospect_manager.open_edit_prospect_dialog)
        context_menu.add_command(label="Borrar Prospecto", 
                               command=self.prospect_manager.delete_prospect)
        context_menu.add_separator()
        
        if self.selected_prospect.get("estado") != "Convertido":
            context_menu.add_command(label="Convertir a Cliente", 
                                   command=self.convert_prospect_to_client)
        
        context_menu.add_separator()
        context_menu.add_command(label="Actualizar Lista", 
                               command=self.prospect_manager.cargar_prospectos)
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def on_double_click(self, event):
        """Maneja doble clic para abrir consultas"""
        if self.selected_prospect:
            self.prospect_manager.open_view_consultation_dialog()
    
    def on_closing(self):
        """Maneja el cierre de la ventana"""
        self.window.destroy()
    
    def export_prospect_consultations(self):
        """Exporta todas las consultas del prospecto seleccionado usando el servicio unificado"""
        if not self.selected_prospect:
            messagebox.showwarning("Advertencia", "Seleccione un prospecto primero.", 
                                 parent=self.window)
            return
        
        # Usar el servicio para exportar consultas (integrado con WordExportManager)
        success, mensaje, filepath = self.prospect_service.exportar_consultas_prospecto(
            self.selected_prospect, 
            self.window
        )
        
        if success:
            messagebox.showinfo("Éxito", mensaje, parent=self.window)
            
            # Preguntar si quiere abrir el archivo
            if filepath and messagebox.askyesno("Abrir Archivo", 
                                              "¿Desea abrir el archivo exportado?", 
                                              parent=self.window):
                try:
                    os.startfile(filepath)  # Windows
                except:
                    try:
                        import subprocess
                        subprocess.run(['xdg-open', filepath])  # Linux
                    except:
                        try:
                            subprocess.run(['open', filepath])  # macOS
                        except:
                            pass  # Si no puede abrir
    
    def _update_conversion_buttons(self, prospect_data):
        """Actualiza la visibilidad de los botones de conversión según el estado del prospecto"""
        if prospect_data.get("estado") == "Convertido":
            # Mostrar botón de revertir conversión
            self.revert_conversion_btn.pack(fill=tk.X, pady=2)
            
            # Verificar si la conversión es reversible
            es_reversible, _ = self.prospect_service.verificar_conversion_reversible(
                prospect_data["id"]
            )
            
            if es_reversible:
                self.revert_conversion_btn.config(state=tk.NORMAL)
            else:
                self.revert_conversion_btn.config(state=tk.DISABLED)
        else:
            # Ocultar botón de revertir conversión
            self.revert_conversion_btn.pack_forget()
    
    # Propiedades para compatibilidad con ProspectManager
    @property
    def root(self):
        return self.window