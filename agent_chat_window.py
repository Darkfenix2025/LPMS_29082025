"""
Agent Chat Window - Interfaz de chat simplificada para el Asistente de Acuerdos
Permite al usuario interactuar con el agente IA para generar acuerdos de mediación
con contexto pre-cargado del caso actual.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from agent_core import AgentCore
import crm_database as db
import os


class AgentChatWindow:
    """Ventana de chat simplificada para el Asistente de Acuerdos"""

    def __init__(self, parent=None, case_id=None, case_caratula=None):
        self.parent = parent
        self.case_id = case_id
        self.case_caratula = case_caratula
        self.agent = None
        self.case_context = ""

        # Crear ventana principal
        self.root = tk.Toplevel(parent) if parent else tk.Tk()
        title_suffix = f" - {case_caratula}" if case_caratula else ""
        self.root.title(f"Asistente de Acuerdos{title_suffix}")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self._create_widgets()
        self._initialize_agent()
        self._load_case_context()

    def _create_widgets(self):
        """Crear todos los widgets de la interfaz"""

        # Frame superior - Información del caso
        case_frame = ttk.LabelFrame(self.root, text="Información del Caso", padding="10")
        case_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        case_frame.columnconfigure(0, weight=1)

        # Información del caso
        self.case_info_text = tk.Text(case_frame, height=4, wrap=tk.WORD, state=tk.DISABLED, relief=tk.SUNKEN)
        case_info_scroll = ttk.Scrollbar(case_frame, orient=tk.VERTICAL, command=self.case_info_text.yview)
        self.case_info_text.configure(yscrollcommand=case_info_scroll.set)

        self.case_info_text.grid(row=0, column=0, sticky="ew")
        case_info_scroll.grid(row=0, column=1, sticky="ns")

        # Frame principal - Chat con el agente
        main_frame = ttk.Frame(self.root)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Área de chat
        chat_frame = ttk.LabelFrame(main_frame, text="Conversación con el Asistente de Acuerdos", padding="5")
        chat_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        chat_frame.columnconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)

        self.chat_text = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, height=20)
        self.chat_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.chat_text.config(state=tk.DISABLED)

        # Frame de entrada
        input_frame = ttk.LabelFrame(main_frame, text="Escriba sus instrucciones para el acuerdo", padding="5")
        input_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.input_text = tk.Text(input_frame, height=4, wrap=tk.WORD)
        self.input_text.grid(row=0, column=0, sticky="ew", padx=5, pady=2)

        # Frame de botones
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(button_frame, text="Enviar Instrucción", command=self._send_query).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Limpiar Chat", command=self._clear_chat).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cerrar", command=self._close).pack(side=tk.RIGHT, padx=5)

        # Barra de estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo para recibir instrucciones...")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Configurar expansión
        self.root.rowconfigure(1, weight=1)
        main_frame.rowconfigure(0, weight=1)
        chat_frame.rowconfigure(0, weight=1)

        # Mensaje de bienvenida
        self._add_message("Asistente de Acuerdos", "¡Hola! Soy tu asistente especializado en la redacción de acuerdos de mediación.\n\n"
                                        "Ya tengo toda la información del caso cargada y lista para usar. "
                                        "Solo dime qué tipo de acuerdo necesitas y te ayudaré a redactarlo.\n\n"
                                        "Ejemplos de instrucciones:\n"
                                        "• 'Redacta un acuerdo de conciliación por $50,000 con pago en 15 días'\n"
                                        "• 'Necesito un acuerdo laboral con cláusulas específicas'\n"
                                        "• 'Crea un acuerdo comercial con representante legal'\n\n"
                                        "El sistema utilizará automáticamente la plantilla de acuerdos y toda la información del caso actual.")

    def _initialize_agent(self):
        """Inicializar el agente inteligente"""
        try:
            self.status_var.set("Inicializando asistente IA...")
            self.root.update()

            # Crear instancia del agente
            self.agent = AgentCore()

            self.status_var.set("Asistente IA inicializado correctamente")
            self._add_message("Sistema", "Asistente IA inicializado correctamente")

        except Exception as e:
            error_msg = f"Error inicializando asistente: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror("Error", error_msg, parent=self.root)
            self._add_message("Error", error_msg)

    def _load_case_context(self):
        """Cargar y mostrar el contexto del caso"""
        if not self.case_id:
            self._add_message("Sistema", "No se ha especificado un caso para cargar.")
            return

        try:
            self.status_var.set("Cargando información del caso...")
            self.root.update()

            # Obtener datos del caso
            case_data = db.get_case_by_id(self.case_id)
            if not case_data:
                self._add_message("Error", f"No se pudo cargar la información del caso ID {self.case_id}")
                return

            # Obtener partes del caso
            parties = db.get_parties_by_case_id(self.case_id)

            # Formatear contexto del caso
            context_lines = []
            context_lines.append(f"Caso ID: {case_data['id']}")
            context_lines.append(f"Número de Expediente: {case_data.get('numero_expediente', 'No especificado')}")
            context_lines.append(f"Carátula: {case_data.get('caratula', 'No especificada')}")
            context_lines.append(f"Juzgado: {case_data.get('juzgado', 'No especificado')}")
            context_lines.append(f"Jurisdicción: {case_data.get('jurisdiccion', 'No especificada')}")
            context_lines.append(f"Etapa Procesal: {case_data.get('etapa_procesal', 'No especificada')}")
            context_lines.append("")

            # Agregar información de las partes
            if parties:
                context_lines.append("PARTES INTERVINIENTES:")
                for party in parties:
                    rol = party.get('rol', 'Rol no especificado')
                    nombre = party.get('nombre_completo', 'Nombre no disponible')
                    context_lines.append(f"• {rol}: {nombre}")

                    # Agregar información adicional si está disponible
                    if party.get('cuit'):
                        context_lines.append(f"  CUIT: {party['cuit']}")
                    if party.get('domicilio_real'):
                        context_lines.append(f"  Domicilio: {party['domicilio_real']}")
                    if party.get('datos_bancarios'):
                        context_lines.append(f"  Datos Bancarios: {party['datos_bancarios']}")
                    context_lines.append("")
            else:
                context_lines.append("No se encontraron partes intervinientes en el caso.")

            # Crear contexto completo
            self.case_context = "\n".join(context_lines)

            # Mostrar en el área de información del caso
            self.case_info_text.config(state=tk.NORMAL)
            self.case_info_text.delete("1.0", tk.END)
            self.case_info_text.insert("1.0", self.case_context)
            self.case_info_text.config(state=tk.DISABLED)

            # Notificar al agente sobre el caso cargado
            self._add_message("Caso Cargado", f"Se ha cargado exitosamente la información del caso:\n{case_data.get('caratula', f'ID {self.case_id}')}")
            self.status_var.set("Información del caso cargada correctamente")

        except Exception as e:
            error_msg = f"Error cargando información del caso: {str(e)}"
            self.status_var.set("Error cargando caso")
            self._add_message("Error", error_msg)
            print(f"[ERROR] {error_msg}")

    def _extract_case_info(self):
        """Extraer información estructurada del caso para el agente"""
        case_info = {
            'case_id': self.case_id,
            'expediente': 'NO ESPECIFICADO',
            'caratula': 'NO ESPECIFICADA',
            'banco': 'BANCO POR DETERMINAR',
            'cuit_actor': '0'
        }

        try:
            # Obtener datos del caso
            case_data = db.get_case_by_id(self.case_id)
            if case_data:
                case_info['expediente'] = case_data.get('numero_expediente', 'NO ESPECIFICADO')
                case_info['caratula'] = case_data.get('caratula', 'NO ESPECIFICADA')

            # Obtener información de las partes para extraer datos bancarios y CUIT
            parties = db.get_parties_by_case_id(self.case_id)
            if parties:
                for party in parties:
                    # Buscar el actor (demandante)
                    if 'actor' in party.get('rol', '').lower() or 'demandante' in party.get('rol', '').lower():
                        case_info['cuit_actor'] = party.get('cuit', '0')

                        # Extraer información bancaria si está disponible
                        datos_bancarios = party.get('datos_bancarios', '')
                        if datos_bancarios:
                            # Intentar extraer nombre del banco
                            if 'banco' in datos_bancarios.lower():
                                case_info['banco'] = datos_bancarios
                            elif 'bbva' in datos_bancarios.lower():
                                case_info['banco'] = 'BANCO BBVA ARGENTINA S.A.'
                            elif 'galicia' in datos_bancarios.lower():
                                case_info['banco'] = 'BANCO DE GALICIA'
                            elif 'nacion' in datos_bancarios.lower():
                                case_info['banco'] = 'BANCO DE LA NACION ARGENTINA'
                        break

        except Exception as e:
            print(f"[WARNING] Error extrayendo información del caso: {str(e)}")

        return case_info

    def _send_query(self):
        """Enviar consulta al agente"""
        if not self.agent:
            messagebox.showerror("Error", "Asistente no inicializado", parent=self.root)
            return

        user_input = self.input_text.get("1.0", tk.END).strip()
        if not user_input:
            messagebox.showwarning("Advertencia", "Por favor, escriba sus instrucciones", parent=self.root)
            return

        # Limpiar campo de entrada
        self.input_text.delete("1.0", tk.END)

        # Agregar consulta del usuario al chat
        self._add_message("Usuario", user_input)

        # Deshabilitar interfaz durante procesamiento
        self._set_interface_state(False)
        self.status_var.set("Procesando instrucciones...")

        # Procesar en hilo separado
        def process_query():
            try:
                # Extraer información específica del contexto del caso
                case_info = self._extract_case_info()

                # Crear prompt más específico y guiado
                full_prompt = f"""
