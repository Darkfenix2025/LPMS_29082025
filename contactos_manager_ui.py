import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Toplevel
import crm_database as db
import datetime
import re
import webbrowser
import urllib.parse


def open_contactos_manager(root):
    """Función para abrir el gestor de contactos desde main_app.py"""
    ContactosManagerWindow(root)


class ContactosManagerWindow(tk.Toplevel):
    """Ventana principal para gestión centralizada de contactos"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Gestor de Contactos - LPMS Legal")
        self.geometry("1000x700")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Variables de estado
        self.selected_contact_id = None
        self.contacts_data = []
        self.filtered_contacts = []

        # Configurar la interfaz
        self._setup_ui()

        # Cargar datos iniciales
        self._load_contacts()

        # Centrar ventana
        self._center_window()

    def _setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Frame de búsqueda
        search_frame = ttk.LabelFrame(main_frame, text="Buscar Contactos", padding="5")
        search_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self._on_search_change)

        ttk.Button(search_frame, text="Limpiar", command=self._clear_search).pack(side=tk.RIGHT)

        # Frame del Treeview
        tree_frame = ttk.LabelFrame(main_frame, text="Lista de Contactos", padding="5")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Crear Treeview
        columns = ("ID", "Nombre", "Tipo", "CUIT/DNI", "Contacto Principal")
        self.contacts_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")

        # Configurar columnas
        self.contacts_tree.heading("ID", text="ID")
        self.contacts_tree.heading("Nombre", text="Nombre Completo")
        self.contacts_tree.heading("Tipo", text="Tipo")
        self.contacts_tree.heading("CUIT/DNI", text="CUIT/DNI")
        self.contacts_tree.heading("Contacto Principal", text="Email/Teléfono")

        self.contacts_tree.column("ID", width=50, stretch=False)
        self.contacts_tree.column("Nombre", width=200, stretch=True)
        self.contacts_tree.column("Tipo", width=80, stretch=False)
        self.contacts_tree.column("CUIT/DNI", width=120, stretch=False)
        self.contacts_tree.column("Contacto Principal", width=150, stretch=True)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.contacts_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.contacts_tree.xview)
        self.contacts_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Empaquetar Treeview y scrollbars
        self.contacts_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        tree_frame.rowconfigure(0, weight=1)
        tree_frame.rowconfigure(1, weight=0)  # Configure row for horizontal scrollbar
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.columnconfigure(1, weight=0)  # Configure column for vertical scrollbar

        # Bindings
        self.contacts_tree.bind('<<TreeviewSelect>>', self._on_contact_select)
        self.contacts_tree.bind('<Double-1>', self._on_contact_double_click)
        self.contacts_tree.bind('<Button-3>', self._show_context_menu)

        # Frame de botones de acción
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(buttons_frame, text="Agregar Nuevo Contacto", command=self._add_contact).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Editar Contacto Seleccionado", command=self._edit_contact).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(buttons_frame, text="Eliminar Contacto Seleccionado", command=self._delete_contact).pack(side=tk.LEFT, padx=(0, 5))

        # Frame de información del contacto seleccionado
        self.info_frame = ttk.LabelFrame(main_frame, text="Información del Contacto Seleccionado", padding="10")
        self.info_frame.pack(fill=tk.X)

        self.info_text = tk.Text(self.info_frame, height=8, wrap=tk.WORD, state=tk.DISABLED)
        info_scroll = ttk.Scrollbar(self.info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scroll.set)

        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        info_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _center_window(self):
        """Centra la ventana en la pantalla"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _load_contacts(self):
        """Carga todos los contactos desde la base de datos"""
        try:
            self.contacts_data = db.get_contactos()
            self.filtered_contacts = self.contacts_data.copy()
            self._populate_treeview()
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar contactos: {str(e)}", parent=self)

    def _populate_treeview(self):
        """Llena el Treeview con los datos de contactos"""
        # Limpiar Treeview
        for item in self.contacts_tree.get_children():
            self.contacts_tree.delete(item)

        # Agregar contactos
        for contact in self.filtered_contacts:
            contact_id = contact.get('id', '')
            nombre = contact.get('nombre_completo', '')
            es_persona_juridica = contact.get('es_persona_juridica', False)
            tipo = "Empresa" if es_persona_juridica else "Persona"

            # Determinar CUIT/DNI
            cuit_dni = ""
            if contact.get('cuit'):
                cuit_dni = f"CUIT: {contact['cuit']}"
            elif contact.get('dni'):
                cuit_dni = f"DNI: {contact['dni']}"

            # Determinar contacto principal (email y teléfono)
            contacto_principal = ""
            email = (contact.get('email') or '').strip()
            telefono = (contact.get('telefono') or '').strip()

            # Mostrar ambos campos si están disponibles
            if email and telefono:
                contacto_principal = f"{email} / {telefono}"
            elif email:
                contacto_principal = email
            elif telefono:
                contacto_principal = telefono
            else:
                contacto_principal = "Sin contacto"

            self.contacts_tree.insert("", tk.END, values=(
                contact_id, nombre, tipo, cuit_dni, contacto_principal
            ), iid=str(contact_id))

    def _on_search_change(self, event=None):
        """Maneja cambios en el campo de búsqueda"""
        search_term = self.search_var.get().strip().lower()

        if not search_term:
            self.filtered_contacts = self.contacts_data.copy()
        else:
            self.filtered_contacts = []
            for contact in self.contacts_data:
                # Buscar en nombre, email, teléfono, CUIT, DNI
                searchable_text = f"{contact.get('nombre_completo', '')} {(contact.get('email') or '')} {(contact.get('telefono') or '')} {(contact.get('cuit') or '')} {(contact.get('dni') or '')}".lower()
                if search_term in searchable_text:
                    self.filtered_contacts.append(contact)

        self._populate_treeview()

    def _clear_search(self):
        """Limpia el campo de búsqueda"""
        self.search_var.set("")
        self._on_search_change()

    def _on_contact_select(self, event=None):
        """Maneja selección de contacto en el Treeview"""
        selection = self.contacts_tree.selection()
        if selection:
            self.selected_contact_id = int(selection[0])
            self._show_contact_info()
        else:
            self.selected_contact_id = None
            self._clear_contact_info()

    def _on_contact_double_click(self, event=None):
        """Maneja doble clic en un contacto (abre ficha completa)"""
        if self.selected_contact_id:
            self._show_contact_details()

    def _show_context_menu(self, event=None):
        """Muestra menú contextual al hacer clic derecho"""
        if not self.selected_contact_id:
            return

        # Crear menú contextual
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Ver Ficha Completa...", command=self._show_contact_details)
        context_menu.add_separator()
        context_menu.add_command(label="Enviar Email...", command=self._send_email_to_contact)
        context_menu.add_command(label="Enviar WhatsApp...", command=self._send_whatsapp_to_contact)

        # Mostrar menú en posición del cursor
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def _show_contact_info(self):
        """Muestra información básica del contacto seleccionado"""
        if not self.selected_contact_id:
            self._clear_contact_info()
            return

        try:
            contact = db.get_contacto_by_id(self.selected_contact_id)
            if not contact:
                self._clear_contact_info()
                return

            info_lines = []
            info_lines.append(f"Nombre: {contact.get('nombre_completo', 'N/A')}")
            info_lines.append(f"Tipo: {'Empresa' if contact.get('es_persona_juridica') else 'Persona'}")

            if contact.get('dni'):
                info_lines.append(f"DNI: {contact['dni']}")
            if contact.get('cuit'):
                info_lines.append(f"CUIT: {contact['cuit']}")

            info_lines.append(f"Domicilio Real: {contact.get('domicilio_real', 'N/A')}")
            info_lines.append(f"Domicilio Legal: {contact.get('domicilio_legal', 'N/A')}")
            info_lines.append(f"Email: {contact.get('email', 'N/A')}")
            info_lines.append(f"Teléfono: {contact.get('telefono', 'N/A')}")
            info_lines.append(f"Notas: {contact.get('notas_generales', 'N/A')}")

            # Formatear fecha de creación
            created_at = contact.get('created_at')
            if created_at:
                try:
                    fecha = datetime.datetime.fromtimestamp(created_at)
                    info_lines.append(f"Creado: {fecha.strftime('%d/%m/%Y %H:%M')}")
                except:
                    info_lines.append(f"Creado: {created_at}")

            info_text = "\n".join(info_lines)

            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            self.info_text.config(state=tk.DISABLED)

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar información del contacto: {str(e)}", parent=self)

    def _clear_contact_info(self):
        """Limpia el área de información del contacto"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, "Seleccione un contacto para ver su información...")
        self.info_text.config(state=tk.DISABLED)

    def _show_contact_details(self):
        """Muestra la ficha completa del contacto en una nueva ventana"""
        if not self.selected_contact_id:
            return

        try:
            contact = db.get_contacto_by_id(self.selected_contact_id)
            if not contact:
                messagebox.showerror("Error", "No se pudo cargar la información del contacto.", parent=self)
                return

            # Crear ventana de detalles
            details_window = tk.Toplevel(self)
            details_window.title(f"Ficha Completa - {contact.get('nombre_completo', 'Contacto')}")
            details_window.geometry("600x500")
            details_window.transient(self)
            details_window.grab_set()

            # Frame principal
            frame = ttk.Frame(details_window, padding="20")
            frame.pack(fill=tk.BOTH, expand=True)

            # Información del contacto
            info_text = tk.Text(frame, wrap=tk.WORD, height=20)
            info_scroll = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=info_text.yview)
            info_text.configure(yscrollcommand=info_scroll.set)

            # Formatear información completa
            lines = []
            lines.append(f"NOMBRE COMPLETO: {contact.get('nombre_completo', 'N/A')}")
            lines.append(f"TIPO: {'Empresa' if contact.get('es_persona_juridica') else 'Persona'}")
            lines.append("")

            if contact.get('dni'):
                lines.append(f"DNI: {contact['dni']}")
            if contact.get('cuit'):
                lines.append(f"CUIT: {contact['cuit']}")
            lines.append("")

            lines.append(f"DOMICILIO REAL: {contact.get('domicilio_real', 'N/A')}")
            lines.append(f"DOMICILIO LEGAL: {contact.get('domicilio_legal', 'N/A')}")
            lines.append("")

            lines.append(f"EMAIL: {contact.get('email', 'N/A')}")
            lines.append(f"TELÉFONO: {contact.get('telefono', 'N/A')}")
            lines.append("")

            lines.append("NOTAS GENERALES:")
            lines.append(contact.get('notas_generales', 'Sin notas'))
            lines.append("")

            # Formatear fecha de creación
            created_at = contact.get('created_at')
            if created_at:
                try:
                    fecha = datetime.datetime.fromtimestamp(created_at)
                    lines.append(f"FECHA DE CREACIÓN: {fecha.strftime('%d/%m/%Y %H:%M')}")
                except:
                    lines.append(f"FECHA DE CREACIÓN: {created_at}")

            info_text.insert(1.0, "\n".join(lines))
            info_text.config(state=tk.DISABLED)

            # Botones
            buttons_frame = ttk.Frame(frame)
            buttons_frame.pack(fill=tk.X, pady=(10, 0))

            ttk.Button(buttons_frame, text="Enviar Email", command=lambda: self._send_email_to_contact(contact['id'])).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="Enviar WhatsApp", command=lambda: self._send_whatsapp_to_contact(contact['id'])).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="Editar", command=lambda: self._edit_contact(contact['id'])).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons_frame, text="Cerrar", command=details_window.destroy).pack(side=tk.RIGHT)

            # Layout
            info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            info_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar detalles del contacto: {str(e)}", parent=self)

    def _add_contact(self):
        """Abre diálogo para agregar nuevo contacto"""
        self._open_contact_dialog()

    def _edit_contact(self, contact_id=None):
        """Abre diálogo para editar contacto existente"""
        if contact_id is None:
            contact_id = self.selected_contact_id
        if not contact_id:
            messagebox.showwarning("Advertencia", "Seleccione un contacto para editar.", parent=self)
            return

        self._open_contact_dialog(contact_id)

    def _delete_contact(self):
        """Elimina el contacto seleccionado"""
        if not self.selected_contact_id:
            messagebox.showwarning("Advertencia", "Seleccione un contacto para eliminar.", parent=self)
            return

        try:
            contact = db.get_contacto_by_id(self.selected_contact_id)
            if not contact:
                messagebox.showerror("Error", "No se pudo encontrar el contacto.", parent=self)
                return

            nombre = contact.get('nombre_completo', 'Contacto')

            if messagebox.askyesno("Confirmar Eliminación",
                                 f"¿Está seguro de que desea eliminar el contacto:\n\n{nombre}\n\nEsta acción no se puede deshacer.",
                                 parent=self, icon="warning"):

                success = db.delete_contacto(self.selected_contact_id)
                if success:
                    messagebox.showinfo("Éxito", f"Contacto '{nombre}' eliminado correctamente.", parent=self)
                    self._load_contacts()
                    self.selected_contact_id = None
                    self._clear_contact_info()
                else:
                    messagebox.showerror("Error", "No se pudo eliminar el contacto.", parent=self)

        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar contacto: {str(e)}", parent=self)

    def _open_contact_dialog(self, contact_id=None):
        """Abre diálogo para crear/editar contacto"""
        is_edit = contact_id is not None
        contact_data = {}

        if is_edit:
            contact_data = db.get_contacto_by_id(contact_id)
            if not contact_data:
                messagebox.showerror("Error", "No se pudo cargar la información del contacto.", parent=self)
                return

        # Crear ventana de diálogo
        dialog = tk.Toplevel(self)
        dialog.title("Editar Contacto" if is_edit else "Nuevo Contacto")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        dialog.resizable(True, True)

        # Frame principal
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # Variables
        nombre_var = tk.StringVar(value=contact_data.get('nombre_completo', ''))
        es_persona_juridica_var = tk.BooleanVar(value=contact_data.get('es_persona_juridica', False))
        dni_var = tk.StringVar(value=contact_data.get('dni', ''))
        cuit_var = tk.StringVar(value=contact_data.get('cuit', ''))
        domicilio_real_var = tk.StringVar(value=contact_data.get('domicilio_real', ''))
        domicilio_legal_var = tk.StringVar(value=contact_data.get('domicilio_legal', ''))
        email_var = tk.StringVar(value=contact_data.get('email', ''))
        telefono_var = tk.StringVar(value=contact_data.get('telefono', ''))
        notas_var = tk.StringVar(value=contact_data.get('notas_generales', ''))

        row_idx = 0

        # Nombre completo
        ttk.Label(frame, text="*Nombre Completo:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=nombre_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3)
        row_idx += 1

        # Tipo (Persona/Empresa)
        ttk.Label(frame, text="Tipo:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        tipo_frame = ttk.Frame(frame)
        tipo_frame.grid(row=row_idx, column=1, sticky=tk.W, pady=3)
        ttk.Radiobutton(tipo_frame, text="Persona", variable=es_persona_juridica_var, value=False).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(tipo_frame, text="Empresa", variable=es_persona_juridica_var, value=True).pack(side=tk.LEFT)
        row_idx += 1

        # DNI
        ttk.Label(frame, text="DNI:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=dni_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3)
        row_idx += 1

        # CUIT
        ttk.Label(frame, text="CUIT:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=cuit_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3)
        row_idx += 1

        # Domicilio Real
        ttk.Label(frame, text="Domicilio Real:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=domicilio_real_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3)
        row_idx += 1

        # Domicilio Legal
        ttk.Label(frame, text="Domicilio Legal:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=domicilio_legal_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3)
        row_idx += 1

        # Email
        ttk.Label(frame, text="Email:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=email_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3)
        row_idx += 1

        # Teléfono
        ttk.Label(frame, text="Teléfono:").grid(row=row_idx, column=0, sticky=tk.W, pady=3)
        ttk.Entry(frame, textvariable=telefono_var).grid(row=row_idx, column=1, sticky=tk.EW, pady=3)
        row_idx += 1

        # Notas
        ttk.Label(frame, text="Notas Generales:").grid(row=row_idx, column=0, sticky=tk.NW, pady=3)
        notas_text = tk.Text(frame, height=4, wrap=tk.WORD)
        notas_text.grid(row=row_idx, column=1, sticky=tk.NSEW, pady=3)
        notas_text.insert(1.0, contact_data.get('notas_generales', ''))
        frame.rowconfigure(row_idx, weight=1)
        row_idx += 1

        # Botones
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=row_idx, column=0, columnspan=2, pady=20, sticky=tk.E)

        def save_contact():
            # Validar campos obligatorios
            if not nombre_var.get().strip():
                messagebox.showerror("Validación", "El nombre completo es obligatorio.", parent=dialog)
                return

            # Preparar datos
            contact_data = {
                'nombre_completo': nombre_var.get().strip(),
                'es_persona_juridica': es_persona_juridica_var.get(),
                'dni': dni_var.get().strip(),
                'cuit': cuit_var.get().strip(),
                'domicilio_real': domicilio_real_var.get().strip(),
                'domicilio_legal': domicilio_legal_var.get().strip(),
                'email': email_var.get().strip(),
                'telefono': telefono_var.get().strip(),
                'notas_generales': notas_text.get(1.0, tk.END).strip()
            }

            try:
                if is_edit:
                    success = db.update_contacto(contact_id, **contact_data)
                    msg = "actualizado"
                else:
                    new_id = db.add_contacto(**contact_data)
                    success = new_id is not None
                    msg = "creado"

                if success:
                    messagebox.showinfo("Éxito", f"Contacto {msg} correctamente.", parent=self)
                    dialog.destroy()
                    self._load_contacts()
                else:
                    messagebox.showerror("Error", f"No se pudo {msg} el contacto.", parent=dialog)

            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar contacto: {str(e)}", parent=dialog)

        ttk.Button(buttons_frame, text="Guardar", command=save_contact).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Centrar diálogo
        dialog.update_idletasks()
        dialog_width = dialog.winfo_width()
        dialog_height = dialog.winfo_height()
        parent_x = self.winfo_x()
        parent_y = self.winfo_y()
        parent_width = self.winfo_width()
        parent_height = self.winfo_height()
        x_pos = parent_x + (parent_width - dialog_width) // 2
        y_pos = parent_y + (parent_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x_pos}+{y_pos}")

        nombre_var.get()  # Focus on first field

    def _send_email_to_contact(self, contact_id=None):
        """Envía email al contacto seleccionado"""
        if contact_id is None:
            contact_id = self.selected_contact_id
        if not contact_id:
            messagebox.showwarning("Advertencia", "Seleccione un contacto.", parent=self)
            return

        try:
            contact = db.get_contacto_by_id(contact_id)
            if not contact:
                messagebox.showerror("Error", "No se pudo cargar la información del contacto.", parent=self)
                return

            email = contact.get('email', '').strip()
            if not email:
                messagebox.showwarning("Advertencia", "El contacto no tiene email registrado.", parent=self)
                return

            # Abrir cliente de correo con mailto:
            subject = f"Contacto desde LPMS Legal - {contact.get('nombre_completo', 'Contacto')}"
            body = f"Estimado {contact.get('nombre_completo', 'Contacto')},\n\n"
            mailto_url = f"mailto:{email}?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"

            webbrowser.open(mailto_url)
            messagebox.showinfo("Email", f"Abriendo cliente de correo para: {email}", parent=self)

        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar email: {str(e)}", parent=self)

    def _send_whatsapp_to_contact(self, contact_id=None):
        """Envía mensaje de WhatsApp al contacto seleccionado"""
        if contact_id is None:
            contact_id = self.selected_contact_id
        if not contact_id:
            messagebox.showwarning("Advertencia", "Seleccione un contacto.", parent=self)
            return

        try:
            contact = db.get_contacto_by_id(contact_id)
            if not contact:
                messagebox.showerror("Error", "No se pudo cargar la información del contacto.", parent=self)
                return

            telefono = (contact.get('telefono') or '').strip()
            if not telefono:
                messagebox.showwarning("Advertencia", "El contacto no tiene teléfono registrado.", parent=self)
                return

            # Limpiar número de teléfono (remover espacios, guiones, etc.)
            telefono_limpio = re.sub(r'[^\d+]', '', telefono)

            # Validar que el número tenga al menos 6 dígitos
            if len(telefono_limpio) < 6:
                messagebox.showwarning("Advertencia", "El número de teléfono parece ser demasiado corto.", parent=self)
                return

            # Si no tiene código de país, asumir Argentina (+54)
            if not telefono_limpio.startswith('+'):
                if telefono_limpio.startswith('0'):
                    telefono_limpio = '+54' + telefono_limpio[1:]
                else:
                    telefono_limpio = '+54' + telefono_limpio

            # Crear mensaje predeterminado
            nombre = (contact.get('nombre_completo') or 'Contacto').strip()
            mensaje = f"Hola {nombre}, te contacto desde LPMS Legal."

            # Abrir WhatsApp Web con wa.me
            whatsapp_url = f"https://wa.me/{telefono_limpio}?text={urllib.parse.quote(mensaje, safe='')}"
            try:
                webbrowser.open(whatsapp_url)
            except Exception as url_error:
                messagebox.showerror("Error", f"Error al abrir WhatsApp: {str(url_error)}", parent=self)
                return

            messagebox.showinfo("WhatsApp", f"Abriendo WhatsApp para: {telefono}", parent=self)

        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar WhatsApp: {str(e)}", parent=self)


def get_contactos():
    """Función auxiliar para obtener todos los contactos (para compatibilidad)"""
    return db.get_contactos()