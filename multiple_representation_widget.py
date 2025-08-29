# multiple_representation_widget.py
import tkinter as tk
from tkinter import ttk

class MultipleRepresentationWidget(ttk.Frame):
    """
    Widget para seleccionar múltiples partes que un abogado puede representar.
    Proporciona una interfaz intuitiva con checkboxes y validación en tiempo real.
    """
    
    def __init__(self, parent, available_parties=None, on_selection_change=None):
        super().__init__(parent)
        
        self.available_parties = available_parties or []
        self.on_selection_change = on_selection_change
        self.selected_parties = {}  # {party_id: party_data}
        self.party_vars = {}  # {party_id: BooleanVar}
        
        self._create_widgets()
        self._update_available_parties()
    
    def _create_widgets(self):
        """Crea la interfaz del widget."""
        
        # Frame principal con scroll
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(self.main_frame, text="Seleccionar Partes a Representar:", 
                               font=('TkDefaultFont', 9, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # Frame con scroll para la lista de partes
        self.scroll_frame = ttk.Frame(self.main_frame)
        self.scroll_frame.pack(fill=tk.BOTH, expand=True)
        
        # Canvas y scrollbar para scroll vertical
        self.canvas = tk.Canvas(self.scroll_frame, height=150)
        self.scrollbar = ttk.Scrollbar(self.scroll_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Empaquetar canvas y scrollbar
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para resumen de selección
        self.summary_frame = ttk.LabelFrame(self.main_frame, text="Resumen de Selección", padding="5")
        self.summary_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.summary_label = ttk.Label(self.summary_frame, text="Ninguna parte seleccionada", 
                                     foreground='gray')
        self.summary_label.pack(anchor=tk.W)
        
        # Frame para mensajes de validación
        self.validation_frame = ttk.Frame(self.main_frame)
        self.validation_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.validation_label = ttk.Label(self.validation_frame, text="", foreground='red')
        self.validation_label.pack(anchor=tk.W)
        
        # Configurar eventos de scroll con mouse wheel
        self._bind_mousewheel()
    
    def _bind_mousewheel(self):
        """Configura el scroll con la rueda del mouse."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def set_available_parties(self, parties):
        """
        Establece las partes disponibles para selección.
        
        Args:
            parties (list): Lista de diccionarios con información de partes
        """
        self.available_parties = parties or []
        self._update_available_parties()
    
    def _update_available_parties(self):
        """Actualiza la lista de partes disponibles en la interfaz."""
        # Limpiar widgets existentes
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.party_vars.clear()
        
        if not self.available_parties:
            no_parties_label = ttk.Label(self.scrollable_frame, 
                                       text="No hay partes disponibles para representar",
                                       foreground='gray', font=('TkDefaultFont', 9, 'italic'))
            no_parties_label.pack(anchor=tk.W, pady=10)
            self._update_summary()
            return
        
        # Crear checkboxes para cada parte disponible
        for i, party in enumerate(self.available_parties):
            party_id = party.get('rol_id') or party.get('id')
            if not party_id:
                continue
            
            # Crear variable booleana para el checkbox
            var = tk.BooleanVar()
            var.trace('w', lambda *args, pid=party_id: self._on_party_selection_change(pid))
            self.party_vars[party_id] = var
            
            # Frame para cada partido
            party_frame = ttk.Frame(self.scrollable_frame)
            party_frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Checkbox
            checkbox = ttk.Checkbutton(party_frame, variable=var)
            checkbox.pack(side=tk.LEFT)
            
            # Información de la parte
            party_name = party.get('nombre_completo', 'N/A')
            party_role = party.get('rol_principal', 'N/A')
            party_secondary = party.get('rol_secundario', '')
            
            # Texto principal
            main_text = f"{party_name} ({party_role})"
            if party_secondary:
                main_text += f" - {party_secondary}"
            
            info_label = ttk.Label(party_frame, text=main_text)
            info_label.pack(side=tk.LEFT, padx=(5, 0))
            
            # Indicador de tipo de persona si está disponible
            if party.get('es_persona_juridica'):
                type_label = ttk.Label(party_frame, text="🏢", font=('TkDefaultFont', 8))
                type_label.pack(side=tk.RIGHT)
            else:
                type_label = ttk.Label(party_frame, text="👤", font=('TkDefaultFont', 8))
                type_label.pack(side=tk.RIGHT)
            
            # Separador visual
            if i < len(self.available_parties) - 1:
                separator = ttk.Separator(self.scrollable_frame, orient=tk.HORIZONTAL)
                separator.pack(fill=tk.X, pady=1)
        
        self._update_summary()
    
    def _on_party_selection_change(self, party_id):
        """
        Maneja cambios en la selección de partes.
        
        Args:
            party_id: ID de la parte que cambió su estado de selección
        """
        var = self.party_vars.get(party_id)
        if not var:
            return
        
        # Actualizar diccionario de partes seleccionadas
        if var.get():
            # Parte seleccionada - agregar al diccionario
            party_data = next((p for p in self.available_parties 
                             if (p.get('rol_id') or p.get('id')) == party_id), None)
            if party_data:
                self.selected_parties[party_id] = party_data
        else:
            # Parte deseleccionada - remover del diccionario
            self.selected_parties.pop(party_id, None)
        
        # Actualizar resumen y validación
        self._update_summary()
        self._validate_selection()
        
        # Notificar cambio si hay callback
        if self.on_selection_change:
            self.on_selection_change(self.get_selected_parties())
    
    def _update_summary(self):
        """Actualiza el resumen de selección."""
        selected_count = len(self.selected_parties)
        
        if selected_count == 0:
            summary_text = "Ninguna parte seleccionada"
            color = 'gray'
        elif selected_count == 1:
            party = list(self.selected_parties.values())[0]
            party_name = party.get('nombre_completo', 'N/A')
            summary_text = f"1 parte seleccionada: {party_name}"
            color = 'blue'
        else:
            party_names = [p.get('nombre_completo', 'N/A') for p in self.selected_parties.values()]
            if len(party_names) <= 3:
                names_text = ", ".join(party_names)
            else:
                names_text = ", ".join(party_names[:2]) + f" y {len(party_names)-2} más"
            
            summary_text = f"{selected_count} partes seleccionadas: {names_text}"
            color = 'green'
        
        self.summary_label.config(text=summary_text, foreground=color)
    
    def _validate_selection(self):
        """Valida la selección actual y muestra mensajes de error si es necesario."""
        selected_count = len(self.selected_parties)
        
        if selected_count == 0:
            self.validation_label.config(text="⚠️ Debe seleccionar al menos una parte para representar", 
                                       foreground='orange')
        elif selected_count == 1:
            self.validation_label.config(text="ℹ️ Para representación múltiple, seleccione al menos 2 partes", 
                                       foreground='blue')
        else:
            self.validation_label.config(text="✅ Selección válida para representación múltiple", 
                                       foreground='green')
    
    def get_selected_parties(self):
        """
        Obtiene las partes actualmente seleccionadas.
        
        Returns:
            list: Lista de datos de partes seleccionadas
        """
        return list(self.selected_parties.values())
    
    def get_selected_party_ids(self):
        """
        Obtiene los IDs de las partes seleccionadas.
        
        Returns:
            list: Lista de IDs de partes seleccionadas
        """
        return list(self.selected_parties.keys())
    
    def set_selected_parties(self, party_ids):
        """
        Establece las partes seleccionadas programáticamente.
        
        Args:
            party_ids (list): Lista de IDs de partes a seleccionar
        """
        # Limpiar selección actual
        for var in self.party_vars.values():
            var.set(False)
        
        self.selected_parties.clear()
        
        # Seleccionar las partes especificadas
        for party_id in party_ids:
            if party_id in self.party_vars:
                self.party_vars[party_id].set(True)
                # La actualización se maneja automáticamente por el trace
    
    def clear_selection(self):
        """Limpia toda la selección."""
        self.set_selected_parties([])
    
    def is_valid_selection(self):
        """
        Verifica si la selección actual es válida.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        selected_count = len(self.selected_parties)
        
        if selected_count == 0:
            return False, "Debe seleccionar al menos una parte para representar"
        
        # Para representación múltiple, requerir al menos 2 partes
        if selected_count == 1:
            return True, "Representación simple válida"
        
        return True, "Representación múltiple válida"
    
    def get_selection_summary(self):
        """
        Obtiene un resumen textual de la selección actual.
        
        Returns:
            str: Resumen de la selección
        """
        selected_count = len(self.selected_parties)
        
        if selected_count == 0:
            return "Sin selección"
        elif selected_count == 1:
            party = list(self.selected_parties.values())[0]
            return f"Representa a: {party.get('nombre_completo', 'N/A')}"
        else:
            party_names = [p.get('nombre_completo', 'N/A') for p in self.selected_parties.values()]
            return f"Representa a {selected_count} partes: {', '.join(party_names)}"


# Función de utilidad para crear el widget en diálogos
def create_multiple_representation_widget(parent, available_parties, on_change=None):
    """
    Función de utilidad para crear fácilmente el widget de representación múltiple.
    
    Args:
        parent: Widget padre
        available_parties: Lista de partes disponibles
        on_change: Callback para cambios en la selección
        
    Returns:
        MultipleRepresentationWidget: Widget configurado
    """
    widget = MultipleRepresentationWidget(parent, available_parties, on_change)
    return widget