**CONTEXTO DEL CASO:**
{self.case_context}

**INSTRUCCIONES DEL USUARIO:**
{user_input}

**TAREA ESPECÍFICA:**
Necesito que generes un acuerdo de mediación completo usando la siguiente información del caso:

**DATOS EXTRAÍDOS DEL CASO:**
- ID del caso: {case_info.get('case_id', 'DESCONOCIDO')}
- Expediente: {case_info.get('expediente', 'NO ESPECIFICADO')}
- Carátula: {case_info.get('caratula', 'NO ESPECIFICADA')}

**PASOS A SEGUIR:**
1. PRIMERO: Lee la plantilla usando 'leer_plantilla_de_acuerdo' con filepath="modelo_acuerdo.txt"
2. LUEGO: Usa 'generar_acuerdo_template_tool' con estos parámetros específicos:
   - id_del_caso: {case_info.get('case_id', 'DESCONOCIDO')}
   - monto_compensacion: "0" (dejar en 0 para completar manualmente)
   - plazo_pago_dias: "20" (valor por defecto, puede ajustarse)
   - banco_actor: "{case_info.get('banco', 'BANCO POR DETERMINAR')}"
   - cbu_actor: "0" (completar manualmente)
   - alias_actor: "0" (completar manualmente)
   - cuit_actor: "{case_info.get('cuit_actor', '0')}"
   - contexto_adicional: "{user_input}"

