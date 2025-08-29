"""
Client Dialog Manager - Refactorizado desde main_app.py
Maneja toda la lógica relacionada con la interfaz de clientes
"""

import tkinter as tk
from tkinter import ttk, messagebox
import crm_database as db


class ClientManager:
    """Clase que maneja toda la lógica de clientes"""
    
    def __init__(self, app_controller):
        self.app_controller = app_controller
        self.db = db
    
    def validar_datos_cliente(self, datos: dict) -> tuple[bool, str]:
        """
        Valida los datos de un cliente antes de guardar.
        
        Args:
            datos (dict): Diccionario con los datos del cliente
            
        Returns:
            tuple[bool, str]: (es_valido, mensaje_error)
        """
        # Validar nombre obligatorio
        nombre = datos.get('nombre', '').strip()
        if not nombre:
            return False, "El nombre del cliente no puede estar vacío."
        
        # Validar longitud del nombre
        if len(nombre) > 255:
            return False, "El nombre del cliente es demasiado largo (máximo 255 caracteres)."
        
        # Validar dirección si se proporciona
        direccion = datos.get('direccion', '').strip()
        if direccion and len(direccion) > 500:
            return False, "La dirección es demasiado larga (máximo 500 caracteres)."
        
        # Validar email si se proporciona
        email = datos.get('email', '').strip()
        if email:
            if len(email) > 255:
                return False, "El email es demasiado largo (máximo 255 caracteres)."
            # Validación básica de formato de email
            if '@' not in email or '.' not in email.split('@')[-1]:
                return False, "El formato del email no es válido."
        
        # Validar WhatsApp si se proporciona
        whatsapp = datos.get('whatsapp', '').strip()
        if whatsapp and len(whatsapp) > 50:
            return False, "El número de WhatsApp es demasiado largo (máximo 50 caracteres)."
        
        # Validar etiquetas si se proporcionan
        etiquetas = datos.get('etiquetas', '').strip()
        if etiquetas and len(etiquetas) > 1000:
            return False, "Las etiquetas son demasiado largas (máximo 1000 caracteres)."
        
        return True, ""
    
    def open_client_dialog(self, client_id=None):
        """Abre el diálogo para agregar o editar un cliente"""
        is_edit = client_id is not None
        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title("Editar Cliente" if is_edit else "Agregar Nuevo Cliente")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Variables de Tkinter
        name_var = tk.StringVar()
        address_var = tk.StringVar()
        email_var = tk.StringVar()
        whatsapp_var = tk.StringVar()
        etiquetas_var = tk.StringVar()

        if is_edit:
            client_data = self.db.get_client_by_id(client_id)
            if client_data:
                name_var.set(client_data.get('nombre', ''))
                address_var.set(client_data.get('direccion', ''))
                email_var.set(client_data.get('email', ''))
                whatsapp_var.set(client_data.get('whatsapp', ''))
                
                # Cargar etiquetas existentes para este cliente
                etiquetas_actuales_obj = self.db.get_etiquetas_de_cliente(client_id)
                etiquetas_actuales_nombres = [e['nombre_etiqueta'] for e in etiquetas_actuales_obj]
                etiquetas_var.set(", ".join(etiquetas_actuales_nombres))
            else:
                messagebox.showerror("Error", "No se pudieron cargar los datos del cliente.", parent=dialog)
                dialog.destroy()
                return

        # Layout de los widgets
        row_idx = 0
        ttk.Label(frame, text="Nombre Completo:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
        name_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Dirección:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        address_entry = ttk.Entry(frame, textvariable=address_var, width=40)
        address_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Email:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        email_entry = ttk.Entry(frame, textvariable=email_var, width=40)
        email_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="WhatsApp:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        whatsapp_entry = ttk.Entry(frame, textvariable=whatsapp_var, width=40)
        whatsapp_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # Campo para etiquetas
        ttk.Label(frame, text="Etiquetas:").grid(row=row_idx, column=0, sticky=tk.W, pady=(10,3), padx=5)
        ttk.Label(frame, text="(separadas por coma)").grid(row=row_idx, column=1, sticky=tk.E, pady=(10,3), padx=0)
        row_idx += 1
        etiquetas_entry = ttk.Entry(frame, textvariable=etiquetas_var, width=40)
        etiquetas_entry.grid(row=row_idx, column=0, columnspan=2, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        frame.columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=15)
        
        # Comando del botón Guardar
        save_command = lambda: self.save_client(
            client_id, 
            name_var.get(), 
            address_var.get(), 
            email_var.get(), 
            whatsapp_var.get(),
            etiquetas_var.get(),
            dialog
        )
        ttk.Button(button_frame, text="Guardar", command=save_command).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        name_entry.focus_set()
        self.app_controller.root.wait_window(dialog)

    def save_client(self, client_id, nombre, direccion, email, whatsapp, etiquetas_str, dialog):
        """Guarda los datos del cliente en la base de datos"""
        
        # Validar datos usando función centralizada
        datos_cliente = {
            'nombre': nombre,
            'direccion': direccion,
            'email': email,
            'whatsapp': whatsapp,
            'etiquetas': etiquetas_str
        }
        
        es_valido, mensaje_error = self.validar_datos_cliente(datos_cliente)
        if not es_valido:
            messagebox.showwarning("Advertencia", mensaje_error, parent=dialog)
            return

        success_main_data = False
        saved_client_id = client_id

        if client_id is None:  # Nuevo cliente
            new_id = self.db.add_client(nombre.strip(), direccion.strip(), email.strip(), whatsapp.strip())
            if new_id:
                success_main_data = True
                saved_client_id = new_id
                msg_op = "agregado"
            else:
                msg_op = "falló al agregar"
        else:  # Editar cliente
            if self.db.update_client(client_id, nombre.strip(), direccion.strip(), email.strip(), whatsapp.strip()):
                success_main_data = True
                msg_op = "actualizado"
                # Actualizar datos del cliente seleccionado si es el mismo
                if self.app_controller.selected_client and self.app_controller.selected_client['id'] == client_id:
                    self.app_controller.selected_client = self.db.get_client_by_id(client_id)
                    self.display_client_details(self.app_controller.selected_client)
            else:
                msg_op = "falló al actualizar"

        if success_main_data:
            # Lógica para guardar etiquetas
            if saved_client_id is not None:
                self._save_client_tags(saved_client_id, etiquetas_str)

            messagebox.showinfo("Éxito", f"Cliente {msg_op} con éxito. Etiquetas actualizadas.", parent=self.app_controller.root)
            dialog.destroy()
            self.load_clients()
        else:
            messagebox.showerror("Error", f"No se pudo guardar la información principal del cliente.", parent=dialog)

    def _save_client_tags(self, client_id, etiquetas_str):
        """Guarda las etiquetas del cliente"""
        # Obtener los nombres de las etiquetas ingresadas por el usuario
        nombres_etiquetas_nuevas = [tag.strip().lower() for tag in etiquetas_str.split(',') if tag.strip()]
        
        # Obtener las etiquetas actualmente asignadas al cliente desde la BD
        etiquetas_actuales_obj_db = self.db.get_etiquetas_de_cliente(client_id)
        nombres_etiquetas_actuales_db = {e['nombre_etiqueta'].lower() for e in etiquetas_actuales_obj_db}

        # Determinar qué etiquetas añadir y cuáles quitar
        ids_etiquetas_a_asignar = set()
        for nombre_tag_nuevo in nombres_etiquetas_nuevas:
            tag_id = self.db.add_etiqueta(nombre_tag_nuevo)
            if tag_id:
                ids_etiquetas_a_asignar.add(tag_id)
        
        etiquetas_ids_actuales_db = {e['id_etiqueta'] for e in etiquetas_actuales_obj_db}

        # Etiquetas a asignar (nuevas o que ya estaban y deben permanecer)
        for tag_id_to_assign in ids_etiquetas_a_asignar:
            self.db.asignar_etiqueta_a_cliente(client_id, tag_id_to_assign)

        # Etiquetas a quitar (estaban en BD pero no en la nueva lista del usuario)
        ids_etiquetas_a_quitar = etiquetas_ids_actuales_db - ids_etiquetas_a_asignar
        for tag_id_to_remove in ids_etiquetas_a_quitar:
            self.db.quitar_etiqueta_de_cliente(client_id, tag_id_to_remove)

    def delete_client(self):
        """Elimina el cliente seleccionado"""
        if not self.app_controller.selected_client:
            messagebox.showwarning("Advertencia", "Selecciona un cliente.")
            return
        
        client_id = self.app_controller.selected_client['id']
        client_name = self.app_controller.selected_client.get('nombre', f'ID {client_id}')
        
        if messagebox.askyesno("Confirmar", 
                              f"¿Eliminar cliente '{client_name}' y TODOS sus casos, actividades y audiencias asociadas?", 
                              parent=self.app_controller.root, icon='warning'):
            if self.db.delete_client(client_id):
                messagebox.showinfo("Éxito", "Cliente eliminado.", parent=self.app_controller.root)
                self.load_clients()
                self.app_controller.actualizar_lista_audiencias()
                self.app_controller.marcar_dias_audiencias_calendario()
            else:
                messagebox.showerror("Error", "No se pudo eliminar el cliente.", parent=self.app_controller.root)

    def load_clients(self):
        """Carga la lista de clientes en el TreeView"""
        # Limpiar lista actual
        for i in self.app_controller.client_tree.get_children():
            self.app_controller.client_tree.delete(i)
        
        clients = self.db.get_clients()
        for client in clients:
            # Obtener etiquetas del cliente
            etiquetas_obj = self.db.get_etiquetas_de_cliente(client['id'])
            etiquetas_nombres = [e['nombre_etiqueta'] for e in etiquetas_obj]
            etiquetas_str = ", ".join(etiquetas_nombres) if etiquetas_nombres else ""
            
            # Insertar en el TreeView
            self.app_controller.client_tree.insert("", tk.END, 
                                                  values=(client['id'], client['nombre']), 
                                                  iid=str(client['id']))
        
        # Limpiar selección y detalles
        self.app_controller.selected_client = None
        self.clear_client_details()
        self.disable_client_buttons()
        self.app_controller.case_manager.clear_case_list()
        self.app_controller.update_add_audiencia_button_state()

    def on_client_select(self, event):
        """Maneja la selección de un cliente en el TreeView"""
        selected_items = self.app_controller.client_tree.selection()
        if selected_items:
            try:
                client_id = int(selected_items[0])
                client_data = self.db.get_client_by_id(client_id)
                if client_data:
                    self.app_controller.selected_client = client_data
                    self.display_client_details(client_data)
                    self.enable_client_buttons()

                    self.app_controller.case_manager.load_cases_by_client(client_id)
                else:
                    print(f"Error: No se encontró cliente con ID {client_id}")
                    self.app_controller.selected_client = None
                    self.clear_client_details()
                    self.disable_client_buttons()
            except (ValueError, IndexError) as e:
                print(f"Error seleccionando cliente: {e}")
                self.app_controller.selected_client = None
                self.clear_client_details()
                self.disable_client_buttons()
        else:
            self.app_controller.selected_client = None
            self.clear_client_details()
            self.disable_client_buttons()
            # Si no hay cliente seleccionado, también debemos limpiar la lista de casos
            self.app_controller.case_manager.clear_case_list()
        
        self.app_controller.update_add_audiencia_button_state()

    def display_client_details(self, client_data):
        """Muestra los detalles del cliente seleccionado"""
        if client_data:
            self.app_controller.client_detail_name_lbl.config(text=client_data.get("nombre", "N/A"))
            self.app_controller.client_detail_address_lbl.config(text=client_data.get("direccion", "N/A"))
            self.app_controller.client_detail_email_lbl.config(text=client_data.get("email", "N/A"))
            self.app_controller.client_detail_whatsapp_lbl.config(text=client_data.get("whatsapp", "N/A"))
            
            # Mostrar etiquetas
            etiquetas_obj = self.db.get_etiquetas_de_cliente(client_data['id'])
            etiquetas_nombres = [e['nombre_etiqueta'] for e in etiquetas_obj]
            etiquetas_str = ", ".join(etiquetas_nombres) if etiquetas_nombres else "Sin etiquetas"
            self.app_controller.client_detail_tags_lbl.config(text=etiquetas_str)
        else:
            self.clear_client_details()

    def clear_client_details(self):
        """Limpia los detalles del cliente"""
        self.app_controller.client_detail_name_lbl.config(text="")
        self.app_controller.client_detail_address_lbl.config(text="")
        self.app_controller.client_detail_email_lbl.config(text="")
        self.app_controller.client_detail_whatsapp_lbl.config(text="")
        self.app_controller.client_detail_tags_lbl.config(text="")

    def enable_client_buttons(self):
        """Habilita los botones de cliente"""
        self.app_controller.edit_client_btn.config(state=tk.NORMAL)
        self.app_controller.delete_client_btn.config(state=tk.NORMAL)

    def disable_client_buttons(self):
        """Deshabilita los botones de cliente"""
        self.app_controller.edit_client_btn.config(state=tk.DISABLED)
        self.app_controller.delete_client_btn.config(state=tk.DISABLED)
    
    def convert_prospect_to_client(self, prospect_data):
        """Convierte un prospecto a cliente abriendo el diálogo pre-rellenado"""
        if not prospect_data:
            messagebox.showerror("Error", "No se proporcionaron datos del prospecto.")
            return
        
        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title("Convertir Prospecto a Cliente")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.resizable(False, False)
        
        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Agregar etiqueta informativa
        info_label = ttk.Label(frame, text=f"Convirtiendo prospecto: {prospect_data['nombre']}", 
                              font=("TkDefaultFont", 10, "bold"))
        info_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        # Variables de Tkinter pre-rellenadas con datos del prospecto
        name_var = tk.StringVar(value=prospect_data.get('nombre', ''))
        address_var = tk.StringVar()
        email_var = tk.StringVar()
        whatsapp_var = tk.StringVar()
        etiquetas_var = tk.StringVar()
        
        # Intentar extraer email y teléfono del campo contacto
        contacto = prospect_data.get('contacto', '')
        if contacto:
            # Si el contacto contiene @, probablemente es un email
            if '@' in contacto:
                email_var.set(contacto)
            else:
                # Si no, probablemente es un teléfono
                whatsapp_var.set(contacto)
        
        # Layout de los widgets
        row_idx = 1
        ttk.Label(frame, text="Nombre Completo:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        name_entry = ttk.Entry(frame, textvariable=name_var, width=40)
        name_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Dirección:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        address_entry = ttk.Entry(frame, textvariable=address_var, width=40)
        address_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="Email:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        email_entry = ttk.Entry(frame, textvariable=email_var, width=40)
        email_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        ttk.Label(frame, text="WhatsApp:").grid(row=row_idx, column=0, sticky=tk.W, pady=3, padx=5)
        whatsapp_entry = ttk.Entry(frame, textvariable=whatsapp_var, width=40)
        whatsapp_entry.grid(row=row_idx, column=1, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        # Campo para etiquetas
        ttk.Label(frame, text="Etiquetas:").grid(row=row_idx, column=0, sticky=tk.W, pady=(10,3), padx=5)
        ttk.Label(frame, text="(separadas por coma)").grid(row=row_idx, column=1, sticky=tk.E, pady=(10,3), padx=0)
        row_idx += 1
        etiquetas_entry = ttk.Entry(frame, textvariable=etiquetas_var, width=40)
        etiquetas_entry.grid(row=row_idx, column=0, columnspan=2, sticky=tk.EW, pady=3, padx=5)
        row_idx += 1

        frame.columnconfigure(1, weight=1)
        
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row_idx, column=0, columnspan=2, pady=15)
        
        def save_converted_client():
            nombre = name_var.get().strip()
            direccion = address_var.get().strip()
            email = email_var.get().strip()
            whatsapp = whatsapp_var.get().strip()
            etiquetas_str = etiquetas_var.get().strip()
            
            # Validar datos usando función centralizada
            datos_cliente = {
                'nombre': nombre,
                'direccion': direccion,
                'email': email,
                'whatsapp': whatsapp,
                'etiquetas': etiquetas_str
            }
            
            es_valido, mensaje_error = self.validar_datos_cliente(datos_cliente)
            if not es_valido:
                messagebox.showwarning("Advertencia", mensaje_error, parent=dialog)
                return
            
            # Crear el cliente
            new_client_id = self.db.add_client(nombre, direccion, email, whatsapp)
            if new_client_id:
                # Guardar etiquetas si las hay
                if etiquetas_str:
                    self._save_client_tags(new_client_id, etiquetas_str)
                
                # Marcar el prospecto como convertido
                success = self.db.marcar_prospecto_como_convertido(prospect_data['id'], new_client_id)
                
                if success:
                    # Guardar análisis de IA como notas del cliente si existen
                    self._save_prospect_analysis_to_client(prospect_data['id'], new_client_id)
                    
                    messagebox.showinfo("Éxito", 
                                      f"Prospecto convertido a cliente exitosamente.\n\n"
                                      f"Cliente ID: {new_client_id}\n"
                                      f"Nombre: {nombre}", 
                                      parent=self.app_controller.root)
                    dialog.destroy()
                    
                    # Recargar listas
                    self.load_clients()
                    if hasattr(self.app_controller, 'prospect_manager'):
                        self.app_controller.prospect_manager.load_prospects()
                else:
                    messagebox.showwarning("Advertencia", 
                                         "Cliente creado pero no se pudo actualizar el estado del prospecto.", 
                                         parent=dialog)
            else:
                messagebox.showerror("Error", "No se pudo crear el cliente.", parent=dialog)
        
        ttk.Button(button_frame, text="Convertir a Cliente", command=save_converted_client).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

        # Enfocar el campo de dirección ya que el nombre ya está rellenado
        address_entry.focus_set()
        self.app_controller.root.wait_window(dialog)
    
    def _save_prospect_analysis_to_client(self, prospect_id, client_id):
        """Guarda el análisis de IA de las consultas del prospecto como información del cliente"""
        try:
            # Obtener todas las consultas del prospecto
            consultas = self.db.get_consultas_by_prospecto_id(prospect_id)
            
            if not consultas:
                return
            
            # Crear un resumen de todas las consultas y análisis
            analysis_summary = "=== ANÁLISIS DE CONSULTAS INICIALES (PROSPECTO) ===\n\n"
            
            for i, consulta in enumerate(consultas, 1):
                analysis_summary += f"CONSULTA {i} - Fecha: {consulta.get('fecha_consulta', 'N/A')}\n"
                analysis_summary += "-" * 50 + "\n"
                
                if consulta.get('relato_original_cliente'):
                    analysis_summary += "RELATO ORIGINAL:\n"
                    analysis_summary += consulta['relato_original_cliente'] + "\n\n"
                
                if consulta.get('hechos_reformulados_ia'):
                    analysis_summary += "ANÁLISIS IA:\n"
                    analysis_summary += consulta['hechos_reformulados_ia'] + "\n\n"
                
                if consulta.get('encuadre_legal_preliminar'):
                    analysis_summary += "ENCUADRE LEGAL PRELIMINAR:\n"
                    analysis_summary += consulta['encuadre_legal_preliminar'] + "\n\n"
                
                analysis_summary += "=" * 60 + "\n\n"
            
            # Crear un archivo de texto con el análisis
            import os
            import datetime
            
            # Crear directorio si no existe
            analysis_dir = "client_analysis"
            if not os.path.exists(analysis_dir):
                os.makedirs(analysis_dir)
            
            # Nombre del archivo
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"client_{client_id}_prospect_analysis_{timestamp}.txt"
            filepath = os.path.join(analysis_dir, filename)
            
            # Guardar archivo
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(analysis_summary)
            
            print(f"Análisis de prospecto guardado en: {filepath}")
            
        except Exception as e:
            print(f"Error guardando análisis de prospecto: {e}")
            # No mostrar error al usuario, es una funcionalidad adicional


# Funciones de compatibilidad para mantener la interfaz existente
''' def open_client_dialog(app_controller, client_id=None):
    """Función de compatibilidad - usa la nueva clase ClientManager"""
    if not hasattr(app_controller, 'client_manager'):
        app_controller.client_manager = ClientManager(app_controller)
    app_controller.client_manager.open_client_dialog(client_id)

def save_client(app_controller, client_id, nombre, direccion, email, whatsapp, etiquetas_str, dialog):
    """Función de compatibilidad - usa la nueva clase ClientManager"""
    if not hasattr(app_controller, 'client_manager'):
        app_controller.client_manager = ClientManager(app_controller)
    app_controller.client_manager.save_client(client_id, nombre, direccion, email, whatsapp, etiquetas_str, dialog)
'''