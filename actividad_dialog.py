import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import datetime

class ActividadDialog(tk.Toplevel):
    def __init__(self, parent, app_controller, caso_id, actividad_id=None):
        super().__init__(parent)
        self.parent = parent
        self.app_controller = app_controller
        self.caso_id = caso_id
        self.actividad_id = actividad_id
        self.db_crm = self.app_controller.db_crm

        self.title("Gestión de Actividad")
        self.transient(parent)
        self.grab_set()
        self.resizable(False, False)

        self.create_widgets()
        if self.actividad_id:
            self.load_actividad_data()

    def create_widgets(self):
        frame = ttk.Frame(self, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Tipo de Actividad:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.tipo_actividad_var = tk.StringVar()
        self.tipo_actividad_entry = ttk.Entry(frame, textvariable=self.tipo_actividad_var, width=40)
        self.tipo_actividad_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)

        ttk.Label(frame, text="Descripción:").grid(row=1, column=0, sticky=tk.NW, pady=5)
        self.descripcion_text = tk.Text(frame, width=40, height=10, wrap=tk.WORD)
        self.descripcion_text.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(frame, text="Referencia Documento:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.referencia_doc_var = tk.StringVar()
        self.referencia_doc_entry = ttk.Entry(frame, textvariable=self.referencia_doc_var, width=40)
        self.referencia_doc_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=3, column=1, sticky=tk.E, pady=10)

        save_button = ttk.Button(button_frame, text="Guardar", command=self.save_actividad)
        save_button.pack(side=tk.LEFT, padx=5)

        cancel_button = ttk.Button(button_frame, text="Cancelar", command=self.destroy)
        cancel_button.pack(side=tk.LEFT)

    def load_actividad_data(self):
        actividad = self.db_crm.get_actividad_by_id(self.actividad_id)
        if actividad:
            self.tipo_actividad_var.set(actividad.get("tipo_actividad", ""))
            self.descripcion_text.insert(tk.END, actividad.get("descripcion", ""))
            self.referencia_doc_var.set(actividad.get("referencia_documento", ""))

    def save_actividad(self):
        tipo_actividad = self.tipo_actividad_var.get()
        descripcion = self.descripcion_text.get("1.0", tk.END).strip()
        referencia_doc = self.referencia_doc_var.get()

        if not tipo_actividad or not descripcion:
            messagebox.showerror("Error", "Tipo de actividad y descripción son obligatorios.", parent=self)
            return

        fecha_hora = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if self.actividad_id:
            success = self.db_crm.update_actividad_caso(
                self.actividad_id, tipo_actividad, descripcion, referencia_doc
            )
        else:
            success = self.db_crm.add_actividad_caso(
                self.caso_id, fecha_hora, tipo_actividad, descripcion, "Usuario", referencia_doc
            )

        if success:
            messagebox.showinfo("Éxito", "Actividad guardada correctamente.", parent=self)
            self.app_controller.refresh_case_window(self.caso_id)
            self.destroy()
        else:
            messagebox.showerror("Error", "No se pudo guardar la actividad.", parent=self)
