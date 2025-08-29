import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ReportGeneratorWindow(tk.Toplevel):
    def __init__(self, app_controller):
        super().__init__(app_controller.root)
        self.app_controller = app_controller
        self.db = app_controller.db_crm

        self.title("Generador de Reportes")
        self.geometry("700x500")
        self.minsize(650, 400)

        # Bloquea la ventana principal hasta cerrar esta
        self.transient(app_controller.root)
        self.grab_set()

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)

        # Filtros
        ttk.Label(frame, text="Fecha desde (YYYY-MM-DD):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.from_date = tk.StringVar()
        ttk.Entry(frame, textvariable=self.from_date, width=15).grid(row=0, column=1, sticky=tk.W)

        ttk.Label(frame, text="Fecha hasta (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.to_date = tk.StringVar()
        ttk.Entry(frame, textvariable=self.to_date, width=15).grid(row=1, column=1, sticky=tk.W)

        ttk.Label(frame, text="Palabra clave:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.keyword = tk.StringVar()
        ttk.Entry(frame, textvariable=self.keyword, width=30).grid(row=2, column=1, sticky=tk.W)

        # Botones
        ttk.Button(frame, text="Generar Reporte", command=self.generate_report).grid(row=3, column=0, columnspan=2, pady=10)

        # Resultados
        self.result_text = tk.Text(frame, wrap=tk.WORD, height=20)
        self.result_text.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, command=self.result_text.yview)
        scrollbar.grid(row=4, column=2, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)

        frame.rowconfigure(4, weight=1)
        frame.columnconfigure(1, weight=1)

    def generate_report(self):
        try:
            from_date = self.from_date.get().strip()
            to_date = self.to_date.get().strip()
            keyword = self.keyword.get().strip()

            # Validación de fechas
            if from_date:
                datetime.strptime(from_date, "%Y-%m-%d")
            if to_date:
                datetime.strptime(to_date, "%Y-%m-%d")

            # Obtener datos de la base
            cases = self.db.get_all_cases()

            # Filtrar
            filtered = []
            for case in cases:
                fecha = case.get("fecha", "")
                caratula = case.get("caratula", "")
                descripcion = case.get("descripcion", "")

                if from_date and fecha < from_date:
                    continue
                if to_date and fecha > to_date:
                    continue
                if keyword and keyword.lower() not in (caratula.lower() + descripcion.lower()):
                    continue

                filtered.append(case)

            # Mostrar resultados
            self.result_text.delete("1.0", tk.END)
            if filtered:
                for case in filtered:
                    self.result_text.insert(tk.END, f"ID: {case['id']} | Fecha: {case['fecha']} | Carátula: {case['caratula']}\n")
            else:
                self.result_text.insert(tk.END, "No se encontraron casos con esos criterios.\n")

        except ValueError:
            messagebox.showerror("Error", "Formato de fecha inválido. Use YYYY-MM-DD.", parent=self)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema generando el reporte:\n{e}", parent=self)
