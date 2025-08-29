import tkinter as tk
from tkinter import ttk

class DetallesTab(ttk.Frame):
    def __init__(self, parent, app_controller, case_data): # case_data añadido
        super().__init__(parent, padding="10")
        self.app_controller = app_controller
        self.case_data = case_data # Guardar case_data
        self.create_widgets()
        if self.case_data: # Cargar detalles si case_data está disponible
            self.load_details(self.case_data)

    def create_widgets(self):
        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)
        current_row = 0

        ttk.Label(self, text="Carátula:").grid(row=current_row, column=0, sticky=tk.W, pady=2, padx=2)
        self.caratula_lbl = ttk.Label(self, text="", wraplength=500)
        self.caratula_lbl.grid(row=current_row, column=1, columnspan=3, sticky=tk.EW, pady=2, padx=2)
        current_row += 1

        ttk.Label(self, text="Expediente:").grid(row=current_row, column=0, sticky=tk.W, pady=2, padx=2)
        self.expediente_lbl = ttk.Label(self, text="")
        self.expediente_lbl.grid(row=current_row, column=1, columnspan=3, sticky=tk.EW, pady=2, padx=2)
        current_row += 1

        ttk.Label(self, text="Juzgado:").grid(row=current_row, column=0, sticky=tk.W, pady=2, padx=2)
        self.juzgado_lbl = ttk.Label(self, text="", wraplength=300)
        self.juzgado_lbl.grid(row=current_row, column=1, columnspan=3, sticky=tk.EW, pady=2, padx=2)
        current_row += 1

        ttk.Label(self, text="Jurisdicción:").grid(row=current_row, column=0, sticky=tk.W, pady=2, padx=2)
        self.jurisdiccion_lbl = ttk.Label(self, text="", wraplength=300)
        self.jurisdiccion_lbl.grid(row=current_row, column=1, columnspan=3, sticky=tk.EW, pady=2, padx=2)
        current_row += 1

        ttk.Label(self, text="Etapa Procesal:").grid(row=current_row, column=0, sticky=tk.W, pady=2, padx=2)
        self.etapa_lbl = ttk.Label(self, text="")
        self.etapa_lbl.grid(row=current_row, column=1, sticky=tk.EW, pady=2, padx=2)

        ttk.Label(self, text="Etiquetas Caso:").grid(row=current_row, column=2, sticky=tk.W, pady=2, padx=10)
        self.case_detail_tags_lbl = ttk.Label(self, text="")
        self.case_detail_tags_lbl.grid(row=current_row, column=3, sticky=tk.EW, pady=2, padx=2)
        current_row += 1

        ttk.Label(self, text="Notas:").grid(row=current_row, column=0, sticky=tk.NW, pady=2, padx=2)
        notes_frame = ttk.Frame(self)
        notes_frame.grid(row=current_row, column=1, columnspan=3, sticky=tk.NSEW, pady=2, padx=2)
        notes_frame.rowconfigure(0, weight=1)
        notes_frame.columnconfigure(0, weight=1)
        self.notas_text = tk.Text(notes_frame, height=4, wrap=tk.WORD, state=tk.DISABLED)
        self.notas_text.grid(row=0, column=0, sticky='nsew')
        notas_scrollbar = ttk.Scrollbar(notes_frame, orient=tk.VERTICAL, command=self.notas_text.yview)
        notas_scrollbar.grid(row=0, column=1, sticky='ns')
        self.notas_text['yscrollcommand'] = notas_scrollbar.set
        self.rowconfigure(current_row, weight=1)
        current_row += 1

        inactivity_frame = ttk.LabelFrame(self, text="Alarma Inactividad", padding="5")
        inactivity_frame.grid(row=current_row, column=0, columnspan=4, sticky=tk.EW, pady=5, padx=2)
        inactivity_frame.columnconfigure(1, weight=1)
        ttk.Label(inactivity_frame, text="Habilitada:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=1)
        self.inactivity_enabled_lbl = ttk.Label(inactivity_frame, text="")
        self.inactivity_enabled_lbl.grid(row=0, column=1, sticky=tk.W, pady=1)
        ttk.Label(inactivity_frame, text="Umbral Días:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=1)
        self.inactivity_threshold_lbl = ttk.Label(inactivity_frame, text="")
        self.inactivity_threshold_lbl.grid(row=1, column=1, sticky=tk.W, pady=1)
    
    def load_details(self, case_data):
        if not case_data:
            return

        self.caratula_lbl.config(text=case_data.get('caratula', 'N/A'))
        exp = f"{case_data.get('numero_expediente', 'S/N')}/{case_data.get('anio_caratula', 'S/A')}"
        self.expediente_lbl.config(text=exp)
        self.juzgado_lbl.config(text=case_data.get('juzgado', 'N/A'))
        self.jurisdiccion_lbl.config(text=case_data.get('jurisdiccion', 'N/A'))
        self.etapa_lbl.config(text=case_data.get('etapa_procesal', 'N/A'))

        nombres_etiquetas_caso = []
        case_id_for_tags = case_data.get('id')
        if case_id_for_tags:
            etiquetas_obj = self.app_controller.db_crm.get_etiquetas_de_caso(case_id_for_tags)
            nombres_etiquetas_caso = [e['nombre_etiqueta'] for e in etiquetas_obj]
        
        self.case_detail_tags_lbl.config(text=", ".join(nombres_etiquetas_caso).capitalize() if nombres_etiquetas_caso else "Ninguna")

        self.notas_text.config(state=tk.NORMAL)
        self.notas_text.delete('1.0', tk.END)
        notas_valor = case_data.get('notas') or ''
        self.notas_text.insert('1.0', notas_valor)
        self.notas_text.config(state=tk.DISABLED)

        inactivity_enabled = "Sí" if case_data.get('inactivity_enabled') else "No"
        inactivity_threshold = case_data.get('inactivity_threshold_days', 30)
        self.inactivity_enabled_lbl.config(text=inactivity_enabled)
        self.inactivity_threshold_lbl.config(text=str(inactivity_threshold))