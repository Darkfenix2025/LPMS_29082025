"""
Prospect Dialog Manager - Gestor de Diálogos de Consultas para Prospectos
Maneja la interfaz de consultas y la integración con IA para reformulación de hechos
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import crm_database as db
import datetime
import threading
import os
from word_export_manager import WordExportManager
import date_utils
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class ProspectDialogManager:
    """Clase que maneja los diálogos de consultas de prospectos"""

    def __init__(self, app_controller):
        self.app_controller = app_controller
        self.db = db
        self.consultation_saved = False  # Flag to track if consultation has been manually saved
    
    def open_consultation_dialog(self, prospect_data, consultation_data=None):
        """
        Abre el diálogo de consulta para un prospecto.

        Args:
            prospect_data (dict): Datos del prospecto
            consultation_data (dict): Datos de consulta existente (opcional, para edición)
        """
        is_edit = consultation_data is not None
        self.consultation_saved = is_edit  # Reset flag: True if editing existing, False if new
        
        dialog = tk.Toplevel(self.app_controller.root)
        dialog.title(f"{'Editar' if is_edit else 'Nueva'} Consulta - {prospect_data['nombre']}")
        dialog.transient(self.app_controller.root)
        dialog.grab_set()
        dialog.geometry("900x700")
        dialog.resizable(True, True)
        
        # Frame principal con scroll
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Información del prospecto
        info_frame = ttk.LabelFrame(main_frame, text="Información del Prospecto", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(info_frame, text=f"Nombre: {prospect_data['nombre']}", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Contacto: {prospect_data.get('contacto', 'N/A')}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Estado: {prospect_data.get('estado', 'N/A')}").pack(anchor=tk.W)
        
        # Frame para fecha de consulta
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(date_frame, text="Fecha de Consulta:").pack(side=tk.LEFT)
        date_var = tk.StringVar()
        if is_edit and consultation_data.get('fecha_consulta'):
            fecha_consulta = consultation_data['fecha_consulta']
            if isinstance(fecha_consulta, str):
                # Try to parse and convert to Argentine format
                parsed_date = date_utils.DateFormatter.parse_date_input(fecha_consulta)
                if parsed_date:
                    date_var.set(parsed_date.strftime(date_utils.DateFormatter.ARGENTINE_FORMAT))
                else:
                    date_var.set(fecha_consulta)
            else:
                date_var.set(fecha_consulta.strftime(date_utils.DateFormatter.ARGENTINE_FORMAT))
        else:
            date_var.set(date_utils.DateFormatter.get_today_display().replace('/', '-'))
        
        date_entry = ttk.Entry(date_frame, textvariable=date_var, width=12)
        date_entry.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Label(date_frame, text="(DD-MM-YYYY)").pack(side=tk.LEFT, padx=(5, 0))
        
        # Frame para relato original del cliente
        relato_frame = ttk.LabelFrame(main_frame, text="Relato Original del Cliente", padding="10")
        relato_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        relato_text = scrolledtext.ScrolledText(relato_frame, height=8, wrap=tk.WORD)
        relato_text.pack(fill=tk.BOTH, expand=True)
        
        if is_edit and consultation_data.get('relato_original_cliente'):
            relato_text.insert("1.0", consultation_data['relato_original_cliente'])
        
        # Frame para análisis de IA
        ia_frame = ttk.LabelFrame(main_frame, text="Análisis de IA", padding="10")
        ia_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Botón para análisis de IA
        ia_button_frame = ttk.Frame(ia_frame)
        ia_button_frame.pack(fill=tk.X, pady=(0, 5))
        
        analyze_btn = ttk.Button(ia_button_frame, text="Analizar y Reformular Hechos con IA")
        analyze_btn.pack(side=tk.LEFT)
        
        # Label de estado
        status_label = ttk.Label(ia_button_frame, text="")
        status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # Área de texto para hechos reformulados (solo lectura)
        hechos_reformulados_text = scrolledtext.ScrolledText(ia_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        hechos_reformulados_text.pack(fill=tk.BOTH, expand=True, pady=(5, 5))
        
        if is_edit and consultation_data.get('hechos_reformulados_ia'):
            hechos_reformulados_text.config(state=tk.NORMAL)
            hechos_reformulados_text.insert("1.0", consultation_data['hechos_reformulados_ia'])
            hechos_reformulados_text.config(state=tk.DISABLED)
        
        # Botón para guardar y exportar análisis
        export_button_frame = ttk.Frame(ia_frame)
        export_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        export_btn = ttk.Button(
            export_button_frame, 
            text="💾 Guardar y Exportar Análisis a Word",
            command=lambda: self._save_and_export_analysis(
                prospect_data, relato_text, hechos_reformulados_text, 
                date_var, dialog, is_edit, consultation_data
            ),
            state=tk.DISABLED
        )
        export_btn.pack(side=tk.RIGHT, padx=(5, 0))
        

        
        # Configurar el comando del botón de análisis de IA
        def analyze_with_ai():
            relato_original = relato_text.get("1.0", tk.END).strip()
            if not relato_original:
                messagebox.showwarning("Advertencia", "Ingrese el relato original del cliente antes de analizar.", parent=dialog)
                return
            
            self._start_ai_analysis(relato_original, hechos_reformulados_text, analyze_btn, status_label, prospect_data, export_btn)
        
        analyze_btn.config(command=analyze_with_ai)
        

        
        # Botones de acción
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        def save_consultation():
            # Validar fecha
            try:
                fecha_consulta = date_utils.DateFormatter.parse_date_input(date_var.get())
                if fecha_consulta is None:
                    raise ValueError("Fecha inválida")
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD-MM-YYYY (ej: 15-03-2024).", parent=dialog)
                return
            
            relato_original = relato_text.get("1.0", tk.END).strip()
            hechos_reformulados = hechos_reformulados_text.get("1.0", tk.END).strip()
            
            if not relato_original:
                messagebox.showwarning("Advertencia", "El relato original del cliente no puede estar vacío.", parent=dialog)
                return
            
            if is_edit:
                # Actualizar consulta existente
                success = self.db.update_consulta(
                    consultation_data['id'],
                    relato_original_cliente=relato_original,
                    hechos_reformulados_ia=hechos_reformulados
                )
                if success:
                    # Marcar como guardada para evitar auto-guardado duplicado
                    self.consultation_saved = True
                    messagebox.showinfo("Éxito", "Consulta actualizada con éxito.", parent=self.app_controller.root)
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo actualizar la consulta.", parent=dialog)
            else:
                # Crear nueva consulta
                consulta_id = self.db.add_consulta(
                    prospect_data['id'],
                    fecha_consulta=fecha_consulta,
                    relato_original_cliente=relato_original,
                    hechos_reformulados_ia=hechos_reformulados
                )
                if consulta_id:
                    # Marcar como guardada para evitar auto-guardado duplicado
                    self.consultation_saved = True

                    # Actualizar estado del prospecto a "En Análisis" si está en "Consulta Inicial"
                    if prospect_data.get('estado') == 'Consulta Inicial':
                        self.app_controller.prospect_manager.update_prospect_status(prospect_data['id'], 'En Análisis')

                    messagebox.showinfo("Éxito", "Consulta guardada con éxito.", parent=self.app_controller.root)
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "No se pudo guardar la consulta.", parent=dialog)
        
        ttk.Button(button_frame, text="Guardar Consulta", command=save_consultation).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.LEFT)
        
        # Enfocar el área de relato
        relato_text.focus_set()
        
        self.app_controller.root.wait_window(dialog)
    
    def _save_and_export_analysis(self, prospect_data, relato_text_widget, hechos_text_widget, 
                                 date_var, dialog, is_edit=False, consultation_data=None):
        """
        Guarda la consulta con análisis IA y la exporta a Word
        
        Args:
            prospect_data (dict): Datos del prospecto
            relato_text_widget: Widget con el relato original
            hechos_text_widget: Widget con el análisis IA
            date_var: Variable con la fecha de consulta
            dialog: Ventana del diálogo
            is_edit (bool): Si es edición de consulta existente
            consultation_data (dict): Datos de consulta existente si es edición
        """
        try:
            # Validar fecha
            try:
                fecha_consulta = date_utils.DateFormatter.parse_date_input(date_var.get())
                if fecha_consulta is None:
                    raise ValueError("Fecha inválida")
            except (ValueError, TypeError):
                messagebox.showerror("Error", "Formato de fecha inválido. Use DD-MM-YYYY (ej: 15-03-2024).", parent=dialog)
                return
            
            # Obtener contenido
            relato_original = relato_text_widget.get("1.0", tk.END).strip()
            hechos_reformulados = hechos_text_widget.get("1.0", tk.END).strip()
            
            if not relato_original:
                messagebox.showwarning("Advertencia", "El relato original del cliente no puede estar vacío.", parent=dialog)
                return
            
            if not hechos_reformulados or hechos_reformulados == "Procesando, esto puede tardar varios segundos...":
                messagebox.showwarning("Advertencia", "Debe generar el análisis de IA antes de exportar.", parent=dialog)
                return
            
            # Preparar datos de consulta para exportación
            consultation_export_data = {
                'fecha_consulta': fecha_consulta,
                'relato_original_cliente': relato_original,
                'hechos_reformulados_ia': hechos_reformulados
            }
            
            # Guardar en base de datos primero
            if is_edit and consultation_data:
                # Actualizar consulta existente
                success = self.db.update_consulta(
                    consultation_data['id'],
                    relato_original_cliente=relato_original,
                    hechos_reformulados_ia=hechos_reformulados
                )
                if not success:
                    messagebox.showerror("Error", "No se pudo guardar la consulta en la base de datos.", parent=dialog)
                    return
                consultation_export_data['id'] = consultation_data['id']

                # Marcar como guardada para evitar auto-guardado duplicado
                self.consultation_saved = True
            else:
                # Crear nueva consulta
                consulta_id = self.db.add_consulta(
                    prospect_data['id'],
                    fecha_consulta=fecha_consulta,
                    relato_original_cliente=relato_original,
                    hechos_reformulados_ia=hechos_reformulados
                )
                if not consulta_id:
                    messagebox.showerror("Error", "No se pudo guardar la consulta en la base de datos.", parent=dialog)
                    return
                consultation_export_data['id'] = consulta_id

                # Marcar como guardada para evitar auto-guardado duplicado
                self.consultation_saved = True
                
                # Actualizar estado del prospecto
                if prospect_data.get('estado') == 'Consulta Inicial':
                    self.app_controller.prospect_manager.update_prospect_status(prospect_data['id'], 'En Análisis')
            
            # Exportar a Word
            export_manager = WordExportManager()
            filepath = export_manager.export_consultation_to_word(
                prospect_data, 
                consultation_export_data, 
                dialog,
                show_open_dialog=False  # No mostrar diálogo de abrir desde aquí
            )
            
            if filepath:
                # Marcar consulta como exportada en la base de datos
                consulta_id = consultation_export_data.get('id')
                if consulta_id:
                    export_success = self.db.mark_consulta_as_exported(consulta_id, filepath)
                    if not export_success:
                        print(f"Advertencia: No se pudo marcar la consulta {consulta_id} como exportada")
                
                # Éxito total - Preguntar si quiere cerrar la ventana
                result = messagebox.askyesnocancel(
                    "Éxito Completo", 
                    f"Consulta guardada y exportada exitosamente.\n\nArchivo: {os.path.basename(filepath)}\n\n¿Desea cerrar esta ventana?", 
                    parent=dialog
                )
                if result is True:  # Sí, cerrar
                    dialog.destroy()
                elif result is False:  # No, mantener abierta
                    # La ventana permanece abierta para seguir editando
                    pass
                # Si result is None (Cancelar), no hacer nada
            else:
                # Error en exportación pero guardado exitoso
                messagebox.showwarning(
                    "Guardado Parcial", 
                    "La consulta se guardó en la base de datos, pero hubo un error al exportar a Word.\n\nLa ventana permanece abierta para que pueda intentar exportar nuevamente.", 
                    parent=dialog
                )
                
        except Exception as e:
            error_msg = f"Error durante el proceso de guardado y exportación: {str(e)}"
            print(error_msg)
            messagebox.showerror("Error", error_msg, parent=dialog)
    
    def _start_ai_analysis(self, relato_original, result_text_widget, button_widget, status_label_widget, prospect_data=None, export_btn=None):
        """
        Inicia el análisis de IA en un hilo separado para reformular los hechos.
        
        Args:
            relato_original (str): Relato original del cliente
            result_text_widget (tk.Text): Widget donde mostrar el resultado
            button_widget (ttk.Button): Botón a deshabilitar durante el análisis
            status_label_widget (ttk.Label): Label para mostrar el estado
            prospect_data (dict): Datos del prospecto para auto-guardado
        """
        # Deshabilitar botón y mostrar estado
        button_widget.config(state=tk.DISABLED, text="Analizando...")
        status_label_widget.config(text="Estado: Procesando con IA...")
        result_text_widget.config(state=tk.NORMAL)
        result_text_widget.delete("1.0", tk.END)
        result_text_widget.insert("1.0", "Procesando, esto puede tardar varios segundos...")
        result_text_widget.config(state=tk.DISABLED)
        
        def ai_analysis_thread():
            try:
                # Cargar el prompt desde archivo externo
                prompt_final = self._load_reformulation_prompt(relato_original)
                
                # Llamar a la IA local usando Ollama
                resultado = self._call_local_ollama_ai(prompt_final)
                
                def update_ui():
                    result_text_widget.config(state=tk.NORMAL)
                    result_text_widget.delete("1.0", tk.END)
                    
                    if "error" in resultado:
                        texto_final = f"ERROR: {resultado['error']}"
                        result_text_widget.insert("1.0", texto_final)
                        status_label_widget.config(text="Estado: Error en el análisis")
                    else:
                        texto_final = resultado.get("result", "No se obtuvo respuesta de la IA.")
                        result_text_widget.insert("1.0", texto_final)
                        status_label_widget.config(text="Estado: Análisis completado - Guardando automáticamente...")
                        
                        # Habilitar botón de exportar si existe
                        if export_btn:
                            export_btn.config(state=tk.NORMAL)
                        
                        # Guardar automáticamente el análisis de IA si se proporcionaron los datos
                        if prospect_data:
                            self._auto_save_ai_analysis(prospect_data, relato_original, texto_final)
                        
                        # Mostrar notificación de guardado
                        try:
                            import plyer
                            plyer.notification.notify(
                                title="Análisis IA Guardado",
                                message="El análisis de IA ha sido guardado automáticamente. Puede continuar editando la consulta.",
                                timeout=8
                            )
                        except:
                            pass  # Si falla la notificación, continuar normalmente
                    
                    result_text_widget.config(state=tk.DISABLED)
                    button_widget.config(state=tk.NORMAL, text="Analizar y Reformular Hechos con IA")
                
                # Actualizar UI en el hilo principal
                self.app_controller.root.after(0, update_ui)
                
            except Exception as e:
                def update_ui_error():
                    result_text_widget.config(state=tk.NORMAL)
                    result_text_widget.delete("1.0", tk.END)
                    result_text_widget.insert("1.0", f"Error durante el análisis: {str(e)}")
                    result_text_widget.config(state=tk.DISABLED)
                    status_label_widget.config(text="Estado: Error")
                    button_widget.config(state=tk.NORMAL, text="Analizar y Reformular Hechos con IA")
                
                self.app_controller.root.after(0, update_ui_error)
                print(f"Error en análisis de IA: {e}")
        
        # Ejecutar en hilo separado
        threading.Thread(target=ai_analysis_thread, daemon=True).start()
    
    def _load_reformulation_prompt(self, relato_original):
        """
        Carga el prompt de reformulación desde archivo externo.
        
        Args:
            relato_original (str): Relato original del cliente
            
        Returns:
            str: Prompt final con el relato insertado
        """
        try:
            prompt_file_path = "prompts/reformulacion_hechos.txt"
            with open(prompt_file_path, "r", encoding="utf-8") as f:
                plantilla_prompt = f.read()
            
            # Reemplazar el marcador con el relato original
            prompt_final = plantilla_prompt.format(relato_original=relato_original)
            return prompt_final
            
        except FileNotFoundError:
            print(f"ERROR: No se encontró el archivo de prompt '{prompt_file_path}'")
            # Prompt de fallback
            return f"""Actúa como un abogado experto en análisis de casos legales. Tu tarea es reformular el siguiente relato de un cliente en una narrativa fáctica, cronológica y jurídicamente relevante.

