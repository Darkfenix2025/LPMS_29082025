#!/usr/bin/env python3
"""
Modelos Escritos Manager - Gestor de Modelos de Escritos Legales
Maneja plantillas de documentos legales que se completan con datos del caso
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from datetime import datetime
import crm_database as db
from docxtpl import DocxTemplate
from docx import Document
import tempfile
import subprocess
import platform


class ModelosEscritosManager:
    """Gestor de modelos de escritos legales con datos del caso"""
    
    def __init__(self):
        self.modelos_dir = "modelos_escritos"
        self.ensure_modelos_directory()
    
    def ensure_modelos_directory(self):
        """Asegura que exista el directorio de modelos de escritos"""
        if not os.path.exists(self.modelos_dir):
            os.makedirs(self.modelos_dir)
        
        # Crear subdirectorios por categoría si no existen
        categories = ["civil", "familia", "laboral", "penal", "comercial", "general", "mediacion"]
        for category in categories:
            category_path = os.path.join(self.modelos_dir, category)
            if not os.path.exists(category_path):
                os.makedirs(category_path)
        
        # Crear archivo README si no existe
        readme_path = os.path.join(self.modelos_dir, "README.md")
        if not os.path.exists(readme_path):
            self._create_readme_file(readme_path)
    
    def _create_readme_file(self, readme_path):
        """Crea un archivo README con instrucciones"""
        readme_content = """# Modelos de Escritos Legales

Este directorio contiene los modelos de escritos legales que se pueden completar automáticamente con datos del caso.

## Estructura de Carpetas

- `civil/` - Modelos para casos civiles
- `familia/` - Modelos para casos de familia
- `laboral/` - Modelos para casos laborales
- `penal/` - Modelos para casos penales
- `comercial/` - Modelos para casos comerciales
- `general/` - Modelos de uso general
- `mediacion/` - Modelos para mediaciones

## Formato de Archivos

Los modelos deben estar en formato `.docx` y pueden usar las siguientes variables:

### Variables del Caso
- `{{numero_expediente}}` - Número de expediente
- `{{anio_caratula}}` - Año de la carátula
- `{{caratula}}` - Carátula completa del caso
- `{{juzgado}}` - Juzgado donde tramita
- `{{jurisdiccion}}` - Jurisdicción
- `{{etapa_procesal}}` - Etapa procesal actual

### Variables del Cliente
- `{{cliente_nombre}}` - Nombre del cliente
- `{{cliente_direccion}}` - Dirección del cliente
- `{{cliente_email}}` - Email del cliente
- `{{cliente_whatsapp}}` - WhatsApp del cliente

### Variables de Fecha
- `{{fecha_hoy}}` - Fecha actual (formato argentino)
- `{{fecha_hoy_largo}}` - Fecha actual en formato largo

### Variables del Abogado
- `{{abogado_nombre}}` - Nombre del abogado
- `{{matricula_nacion}}` - Matrícula nacional
- `{{matricula_pba}}` - Matrícula PBA
- `{{domicilio_procesal}}` - Domicilio procesal

## Ejemplo de Uso

Para crear un modelo, simplemente cree un archivo `.docx` con el contenido deseado y use las variables entre llaves dobles `{{variable}}`.

