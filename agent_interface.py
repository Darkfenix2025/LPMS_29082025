"""
Agent Interface - Interfaz para el Agente Inteligente de Generación de Acuerdos
Permite al usuario interactuar con el agente IA para generar acuerdos de mediación
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from agent_core import AgentCore
import crm_database as db
import os

class AgentInterface:
    """Interfaz gráfica para el Agente Inteligente de Acuerdos"""

    def __init__(self, parent=None, case_id=None, case_caratula=None):
        self.parent = parent
        self.agent = None
        self.current_case_id = None
        self.preselected_case_id = case_id
        self.preselected_case_caratula = case_caratula

        # Crear ventana principal
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        title_suffix = f" - {case_caratula}" if case_caratula else ""
        self.root.title(f"Agente IA - Base de Datos y Generación de Acuerdos{title_suffix}")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._create_widgets()
        self._initialize_agent()

    def _create_widgets(self):
        """Crear todos los widgets de la interfaz"""

        # Frame superior - Panel de casos con búsqueda
        case_frame = ttk.LabelFrame(self.root, text="Base de Datos de Casos", padding="10")
        case_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        case_frame.columnconfigure(0, weight=1)
        case_frame.rowconfigure(1, weight=1)

        # Panel de búsqueda
        search_frame = ttk.Frame(case_frame)
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        search_frame.columnconfigure(1, weight=1)

        ttk.Label(search_frame, text="Buscar:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        self.search_entry.bind("<KeyRelease>", self._on_search_change)

        ttk.Button(search_frame, text="Limpiar", command=self._clear_search).grid(row=0, column=2, padx=(0, 5))
        ttk.Button(search_frame, text="Recargar", command=self._load_cases).grid(row=0, column=3)

        # Treeview para casos
        tree_frame = ttk.Frame(case_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        # Crear Treeview con scrollbars
        columns = ("ID", "Expediente", "Caratula", "Cliente", "Estado")
        self.case_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse", height=8)

        # Configurar columnas
        self.case_tree.heading("ID", text="ID")
        self.case_tree.heading("Expediente", text="N° Expediente")
        self.case_tree.heading("Caratula", text="Carátula")
        self.case_tree.heading("Cliente", text="Cliente")
        self.case_tree.heading("Estado", text="Estado")

        self.case_tree.column("ID", width=50, stretch=False)
        self.case_tree.column("Expediente", width=120, stretch=False)
        self.case_tree.column("Caratula", width=200, stretch=True)
        self.case_tree.column("Cliente", width=120, stretch=False)
        self.case_tree.column("Estado", width=80, stretch=False)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.case_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.case_tree.xview)
        self.case_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid del treeview y scrollbars
        self.case_tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")

        # Bindings
        self.case_tree.bind("<<TreeviewSelect>>", self._on_case_selected)
        self.case_tree.bind("<Double-1>", self._on_case_double_click)

        # Información del caso seleccionado
        info_frame = ttk.LabelFrame(case_frame, text="Caso Seleccionado", padding="5")
        info_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        info_frame.columnconfigure(0, weight=1)

        self.case_info_text = tk.Text(info_frame, height=3, wrap=tk.WORD, state=tk.DISABLED)
        info_scroll = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.case_info_text.yview)
        self.case_info_text.configure(yscrollcommand=info_scroll.set)

        self.case_info_text.grid(row=0, column=0, sticky="ew")
        info_scroll.grid(row=0, column=1, sticky="ns")

        # Frame principal - Chat con el agente
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Área de chat
        chat_frame = ttk.LabelFrame(main_frame, text="Conversación con el Agente IA", padding="5")
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)

        self.chat_text = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=20)
        self.chat_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chat_text.config(state=tk.DISABLED)

        # Frame de entrada
        input_frame = ttk.LabelFrame(main_frame, text="Escriba su consulta al Agente IA", padding="5")
        input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.input_text = tk.Text(input_frame, height=4, wrap=tk.WORD)
        self.input_text.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

        # Frame de botones
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(button_frame, text="Enviar Consulta", command=self._send_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpiar Chat", command=self._clear_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar", command=self._close).pack(side=tk.RIGHT, padx=5)

        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo para recibir consultas...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Configurar expansión
        self.root.rowconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)

        # Cargar casos iniciales
        self._load_cases()

        # Mensaje de bienvenida
        welcome_message = "¡Hola! Soy tu asistente inteligente para generación de acuerdos de mediación.\n\n"
        if self.preselected_case_caratula:
            welcome_message += f"📋 Caso pre-seleccionado: {self.preselected_case_caratula}\n\n"

        welcome_message += "Ahora tengo acceso directo a tu base de datos de casos y múltiples herramientas:\n\n"
        welcome_message += "🔍 FUNCIONES DE BASE DE DATOS:\n"
        welcome_message += "• Ver todos tus casos ordenados alfabéticamente\n"
        welcome_message += "• Buscar casos por carátula, expediente o cliente\n"
        welcome_message += "• Acceder automáticamente a todos los datos del expediente\n\n"
        welcome_message += "📄 HERRAMIENTAS DE GENERACIÓN:\n"
        welcome_message += "• Generar acuerdos usando templates personalizables\n"
        welcome_message += "• Crear acuerdos con IA avanzada y análisis de documentos\n"
        welcome_message += "• Generar documentos Word profesionales automáticamente\n\n"
        welcome_message += "Ejemplos de consultas:\n"
        welcome_message += "• 'Genera un acuerdo usando template para el caso seleccionado'\n"
        welcome_message += "• 'Crea acuerdo de divorcio con IA para el caso actual'\n"
        welcome_message += "• 'Necesito un acuerdo laboral con monto de $75,000'\n"
        welcome_message += "• 'Genera acuerdo comercial con representante legal'\n\n"

        if self.preselected_case_caratula:
            welcome_message += f"✅ Ya tienes seleccionado el caso '{self.preselected_case_caratula}'. ¡Puedes empezar a escribir tu consulta!\n\n"
        else:
            welcome_message += "Selecciona un caso de la lista y escribe tu consulta."

        self._add_message("Agente IA", welcome_message)

    def _initialize_agent(self):
        """Inicializar el agente inteligente"""
        try:
            self.status_var.set("Inicializando agente IA...")
            self.root.update()

            # Crear instancia del agente
            self.agent = AgentCore()

            self.status_var.set("Agente IA inicializado correctamente")
            self._add_message("Sistema", "Agente IA inicializado correctamente")

        except Exception as e:
            error_msg = f"Error inicializando agente: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.root)
            self._add_message("Error", error_msg)

    def _load_cases(self):
        """Cargar lista de casos disponibles en el treeview"""
        try:
            # Limpiar treeview
            for item in self.case_tree.get_children():
                self.case_tree.delete(item)

            # Debug: Mostrar que estamos intentando cargar casos
            print("[DEBUG] Intentando cargar casos desde la base de datos...")
            self.status_var.set("Cargando casos...")

            # Obtener todos los casos - intentar diferentes métodos
            cases = None
            try:
                # Método 1: Obtener todos los casos
                cases = db.get_cases_by_client(None)
                print(f"[DEBUG] Método 1 - get_cases_by_client(None): {len(cases) if cases else 0} casos")
            except Exception as e1:
                print(f"[DEBUG] Error en método 1: {e1}")
                try:
                    # Método 2: Obtener casos sin filtro de cliente
                    cases = db.get_all_cases() if hasattr(db, 'get_all_cases') else None
                    print(f"[DEBUG] Método 2 - get_all_cases(): {len(cases) if cases else 0} casos")
                except Exception as e2:
                    print(f"[DEBUG] Error en método 2: {e2}")
                    try:
                        # Método 3: Usar una consulta directa
                        import sqlite3
                        conn = sqlite3.connect('crm_database.db')
                        cursor = conn.cursor()
                        cursor.execute("SELECT * FROM casos")
                        cases_data = cursor.fetchall()
                        conn.close()

                        # Convertir a formato de diccionario
                        if cases_data:
                            cases = []
                            for case_row in cases_data:
                                case_dict = {
                                    'id': case_row[0],
                                    'numero_expediente': case_row[2] or '',
                                    'caratula': case_row[3] or 'Sin carátula',
                                    'cliente_id': case_row[1],
                                    'juzgado': case_row[4] or '',
                                    'jurisdiccion': case_row[5] or '',
                                    'anio_caratula': case_row[6] or '',
                                    'notas': case_row[7] or ''
                                }
                                cases.append(case_dict)
                        print(f"[DEBUG] Método 3 - Consulta directa: {len(cases) if cases else 0} casos")
                    except Exception as e3:
                        print(f"[DEBUG] Error en método 3: {e3}")

            if not cases:
                # Mostrar mensaje cuando no hay casos
                self.case_tree.insert("", "end", values=("No hay casos disponibles", "", "", "", ""))
                self.status_var.set("No hay casos disponibles en la base de datos")
                print("[DEBUG] No se encontraron casos en la base de datos")
                return

            # Ordenar casos alfabéticamente por carátula
            cases_sorted = sorted(cases, key=lambda x: x.get('caratula', '').lower())
            print(f"[DEBUG] Casos ordenados: {len(cases_sorted)}")

            # Guardar datos de casos
            self.case_data = {}
            self.all_cases = cases_sorted

            # Agregar casos al treeview
            for case in cases_sorted:
                case_id = case['id']
                numero_exp = case.get('numero_expediente', '')
                caratula = case.get('caratula', 'Sin carátula')
                cliente_id = case.get('cliente_id')

                # Obtener nombre del cliente
                cliente_nombre = "Sin cliente"
                if cliente_id:
                    try:
                        cliente = db.get_client_by_id(cliente_id)
                        if cliente:
                            cliente_nombre = cliente.get('nombre', 'Sin nombre')
                    except Exception as e:
                        print(f"[DEBUG] Error obteniendo cliente {cliente_id}: {e}")
                        cliente_nombre = f"Cliente ID {cliente_id}"

                # Estado del caso (simplificado)
                estado = "Activo"

                # Insertar en treeview
                self.case_tree.insert("", "end", iid=str(case_id), values=(
                    case_id,
                    numero_exp,
                    caratula,
                    cliente_nombre,
                    estado
                ))

                # Guardar datos del caso
                self.case_data[str(case_id)] = case

            self.status_var.set(f"{len(cases_sorted)} casos cargados correctamente")
            print(f"[DEBUG] {len(cases_sorted)} casos agregados al treeview")

            # Seleccionar caso pre-seleccionado o primer caso si existe
            if cases_sorted:
                item_to_select = None

                # Si hay un caso pre-seleccionado, buscarlo
                if self.preselected_case_id:
                    for item in self.case_tree.get_children():
                        if self.case_tree.item(item, 'values')[0] == str(self.preselected_case_id):
                            item_to_select = item
                            break

                # Si no se encontró el caso pre-seleccionado o no hay pre-selección, seleccionar el primero
                if not item_to_select:
                    item_to_select = self.case_tree.get_children()[0]

                if item_to_select:
                    self.case_tree.selection_set(item_to_select)
                    self._on_case_selected()

        except Exception as e:
            error_msg = f"Error cargando casos: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.status_var.set("Error cargando casos - revisar logs")
            messagebox.showerror("Error", error_msg, parent=self.root)

    def _on_case_selected(self, event=None):
        """Manejar selección de caso"""
        selection = self.case_tree.selection()
        if selection:
            case_id = selection[0]
            if case_id in self.case_data:
                case = self.case_data[case_id]
                self.current_case_id = case['id']

                # Mostrar información del caso seleccionado
                self._update_case_info(case)

                # Notificar al agente
                numero_exp = case.get('numero_expediente', 'Sin expediente')
                caratula = case.get('caratula', 'Sin carátula')
                self._add_message("Caso Seleccionado", f"Caso actual: {numero_exp} - {caratula}")
                self.status_var.set(f"Caso seleccionado: ID {self.current_case_id}")

    def _on_case_double_click(self, event=None):
        """Manejar doble clic en caso - mostrar detalles completos"""
        selection = self.case_tree.selection()
        if selection:
            case_id = selection[0]
            if case_id in self.case_data:
                case = self.case_data[case_id]
                self._show_case_details(case)

    def _on_search_change(self, event=None):
        """Manejar cambios en el campo de búsqueda"""
        search_text = self.search_var.get().lower().strip()
        self._filter_cases(search_text)

    def _clear_search(self):
        """Limpiar búsqueda y mostrar todos los casos"""
        self.search_var.set("")
        self._filter_cases("")

    def _filter_cases(self, search_text):
        """Filtrar casos según el texto de búsqueda"""
        # Limpiar treeview
        for item in self.case_tree.get_children():
            self.case_tree.delete(item)

        if not hasattr(self, 'all_cases'):
            return

        # Filtrar casos
        filtered_cases = []
        for case in self.all_cases:
            if not search_text:
                filtered_cases.append(case)
            else:
                # Buscar en carátula, expediente y cliente
                caratula = case.get('caratula', '').lower()
                expediente = case.get('numero_expediente', '').lower()
                cliente_id = case.get('cliente_id')

                cliente_nombre = ""
                if cliente_id:
                    try:
                        cliente = db.get_client_by_id(cliente_id)
                        if cliente:
                            cliente_nombre = cliente.get('nombre', '').lower()
                    except:
                        pass

                if (search_text in caratula or
                    search_text in expediente or
                    search_text in cliente_nombre or
                    search_text in str(case['id'])):
                    filtered_cases.append(case)

        # Mostrar casos filtrados
        for case in filtered_cases:
            case_id = case['id']
            numero_exp = case.get('numero_expediente', '')
            caratula = case.get('caratula', 'Sin carátula')
            cliente_id = case.get('cliente_id')

            # Obtener nombre del cliente
            cliente_nombre = "Sin cliente"
            if cliente_id:
                try:
                    cliente = db.get_client_by_id(cliente_id)
                    if cliente:
                        cliente_nombre = cliente.get('nombre', 'Sin nombre')
                except:
                    pass

            estado = "Activo"

            self.case_tree.insert("", "end", iid=str(case_id), values=(
                case_id,
                numero_exp,
                caratula,
                cliente_nombre,
                estado
            ))

        self.status_var.set(f"{len(filtered_cases)} casos encontrados")

    def _update_case_info(self, case):
        """Actualizar información del caso seleccionado"""
        self.case_info_text.config(state=tk.NORMAL)
        self.case_info_text.delete("1.0", tk.END)

        numero_exp = case.get('numero_expediente', 'Sin expediente')
        caratula = case.get('caratula', 'Sin carátula')
        juzgado = case.get('juzgado', 'Sin juzgado')
        cliente_id = case.get('cliente_id')

        cliente_nombre = "Sin cliente"
        if cliente_id:
            try:
                cliente = db.get_client_by_id(cliente_id)
                if cliente:
                    cliente_nombre = cliente.get('nombre', 'Sin nombre')
            except:
                pass

        info_text = f"Expediente: {numero_exp}\nCarátula: {caratula}\nJuzgado: {juzgado}\nCliente: {cliente_nombre}"
        self.case_info_text.insert("1.0", info_text)
        self.case_info_text.config(state=tk.DISABLED)

    def _show_case_details(self, case):
        """Mostrar detalles completos del caso en una ventana emergente"""
        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Detalles del Caso - ID {case['id']}")
        detail_window.geometry("600x400")
        detail_window.transient(self.root)

        # Frame principal
        main_frame = ttk.Frame(detail_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Información básica
        info_frame = ttk.LabelFrame(main_frame, text="Información del Caso", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        fields = [
            ("ID:", str(case['id'])),
            ("Expediente:", case.get('numero_expediente', 'N/A')),
            ("Carátula:", case.get('caratula', 'N/A')),
            ("Juzgado:", case.get('juzgado', 'N/A')),
            ("Jurisdicción:", case.get('jurisdiccion', 'N/A')),
            ("Año Carátula:", case.get('anio_caratula', 'N/A')),
            ("Notas:", case.get('notas', 'Sin notas')),
        ]

        for i, (label, value) in enumerate(fields):
            ttk.Label(info_frame, text=label, font=("TkDefaultFont", 9, "bold")).grid(row=i, column=0, sticky="w", padx=(0, 10), pady=1)
            ttk.Label(info_frame, text=value, wraplength=400).grid(row=i, column=1, sticky="w", pady=1)

        # Botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(button_frame, text="Cerrar", command=detail_window.destroy).pack(side=tk.RIGHT)

    def _send_query(self):
        """Enviar consulta al agente"""
        if not self.agent:
            messagebox.showerror("Error", "Agente no inicializado", parent=self.root)
            return

        query = self.input_text.get("1.0", tk.END).strip()
        if not query:
            messagebox.showwarning("Advertencia", "Por favor, escriba una consulta", parent=self.root)
            return

        # Limpiar campo de entrada
        self.input_text.delete("1.0", tk.END)

        # Agregar consulta del usuario al chat
        self._add_message("Usuario", query)

        # Deshabilitar interfaz durante procesamiento
        self._set_interface_state(False)
        self.status_var.set("Procesando consulta...")

        # Procesar en hilo separado
        def process_query():
            try:
                # Enviar consulta al agente
                response = self.agent.run_intent(query)

                # Mostrar respuesta
                self.root.after(0, lambda: self._add_message("Agente IA", response))
                self.root.after(0, lambda: self.status_var.set("Consulta procesada"))

            except Exception as e:
                error_msg = f"Error procesando consulta: {str(e)}"
                self.root.after(0, lambda: self._add_message("Error", error_msg))
                self.root.after(0, lambda: self.status_var.set("Error en consulta"))

            finally:
                # Rehabilitar interfaz
                self.root.after(0, lambda: self._set_interface_state(True))

        # Ejecutar en hilo separado
        thread = threading.Thread(target=process_query, daemon=True)
        thread.start()

    def _add_message(self, sender, message):
        """Agregar mensaje al chat"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, f"\n[{sender}] {message}\n")
        self.chat_text.insert(tk.END, "-" * 50 + "\n")
        self.chat_text.see(tk.END)
        self.chat_text.config(state=tk.DISABLED)

    def _clear_chat(self):
        """Limpiar el área de chat"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete("1.0", tk.END)
        self.chat_text.config(state=tk.DISABLED)

        # Mostrar mensaje de bienvenida actualizado
        self._add_message("Agente IA", "Chat limpiado. Estoy listo para ayudarte con la generación de acuerdos.\n\n"
                                      "Recuerda que tengo acceso directo a tu base de datos de casos. "
                                      "Selecciona un caso y escribe tu consulta.")

    def _set_interface_state(self, enabled):
        """Habilitar/deshabilitar elementos de la interfaz"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.input_text.config(state=state)
        self.search_entry.config(state=state)
        self.case_tree.config(selectmode="browse" if enabled else "none")

        # Cambiar color de fondo para indicar estado
        if enabled:
            self.case_tree.configure(style="Treeview")
        else:
            # Aplicar estilo deshabilitado (esto puede variar según el tema)
            pass

    def _close(self):
        """Cerrar la interfaz"""
        if messagebox.askyesno("Confirmar", "¿Desea cerrar la interfaz del Agente IA?", parent=self.root):
            self.root.destroy()

    def run(self):
        """Ejecutar la interfaz"""
        self.root.mainloop()


def open_agent_interface(parent=None, case_id=None, case_caratula=None):
    """Función para abrir la interfaz del agente desde otras partes del sistema"""
    try:
        agent_interface = AgentInterface(parent, case_id=case_id, case_caratula=case_caratula)
        return agent_interface
    except Exception as e:
        messagebox.showerror("Error", f"Error abriendo interfaz del agente: {str(e)}", parent=parent)
        return None


if __name__ == "__main__":
    # Ejecutar interfaz independiente
    app = AgentInterface()
    app.run()