RELATO ORIGINAL DEL CLIENTE:
{relato_original}

INSTRUCCIONES:
1. Organiza los hechos de manera cronológica
2. Identifica los puntos clave jurídicamente relevantes
3. Señala posibles derechos vulnerados o responsabilidades
4. Usa un lenguaje técnico-jurídico apropiado
5. Mantén la objetividad y precisión

HECHOS REFORMULADOS:"""
        
        except Exception as e:
            print(f"Error cargando prompt: {e}")
            return f"Reformula los siguientes hechos de manera jurídicamente relevante:\n\n{relato_original}"
    
    def _call_local_ollama_ai(self, prompt):
        """
        Llama a la IA local Ollama para el análisis.

        Args:
            prompt (str): Prompt para enviar a la IA

        Returns:
            dict: Resultado del análisis o error
        """
        try:
            # Importar las dependencias de IA local
            from langchain_community.llms import Ollama

            # Inicializar el modelo Ollama local
            llm = Ollama(
                model="mistral-small:22b",
                temperature=0.3,
                base_url="http://localhost:11434"
            )

            # Realizar la consulta
            response = llm.invoke(prompt)

            # Extraer el contenido de la respuesta
            if hasattr(response, 'content'):
                return {"result": response.content}
            else:
                return {"result": str(response)}

        except ImportError as e:
            return {"error": f"Error de importación: {e}. Verifique que langchain-community esté instalado."}
        except Exception as e:
            return {"error": f"Error al consultar la IA local: {str(e)}"}
    
    def _auto_save_ai_analysis(self, prospect_data, relato_original, analisis_ia):
        """
        Guarda automáticamente el análisis de IA como una consulta temporal.

        Args:
            prospect_data (dict): Datos del prospecto
            relato_original (str): Relato original del cliente
            analisis_ia (str): Análisis generado por IA
        """
        # Si la consulta ya fue guardada manualmente, no hacer auto-guardado
        if self.consultation_saved:
            print("Auto-guardado omitido: la consulta ya fue guardada manualmente")
            return

        try:
            import datetime
            
            # Buscar si ya existe una consulta para hoy
            consultas_hoy = []
            todas_consultas = self.db.get_consultas_by_prospecto_id(prospect_data['id'])
            
            fecha_hoy = datetime.date.today()
            for consulta in todas_consultas:
                fecha_consulta = consulta.get('fecha_consulta')
                if isinstance(fecha_consulta, str):
                    # Intentar parsear la fecha si es string
                    try:
                        fecha_consulta = date_utils.DateFormatter.parse_date_input(fecha_consulta)
                    except:
                        continue
                
                if fecha_consulta == fecha_hoy:
                    consultas_hoy.append(consulta)
            
            if consultas_hoy:
                # Actualizar la consulta existente de hoy
                consulta_existente = consultas_hoy[0]  # Tomar la primera
                success = self.db.update_consulta(
                    consulta_existente['id'],
                    relato_original_cliente=relato_original,
                    hechos_reformulados_ia=analisis_ia
                )
                if success:
                    print(f"Análisis IA actualizado en consulta existente ID: {consulta_existente['id']}")
                    # Si se actualizó una consulta existente, significa que ya estaba guardada
                    self.consultation_saved = True
                else:
                    print("Error actualizando consulta existente con análisis IA")
            else:
                # Crear nueva consulta con el análisis
                consulta_id = self.db.add_consulta(
                    prospect_data['id'],
                    fecha_consulta=fecha_hoy,
                    relato_original_cliente=relato_original,
                    hechos_reformulados_ia=analisis_ia,
                    encuadre_legal_preliminar="[Análisis automático - Completar encuadre legal]"
                )
                if consulta_id:
                    print(f"Nueva consulta creada con análisis IA, ID: {consulta_id}")

                    # Actualizar estado del prospecto si está en "Consulta Inicial"
                    if prospect_data.get('estado') == 'Consulta Inicial':
                        self.app_controller.prospect_manager.update_prospect_status(
                            prospect_data['id'], 'En Análisis'
                        )
                    # Nueva consulta creada por auto-guardado, pero no cuenta como guardado manual
                    # El flag permanece False para permitir guardado manual posterior
                else:
                    print("Error creando nueva consulta con análisis IA")
                    
        except Exception as e:
            print(f"Error en auto-guardado de análisis IA: {e}")
            # No mostrar error al usuario, es una funcionalidad de respaldo
    
    def _suggest_legal_framework(self, encuadre_text_widget, hechos_reformulados_widget):
        """Sugiere un encuadre legal basado en los hechos reformulados por IA"""
        hechos_reformulados = hechos_reformulados_widget.get("1.0", tk.END).strip()
        
        if not hechos_reformulados or hechos_reformulados == "Procesando, esto puede tardar varios segundos...":
            messagebox.showwarning("Advertencia", 
                                 "Primero debe generar el análisis de IA de los hechos.", 
                                 parent=self.app_controller.root)
            return
        
        # Sugerencias básicas basadas en palabras clave
        sugerencias = []
        hechos_lower = hechos_reformulados.lower()
        
        # Detectar tipos de casos comunes
        if any(word in hechos_lower for word in ['accidente', 'tránsito', 'vehículo', 'colisión']):
            sugerencias.append("• Responsabilidad civil extracontractual (art. 1109 CC)")
            sugerencias.append("• Daños y perjuicios por accidente de tránsito")
            sugerencias.append("• Posible aplicación de la Ley de Tránsito")
        
        if any(word in hechos_lower for word in ['trabajo', 'laboral', 'empleador', 'despido']):
            sugerencias.append("• Derecho laboral - Ley de Contrato de Trabajo")
            sugerencias.append("• Posible despido sin causa o discriminatorio")
            sugerencias.append("• Reclamo de indemnizaciones laborales")
        
        if any(word in hechos_lower for word in ['consumo', 'producto', 'servicio', 'defectuoso']):
            sugerencias.append("• Derecho del consumidor - Ley 24.240")
            sugerencias.append("• Responsabilidad por producto defectuoso")
            sugerencias.append("• Daños y perjuicios al consumidor")
        
        if any(word in hechos_lower for word in ['médico', 'hospital', 'mala praxis', 'negligencia']):
            sugerencias.append("• Responsabilidad médica - Mala praxis")
            sugerencias.append("• Responsabilidad civil profesional")
            sugerencias.append("• Daños y perjuicios por negligencia médica")
        
        if any(word in hechos_lower for word in ['contrato', 'incumplimiento', 'contractual']):
            sugerencias.append("• Responsabilidad contractual")
            sugerencias.append("• Incumplimiento de contrato")
            sugerencias.append("• Resolución contractual y daños")
        
        if not sugerencias:
            sugerencias.append("• Analizar la normativa aplicable según los hechos")
            sugerencias.append("• Determinar la jurisdicción competente")
            sugerencias.append("• Evaluar la viabilidad de la acción legal")
        
        # Agregar sugerencias generales
        sugerencias.extend([
            "",
            "ASPECTOS A CONSIDERAR:",
            "• Plazos de prescripción aplicables",
            "• Pruebas necesarias para acreditar los hechos",
            "• Cuantificación de daños y perjuicios",
            "• Posibilidad de mediación previa"
        ])
        
        # Insertar sugerencias en el campo
        current_content = encuadre_text_widget.get("1.0", tk.END).strip()
        if current_content and not current_content.startswith("[Análisis automático"):
            encuadre_text_widget.insert(tk.END, "\n\nSUGERENCIAS AUTOMÁTICAS:\n")
        else:
            encuadre_text_widget.delete("1.0", tk.END)
            encuadre_text_widget.insert("1.0", "ENCUADRE LEGAL PRELIMINAR:\n\n")
        
        for sugerencia in sugerencias:
            encuadre_text_widget.insert(tk.END, sugerencia + "\n")
    
    def _show_legal_templates(self, encuadre_text_widget):
        """Muestra plantillas de encuadre legal común"""
        templates = {
            "Responsabilidad Civil": """RESPONSABILIDAD CIVIL EXTRACONTRACTUAL