El sistema reemplazará automáticamente estas variables con los datos reales del caso seleccionado.
"""
        
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
        except Exception as e:
            print(f"Error creando README: {e}")
    
    def get_categories(self):
        """Obtiene las categorías disponibles"""
        categories = []
        if os.path.exists(self.modelos_dir):
            for item in os.listdir(self.modelos_dir):
                item_path = os.path.join(self.modelos_dir, item)
                if os.path.isdir(item_path):
                    categories.append(item)
        return sorted(categories)
    
    def get_modelos_in_category(self, category):
        """Obtiene los modelos de una categoría específica"""
        modelos = []
        category_path = os.path.join(self.modelos_dir, category)
        
        if os.path.exists(category_path):
            for file in os.listdir(category_path):
                if file.endswith('.docx') and not file.startswith('~'):  # Excluir archivos temporales
                    modelo_name = file[:-5]  # Remover .docx
                    modelo_name = modelo_name.replace('_', ' ').title()
                    modelos.append({
                        'name': modelo_name,
                        'file': file,
                        'path': os.path.join(category_path, file)
                    })
        
        return sorted(modelos, key=lambda x: x['name'])
    
    def get_case_data(self, case_id):
        """Obtiene los datos del caso para completar el modelo"""
        try:
            case_data = db.get_case_by_id(case_id)
            if not case_data:
                return None
            
            # Obtener datos del cliente
            client_data = db.get_client_by_id(case_data['cliente_id'])
            
            # Obtener datos del usuario/abogado
            user_data = db.get_datos_usuario()
            
            # Preparar variables para el template
            template_vars = {
                # Datos del caso
                'numero_expediente': case_data.get('numero_expediente', ''),
                'anio_caratula': case_data.get('anio_caratula', ''),
                'caratula': case_data.get('caratula', ''),
                'juzgado': case_data.get('juzgado', ''),
                'jurisdiccion': case_data.get('jurisdiccion', ''),
                'etapa_procesal': case_data.get('etapa_procesal', ''),
                'notas': case_data.get('notas', ''),
                
                # Datos del cliente
                'cliente_nombre': client_data.get('nombre', '') if client_data else '',
                'cliente_direccion': client_data.get('direccion', '') if client_data else '',
                'cliente_email': client_data.get('email', '') if client_data else '',
                'cliente_whatsapp': client_data.get('whatsapp', '') if client_data else '',
                
                # Datos de fecha
                'fecha_hoy': datetime.now().strftime('%d-%m-%Y'),
                'fecha_hoy_largo': datetime.now().strftime('%d de %B de %Y'),
                
                # Datos del abogado
                'abogado_nombre': user_data.get('nombre_abogado', '') if user_data else '',
                'matricula_nacion': user_data.get('matricula_nacion', '') if user_data else '',
                'matricula_pba': user_data.get('matricula_pba', '') if user_data else '',
                'matricula_federal': user_data.get('matricula_federal', '') if user_data else '',
                'domicilio_procesal_caba': user_data.get('domicilio_procesal_caba', '') if user_data else '',
                'domicilio_procesal_pba': user_data.get('domicilio_procesal_pba', '') if user_data else '',
                'telefono_estudio': user_data.get('telefono_estudio', '') if user_data else '',
                'email_estudio': user_data.get('email_estudio', '') if user_data else '',
            }
            
            return template_vars
            
        except Exception as e:
            print(f"Error obteniendo datos del caso {case_id}: {e}")
            return None
    
    def generate_document(self, modelo_path, case_id, output_path=None):
        """Genera un documento completando el modelo con datos del caso"""
        try:
            # Obtener datos del caso
            template_vars = self.get_case_data(case_id)
            if not template_vars:
                raise Exception("No se pudieron obtener los datos del caso")
            
            # Cargar el template
            doc = DocxTemplate(modelo_path)
            
            # Renderizar el documento con las variables
            doc.render(template_vars)
            
            # Determinar ruta de salida
            if not output_path:
                # Crear nombre de archivo basado en el caso
                case_data = db.get_case_by_id(case_id)
                filename = f"{case_data.get('caratula', 'Documento')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                # Limpiar caracteres no válidos para nombres de archivo
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                output_path = os.path.join(tempfile.gettempdir(), filename)
            
            # Guardar el documento
            doc.save(output_path)
            
            return output_path
            
        except Exception as e:
            print(f"Error generando documento: {e}")
            raise
    
    def open_document(self, file_path):
        """Abre un documento con la aplicación predeterminada"""
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
        except Exception as e:
            print(f"Error abriendo documento: {e}")
            raise
    
    def open_modelos_manager_window(self, parent, case_id=None):
        """Abre la ventana de gestión de modelos de escritos"""
        window = tk.Toplevel(parent)
        window.title("Modelos de Escritos Legales")
        window.geometry("1000x700")
        window.transient(parent)
        window.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Información del caso si se proporciona
        if case_id:
            case_data = db.get_case_by_id(case_id)
            if case_data:
                info_frame = ttk.LabelFrame(main_frame, text="Caso Seleccionado", padding="10")
                info_frame.pack(fill=tk.X, pady=(0, 10))
                
                ttk.Label(info_frame, text=f"Carátula: {case_data.get('caratula', 'N/A')}", 
                         font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
                ttk.Label(info_frame, text=f"Expediente: {case_data.get('numero_expediente', 'N/A')}/{case_data.get('anio_caratula', 'N/A')}").pack(anchor=tk.W)
                ttk.Label(info_frame, text=f"Cliente: {case_data.get('nombre_cliente', 'N/A')}").pack(anchor=tk.W)
        
        # Configurar grid
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.columnconfigure(0, weight=0)  # Panel izquierdo
        content_frame.columnconfigure(1, weight=1)  # Panel derecho
        content_frame.rowconfigure(0, weight=1)
        
        # Panel izquierdo - Navegación
        left_frame = ttk.Frame(content_frame)
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
        
        ttk.Button(category_buttons_frame, text="Abrir Carpeta", 
                  command=lambda: self._open_category_folder(category_listbox, categories)).pack(fill=tk.X, pady=2)
        
        # Panel derecho - Modelos
        right_frame = ttk.Frame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Título de modelos
        modelos_title_frame = ttk.Frame(right_frame)
        modelos_title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        modelos_title_frame.columnconfigure(0, weight=1)
        
        self.modelos_title_label = ttk.Label(modelos_title_frame, text="Seleccione una categoría", 
                                            font=("TkDefaultFont", 12, "bold"))
        self.modelos_title_label.grid(row=0, column=0, sticky="w")
        
        # Lista de modelos
        modelos_frame = ttk.Frame(right_frame)
        modelos_frame.grid(row=1, column=0, sticky="nsew")
        modelos_frame.columnconfigure(0, weight=1)
        modelos_frame.rowconfigure(0, weight=1)
        
        self.modelos_listbox = tk.Listbox(modelos_frame)
        self.modelos_listbox.grid(row=0, column=0, sticky="nsew")
        
        modelos_scrollbar = ttk.Scrollbar(modelos_frame, orient=tk.VERTICAL, command=self.modelos_listbox.yview)
        modelos_scrollbar.grid(row=0, column=1, sticky="ns")
        self.modelos_listbox.configure(yscrollcommand=modelos_scrollbar.set)
        
        # Botones de modelos
        modelos_buttons_frame = ttk.Frame(right_frame)
        modelos_buttons_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        
        if case_id:
            ttk.Button(modelos_buttons_frame, text="Generar Documento", 
                      command=lambda: self._generate_document_from_selection(category_listbox, categories, case_id, window)).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(modelos_buttons_frame, text="Abrir Modelo", 
                  command=lambda: self._open_modelo_from_selection(category_listbox, categories)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(modelos_buttons_frame, text="Agregar Modelo", 
                  command=lambda: self._add_new_modelo(category_listbox, categories)).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(modelos_buttons_frame, text="Cerrar", command=window.destroy).pack(side=tk.RIGHT)
        
        # Eventos
        def on_category_select(event):
            selection = category_listbox.curselection()
            if selection:
                category = categories[selection[0]]
                self._load_modelos_for_category(category)
        
        category_listbox.bind("<<ListboxSelect>>", on_category_select)
        
        # Variables de instancia para el diálogo
        self.current_category = None
        self.current_modelos = []
        
        parent.wait_window(window)
    
    def _load_modelos_for_category(self, category):
        """Carga los modelos de una categoría"""
        self.current_category = category
        self.current_modelos = self.get_modelos_in_category(category)
        
        self.modelos_title_label.config(text=f"Modelos - {category.title()}")
        
        # Limpiar lista
        self.modelos_listbox.delete(0, tk.END)
        
        # Cargar modelos
        for modelo in self.current_modelos:
            self.modelos_listbox.insert(tk.END, modelo['name'])
    
    def _open_category_folder(self, category_listbox, categories):
        """Abre la carpeta de la categoría seleccionada"""
        selection = category_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una categoría primero.")
            return
        
        category = categories[selection[0]]
        category_path = os.path.join(self.modelos_dir, category)
        
        try:
            self.open_document(category_path)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")
    
    def _generate_document_from_selection(self, category_listbox, categories, case_id, parent_window):
        """Genera un documento desde el modelo seleccionado"""
        selection = self.modelos_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un modelo para generar.")
            return
        
        modelo = self.current_modelos[selection[0]]
        
        try:
            # Generar el documento
            output_path = self.generate_document(modelo['path'], case_id)
            
            # Preguntar si quiere abrir el documento
            if messagebox.askyesno("Documento Generado", 
                                 f"Documento generado exitosamente.\n\n¿Desea abrirlo ahora?"):
                self.open_document(output_path)
            
            messagebox.showinfo("Éxito", f"Documento guardado en:\n{output_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generando documento:\n{str(e)}")
    
    def _open_modelo_from_selection(self, category_listbox, categories):
        """Abre el modelo seleccionado para edición"""
        selection = self.modelos_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione un modelo para abrir.")
            return
        
        modelo = self.current_modelos[selection[0]]
        
        try:
            self.open_document(modelo['path'])
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el modelo: {e}")
    
    def _add_new_modelo(self, category_listbox, categories):
        """Permite agregar un nuevo modelo"""
        selection = category_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Seleccione una categoría primero.")
            return
        
        category = categories[selection[0]]
        category_path = os.path.join(self.modelos_dir, category)
        
        # Abrir diálogo para seleccionar archivo
        file_path = filedialog.askopenfilename(
            title="Seleccionar Modelo de Escrito",
            filetypes=[("Documentos Word", "*.docx"), ("Todos los archivos", "*.*")]
        )
        
        if file_path:
            try:
                # Copiar archivo a la categoría
                import shutil
                filename = os.path.basename(file_path)
                dest_path = os.path.join(category_path, filename)
                
                if os.path.exists(dest_path):
                    if not messagebox.askyesno("Archivo Existente", 
                                             f"Ya existe un archivo con el nombre '{filename}'.\n¿Desea reemplazarlo?"):
                        return
                
                shutil.copy2(file_path, dest_path)
                messagebox.showinfo("Éxito", f"Modelo agregado a la categoría '{category}'")
                
                # Recargar la lista
                self._load_modelos_for_category(category)
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo agregar el modelo: {e}")


# Instancia global del gestor de modelos de escritos
modelos_escritos_manager = ModelosEscritosManager()