**IMPORTANTE:**
- Si algún dato está vacío o es "0", el sistema lo dejará para completar manualmente
- El acuerdo debe incorporar toda la información disponible del caso
- Usa la plantilla como base pero adapta el contenido según las instrucciones del usuario
"""

                # Enviar consulta al agente
                response = self.agent.run_intent(full_prompt)

                # Mostrar respuesta
                self.root.after(0, lambda: self._add_message("Asistente de Acuerdos", response))
                self.root.after(0, lambda: self.status_var.set("Instrucciones procesadas"))

            except Exception as e:
                error_msg = f"Error procesando instrucciones: {str(e)}"
                self.root.after(0, lambda: self._add_message("Error", error_msg))
                self.root.after(0, lambda: self.status_var.set("Error en procesamiento"))

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
        self._add_message("Asistente de Acuerdos", "Chat limpiado. Estoy listo para ayudarte con la redacción de acuerdos de mediación.\n\n"
                                        "Recuerda que tengo toda la información del caso cargada. "
                                        "Solo dime qué tipo de acuerdo necesitas.")

    def _set_interface_state(self, enabled):
        """Habilitar/deshabilitar elementos de la interfaz"""
        state = tk.NORMAL if enabled else tk.DISABLED
        self.input_text.config(state=state)

        # Cambiar color de fondo para indicar estado
        if enabled:
            self.chat_text.configure(bg='white')
        else:
            self.chat_text.configure(bg='#f0f0f0')

    def _close(self):
        """Cerrar la ventana"""
        if messagebox.askyesno("Confirmar", "¿Desea cerrar el Asistente de Acuerdos?", parent=self.root):
            self.root.destroy()

    def run(self):
        """Ejecutar la interfaz"""
        self.root.mainloop()


def open_agent_chat_window(parent=None, case_id=None, case_caratula=None):
    """Función para abrir la ventana de chat del asistente desde otras partes del sistema"""
    try:
        chat_window = AgentChatWindow(parent, case_id=case_id, case_caratula=case_caratula)
        return chat_window
    except Exception as e:
        messagebox.showerror("Error", f"Error abriendo Asistente de Acuerdos: {str(e)}", parent=parent)
        return None


if __name__ == "__main__":
    # Ejecutar interfaz independiente para pruebas
    app = AgentChatWindow()
    app.run()