Marco Legal:
• Artículos 1109 y siguientes del Código Civil
• Elementos: hecho, daño, relación causal, factor de atribución

Análisis:
• Hecho dañoso: [Describir el hecho]
• Daño: [Cuantificar daños materiales y morales]
• Nexo causal: [Establecer relación causa-efecto]
• Factor de atribución: [Culpa o riesgo]

Estrategia:
• Recolección de pruebas
• Pericia técnica si corresponde
• Cuantificación de daños""",

            "Derecho Laboral": """DERECHO LABORAL

Marco Legal:
• Ley de Contrato de Trabajo 20.744
• Convenios colectivos aplicables
• Ley de Riesgos del Trabajo (si aplica)

Análisis:
• Tipo de relación laboral: [Determinar modalidad]
• Causa de extinción: [Analizar legitimidad]
• Indemnizaciones procedentes: [Calcular montos]

Reclamos posibles:
• Indemnización por despido
• Preaviso
• Integración del mes de despido
• Vacaciones proporcionales""",

            "Derecho del Consumidor": """DERECHO DEL CONSUMIDOR

Marco Legal:
• Ley 24.240 de Defensa del Consumidor
• Código Civil y Comercial (Libro III, Título V)

Análisis:
• Relación de consumo: [Verificar elementos]
• Vicio o defecto: [Describir problema]
• Daños: [Cuantificar perjuicios]

