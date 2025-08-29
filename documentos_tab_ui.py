import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import subprocess
import datetime

class DocumentosTab(ttk.Frame):
    def __init__(self, parent, app_controller, case_data):
        super().__init__(parent, padding="10")
        self.app_controller = app_controller
        self.case_data = case_data
        self.case_id = case_data.get('id')
        self.create_widgets()
        self.load_case_documents(self.case_data.get('ruta_carpeta', ''))

    def create_widgets(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        ttk.Label(self, text="Carpeta Documentos:").grid(row=0, column=0, pady=(0, 5), sticky=tk.W)
        
        folder_frame = ttk.Frame(self)
        folder_frame.grid(row=1, column=0, sticky=tk.EW, pady=(0, 5))
        folder_frame.columnconfigure(0, weight=1)
        
        self.folder_path_lbl = ttk.Label(folder_frame, text="...", relief=tk.SUNKEN, anchor=tk.W)
        self.folder_path_lbl.grid(row=0, column=0, sticky=tk.EW, padx=(0, 5))
        
        self.select_folder_btn = ttk.Button(folder_frame, text="...", command=self.select_case_folder, width=3)
        self.select_folder_btn.grid(row=0, column=1, sticky=tk.E, padx=(0,5))
        
        self.open_folder_btn = ttk.Button(folder_frame, text="Abrir Carpeta", command=self.open_case_folder, width=12)
        self.open_folder_btn.grid(row=0, column=2, sticky=tk.E)

        ttk.Label(self, text="Archivos y Carpetas:").grid(row=2, column=0, pady=(5, 5), sticky=tk.NW)
        
        documents_tree_frame = ttk.Frame(self)
        documents_tree_frame.grid(row=3, column=0, sticky='nsew')
        documents_tree_frame.columnconfigure(0, weight=1)
        documents_tree_frame.rowconfigure(0, weight=1)
        
        self.document_tree = ttk.Treeview(documents_tree_frame, columns=('Nombre', 'Tamaño', 'Fecha Mod.'), show='headings')
        self.document_tree.heading('Nombre', text='Nombre')
        self.document_tree.heading('Tamaño', text='Tamaño')
        self.document_tree.heading('Fecha Mod.', text='Modificado')
        self.document_tree.column('Nombre', width=250, stretch=True)
        self.document_tree.column('Tamaño', width=100, stretch=tk.NO, anchor=tk.E)
        self.document_tree.column('Fecha Mod.', width=140, stretch=tk.NO)
        
        document_scrollbar = ttk.Scrollbar(documents_tree_frame, orient=tk.VERTICAL, command=self.document_tree.yview)
        self.document_tree.configure(yscrollcommand=document_scrollbar.set)
        document_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.document_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.document_tree.bind("<Double-1>", self.on_document_double_click)

    def load_case_documents(self, folder_path):
        # Utiliza los métodos del app_controller que ya existen
        self.app_controller.clear_document_list_for_tab(self.document_tree)
        self.app_controller.load_case_documents_for_tab(self.document_tree, folder_path, self.case_data)
        
        # Actualizar labels y botones de esta pestaña
        self.folder_path_lbl.config(text=folder_path if folder_path else "Carpeta no asignada")
        self.open_folder_btn.config(state=tk.NORMAL if folder_path and os.path.isdir(folder_path) else tk.DISABLED)

    def select_case_folder(self):
        # Llama a la lógica del controlador principal, pero actualiza su propia UI
        initial_dir = self.case_data.get('ruta_carpeta') or os.path.expanduser("~")
        folder_selected = filedialog.askdirectory(initialdir=initial_dir, title="Seleccionar Carpeta", parent=self)
        if folder_selected:
            if self.app_controller.db_crm.update_case_folder(self.case_id, folder_selected):
                self.case_data['ruta_carpeta'] = folder_selected # Actualizar en memoria local
                self.load_case_documents(folder_selected)
                messagebox.showinfo("Éxito", "Carpeta asignada.", parent=self)
            else:
                messagebox.showerror("Error", "No se pudo guardar la ruta.", parent=self)

    def open_case_folder(self):
        self.app_controller.open_case_folder_from_tab(self.case_data)
        
    def on_document_double_click(self, event):
        self.app_controller.on_document_double_click_from_tab(event, self.document_tree, self.case_id, self.case_data)