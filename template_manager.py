#!/usr/bin/python3
"""
Template Manager - Gestor de Plantillas Legales Modulares
Maneja plantillas en archivos .txt externos organizadas por categorías
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import json


class TemplateManager:
    """Gestor de plantillas legales modulares"""
    
    def __init__(self):
        self.templates_dir = "templates"
        self.ensure_templates_directory()
    
    def ensure_templates_directory(self):
        """Asegura que exista el directorio de plantillas"""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
        
        # Crear subdirectorios por categoría si no existen
        categories = ["civil", "familia", "laboral", "penal", "comercial", "general"]
        for category in categories:
            category_path = os.path.join(self.templates_dir, category)
            if not os.path.exists(category_path):
                os.makedirs(category_path)
    
    def get_categories(self):
        """Obtiene las categorías disponibles"""
        categories = []
        if os.path.exists(self.templates_dir):
            for item in os.listdir(self.templates_dir):
                item_path = os.path.join(self.templates_dir, item)
                if os.path.isdir(item_path):
                    categories.append(item)
        return sorted(categories)
    
    def get_templates_in_category(self, category):
        """Obtiene las plantillas de una categoría específica"""
        templates = []
        category_path = os.path.join(self.templates_dir, category)
        
        if os.path.exists(category_path):
            for file in os.listdir(category_path):
                if file.endswith('.txt'):
                    template_name = file[:-4]  # Remover .txt
                    template_name = template_name.replace('_', ' ').title()
                    templates.append({
                        'name': template_name,
                        'file': file,
                        'path': os.path.join(category_path, file)
                    })
        
        return sorted(templates, key=lambda x: x['name'])
    
    def load_template(self, template_path):
        """Carga el contenido de una plantilla"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error cargando plantilla {template_path}: {e}")
            return None
    
    def save_template(self, category, filename, content):
        """Guarda una plantilla"""
        try:
            category_path = os.path.join(self.templates_dir, category)
            if not os.path.exists(category_path):
                os.makedirs(category_path)
            
            if not filename.endswith('.txt'):
                filename += '.txt'
            
            template_path = os.path.join(category_path, filename)
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Error guardando plantilla: {e}")
            return False
    
    def delete_template(self, template_path):
        """Elimina una plantilla"""
        try:
            os.remove(template_path)
            return True
        except Exception as e:
            print(f"Error eliminando plantilla: {e}")
            return False
    
    def open_template_manager_window(self, parent, callback=None):
        """Abre la ventana de gestión de plantillas"""
        window = tk.Toplevel(parent)
        window.title("Gestor de Plantillas Legales")
        window.geometry("900x600")
        window.transient(parent)
        window.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid
        main_frame.columnconfigure(0, weight=0)  # Panel izquierdo
        main_frame.columnconfigure(1, weight=1)  # Panel derecho
        main_frame.rowconfigure(0, weight=1)
        
        # Panel izquierdo - Navegación
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        
        # Título
        ttk.Label(left_frame, text="Categorías", font=("TkDefaultFont", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        
        # Lista de categorías
        categories_frame = ttk.Frame(left_frame)
        categories_frame.grid(row=1, column=0, sticky="nsew")
        categories_frame.columnconfigure(0, weight=1)
        categories_frame.rowconfigure(0, weight=1)
        
        category_listbox = tk.Listbox(categories_frame, width=20)
        category_listbox.grid(row=0, column=0, sticky="nsew")
        
        category_scrollbar = ttk.Scrollbar(categories_frame, orient=tk.VERTICAL, command=category_listbox.yview)
        category_scrollbar.grid(row=0, column=1, sticky="ns")
        category_listbox.configure(yscrollcommand=category_scrollbar.set)
        
        # Cargar categorías
        categories = self.get_categories()
        for category in categories:
            category_listbox.insert(tk.END, category.title())
        
        # Botones de categoría
        category_buttons_frame = ttk.Frame(left_frame)
        category_buttons_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(category_buttons_frame, text="Nueva Categoría", 
                  command=lambda: self._create_new_category(category_listbox)).pack(fill=tk.X, pady=2)
        
        # Panel derecho - Plantillas
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Título de plantillas
        templates_title_frame = ttk.Frame(right_frame)
        templates_title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        templates_title_frame.columnconfigure(0, weight=1)
        
        self.templates_title_label = ttk.Label(templates_title_frame, text="Seleccione una categoría", 
                                              font=("TkDefaultFont", 12, "bold"))
        self.templates_title_label.grid(row=0, column=0, sticky="w")
        
        # Lista de plantillas
        templates_frame = ttk.Frame(right_frame)
        templates_frame.grid(row=1, column=0, sticky="nsew")
        templates_frame.columnconfigure(0, weight=1)
        templates_frame.rowconfigure(0, weight=1)
        
        self.templates_listbox = tk.Listbox(templates_frame)
        self.templates_listbox.grid(row=0, column=0, sticky="nsew")
        
        templates_scrollbar = ttk.Scrollbar(templates_frame, orient=tk.VERTICAL, command=self.templates_listbox.yview)
        templates_scrollbar.grid(row=0, column=1, sticky="ns")
        self.templates_listbox.configure(yscrollcommand=templates_scrollbar.set)
        
        # Botones de plantillas
        templates_buttons_frame = ttk.Frame(right_frame)
        templates_buttons_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        ttk.Button(templates_buttons_frame, text="Nueva Plantilla", 
                  command=lambda: self._create_new_template(category_listbox, self.templates_listbox)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(templates_buttons_frame, text="Editar", 
                  command=lambda: self._edit_template(category_listbox, self.templates_listbox)).pack(side=tk.LEFT, padx=5)
        ttk.Button(templates_buttons_frame, text="Eliminar", 
                  command=lambda: self._delete_template(category_listbox, self.templates_listbox)).pack(side=tk.LEFT, padx=5)
        
        if callback:
            ttk.Button(templates_buttons_frame, text="Usar Plantilla", 
                      command=lambda: self._use_template(category_listbox, self.templates_listbox, callback, window)).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(templates_buttons_frame, text="Cerrar", command=window.destroy).pack(side=tk.RIGHT)
        
        # Eventos
        def on_category_select(event):
            selection = category_listbox.curselection()
            if selection:
                category = categories[selection[0]]
                self._load_templates_for_category(category)
        
        category_listbox.bind("<<ListboxSelect>>", on_category_select)
        
        # Variables de instancia para el diálogo
        self.current_category = None
        self.current_templates = []
        
        parent.wait_window(window)
    
    def _load_templates_for_category(self, category):
        """Carga las plantillas de una categoría"""
        self.current_category = category
        self.current_templates = self.get_templates_in_category(category)
        
        self.templates_title_label.config(text=f"Plantillas - {category.title()}")
        
        # Limpiar lista
        self.templates_listbox.delete(0, tk.END)
        
        # Cargar plantillas
        for template in self.current_templates:
            self.templates_listbox.insert(tk.END, template['name'])
    
    def _create_new_category(self, category_listbox):
        """Crea una nueva categoría"""
        from tkinter import simpledialog
        
        new_category = simpledialog.askstring("Nueva Categoría", "Nombre de la nueva categoría:")
        if new_category:
            # Limpiar nombre
            new_category = new_category.lower().replace(' ', '_')
            category_path = os.path.join(self.templates_dir, new_category)
            
            try:
                os.makedirs(category_path, exist_ok=True)
                
                # Actualizar lista
                category_listbox.insert(tk.END, new_category.title())
                messagebox.showinfo("Éxito", f"Categoría '{new_category}' creada correctamente.")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la categoría: {e}")
    
    def _create_new_template(self, category_listbox, templates_listbox):
        """Crea una nueva plantilla"""
        if not self.current_category:
            messagebox.showwarning("Advertencia", "Seleccione una categoría primero.")
            return
        
        self._open_template_editor(None, is_new=True)
    
    def _edit_template(self, category_listbox, templates_listbox):
        """Edita una plantilla existente"""
        selection = templates_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una plantilla para editar.")
            return
        
        template = self.current_templates[selection[0]]
        self._open_template_editor(template)
    
    def _delete_template(self, category_listbox, templates_listbox):
        """Elimina una plantilla"""
        selection = templates_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una plantilla para eliminar.")
            return
        
        template = self.current_templates[selection[0]]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar la plantilla '{template['name']}'?"):
            if self.delete_template(template['path']):
                messagebox.showinfo("Éxito", "Plantilla eliminada correctamente.")
                self._load_templates_for_category(self.current_category)
            else:
                messagebox.showerror("Error", "No se pudo eliminar la plantilla.")
    
    def _use_template(self, category_listbox, templates_listbox, callback, window):
        """Usa una plantilla seleccionada"""
        selection = templates_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una plantilla para usar.")
            return
        
        template = self.current_templates[selection[0]]
        content = self.load_template(template['path'])
        
        if content and callback:
            callback(content)
            window.destroy()
    
    def _open_template_editor(self, template=None, is_new=False):
        """Abre el editor de plantillas"""
        editor_window = tk.Toplevel()
        editor_window.title("Editor de Plantilla" if not is_new else "Nueva Plantilla")
        editor_window.geometry("700x500")
        editor_window.transient()
        editor_window.grab_set()
        
        frame = ttk.Frame(editor_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)
        
        # Nombre de la plantilla
        ttk.Label(frame, text="Nombre de la plantilla:").grid(row=0, column=0, sticky="w", pady=(0, 5))
        name_var = tk.StringVar()
        if template:
            name_var.set(template['name'])
        name_entry = ttk.Entry(frame, textvariable=name_var, width=50)
        name_entry.grid(row=0, column=1, sticky="ew", pady=(0, 5), padx=(10, 0))
        
        # Categoría
        ttk.Label(frame, text="Categoría:").grid(row=1, column=0, sticky="w", pady=(0, 10))
        category_var = tk.StringVar(value=self.current_category if self.current_category else "")
        category_combo = ttk.Combobox(frame, textvariable=category_var, values=self.get_categories(), state="readonly")
        category_combo.grid(row=1, column=1, sticky="ew", pady=(0, 10), padx=(10, 0))
        
        # Contenido
        ttk.Label(frame, text="Contenido de la plantilla:").grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        content_frame = ttk.Frame(frame)
        content_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        content_text = scrolledtext.ScrolledText(content_frame, wrap=tk.WORD)
        content_text.grid(row=0, column=0, sticky="nsew")
        
        if template:
            content = self.load_template(template['path'])
            if content:
                content_text.insert("1.0", content)
        
        # Botones
        buttons_frame = ttk.Frame(frame)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        def save_template():
            name = name_var.get().strip()
            category = category_var.get().strip()
            content = content_text.get("1.0", tk.END).strip()
            
            if not name:
                messagebox.showwarning("Advertencia", "Ingrese un nombre para la plantilla.")
                return
            
            if not category:
                messagebox.showwarning("Advertencia", "Seleccione una categoría.")
                return
            
            if not content:
                messagebox.showwarning("Advertencia", "Ingrese el contenido de la plantilla.")
                return
            
            # Convertir nombre a filename
            filename = name.lower().replace(' ', '_') + '.txt'
            
            if self.save_template(category, filename, content):
                messagebox.showinfo("Éxito", "Plantilla guardada correctamente.")
                editor_window.destroy()
                
                # Actualizar lista si estamos en la misma categoría
                if category == self.current_category:
                    self._load_templates_for_category(category)
            else:
                messagebox.showerror("Error", "No se pudo guardar la plantilla.")
        
        ttk.Button(buttons_frame, text="Guardar", command=save_template).pack(side=tk.LEFT)
        ttk.Button(buttons_frame, text="Cancelar", command=editor_window.destroy).pack(side=tk.LEFT, padx=(10, 0))
        
        name_entry.focus_set()


# Instancia global del gestor de plantillas
template_manager = TemplateManager()