Opciones del consumidor:
• Reparación o cambio
• Devolución del precio
• Daños y perjuicios"""
        }
        
        # Crear ventana de selección de plantillas
        template_window = tk.Toplevel(self.app_controller.root)
        template_window.title("Plantillas de Encuadre Legal")
        template_window.geometry("600x400")
        template_window.transient(self.app_controller.root)
        template_window.grab_set()
        
        frame = ttk.Frame(template_window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Seleccione una plantilla:", font=("TkDefaultFont", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Lista de plantillas
        template_listbox = tk.Listbox(frame, height=6)
        template_listbox.pack(fill=tk.X, pady=(0, 10))
        
        for template_name in templates.keys():
            template_listbox.insert(tk.END, template_name)
        
        # Vista previa
        preview_frame = ttk.LabelFrame(frame, text="Vista Previa", padding="5")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        preview_text = scrolledtext.ScrolledText(preview_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        preview_text.pack(fill=tk.BOTH, expand=True)
        
        def on_template_select(event):
            selection = template_listbox.curselection()
            if selection:
                template_name = template_listbox.get(selection[0])
                preview_text.config(state=tk.NORMAL)
                preview_text.delete("1.0", tk.END)
                preview_text.insert("1.0", templates[template_name])
                preview_text.config(state=tk.DISABLED)
        
        template_listbox.bind("<<ListboxSelect>>", on_template_select)
        
        # Botones
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X)
        
        def use_template():
            selection = template_listbox.curselection()
            if selection:
                template_name = template_listbox.get(selection[0])
                encuadre_text_widget.delete("1.0", tk.END)
                encuadre_text_widget.insert("1.0", templates[template_name])
                template_window.destroy()
            else:
                messagebox.showwarning("Advertencia", "Seleccione una plantilla.", parent=template_window)
        
        ttk.Button(button_frame, text="Usar Plantilla", command=use_template).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Cancelar", command=template_window.destroy).pack(side=tk.RIGHT)
        
        self.app_controller.root.wait_window(template_window)
    
    def _save_draft(self, prospect_data, relato_text_widget, hechos_text_widget, encuadre_text_widget):
        """Guarda un borrador de la consulta"""
        relato = relato_text_widget.get("1.0", tk.END).strip()
        hechos = hechos_text_widget.get("1.0", tk.END).strip()
        encuadre = encuadre_text_widget.get("1.0", tk.END).strip()
        
        if not relato:
            messagebox.showwarning("Advertencia", "Ingrese al menos el relato del cliente.", 
                                 parent=self.app_controller.root)
            return
        
        try:
            import datetime
            
            # Buscar consulta existente de hoy o crear nueva
            consultas_hoy = []
            todas_consultas = self.db.get_consultas_by_prospecto_id(prospect_data['id'])
            
            fecha_hoy = datetime.date.today()
            for consulta in todas_consultas:
                fecha_consulta = consulta.get('fecha_consulta')
                if isinstance(fecha_consulta, str):
                    try:
                        fecha_consulta = date_utils.DateFormatter.parse_date_input(fecha_consulta)
                    except:
                        continue
                
                if fecha_consulta == fecha_hoy:
                    consultas_hoy.append(consulta)
            
            if consultas_hoy:
                # Actualizar consulta existente
                success = self.db.update_consulta(
                    consultas_hoy[0]['id'],
                    relato_original_cliente=relato,
                    hechos_reformulados_ia=hechos,
                    encuadre_legal_preliminar=encuadre
                )
                action = "actualizado"
            else:
                # Crear nueva consulta
                consulta_id = self.db.add_consulta(
                    prospect_data['id'],
                    fecha_consulta=fecha_hoy,
                    relato_original_cliente=relato,
                    hechos_reformulados_ia=hechos,
                    encuadre_legal_preliminar=encuadre
                )
                success = consulta_id is not None
                action = "guardado"

            if success:
                # Marcar como guardada para evitar auto-guardado duplicado
                self.consultation_saved = True
                messagebox.showinfo("Éxito", f"Borrador {action} correctamente.",
                                  parent=self.app_controller.root)
                
                # Actualizar estado del prospecto si es necesario
                if prospect_data.get('estado') == 'Consulta Inicial':
                    self.app_controller.prospect_manager.update_prospect_status(
                        prospect_data['id'], 'En Análisis'
                    )
            else:
                messagebox.showerror("Error", "No se pudo guardar el borrador.", 
                                   parent=self.app_controller.root)
                
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando borrador: {str(e)}", 
                               parent=self.app_controller.root)


# Funciones de utilidad
def create_consultation_dialog(app_controller, prospect_data, consultation_data=None):
    """Función de utilidad para crear un diálogo de consulta"""
    dialog_manager = ProspectDialogManager(app_controller)
    dialog_manager.open_consultation_dialog(prospect_data, consultation_data)