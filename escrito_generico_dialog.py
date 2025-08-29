import tkinter as tk
from tkinter import ttk, messagebox


class EscritoGenericoDialog(tk.Toplevel):
    """
    Modal dialog for collecting user input for generic legal document generation.
    
    This dialog allows users to enter a document title and body content,
    validates the input, and returns the data for document generation.
    """
    
    def __init__(self, parent, callback_function=None):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent window
            callback_function: Optional callback function (for compatibility)
        """
        super().__init__(parent)
        self.parent = parent
        self.callback_function = callback_function
        self.result = None
        
        # Configure dialog window
        self.title("Escrito Genérico")
        self.transient(parent)
        self.grab_set()  # Make dialog modal
        self.resizable(True, True)
        
        # Set minimum size
        self.minsize(500, 400)
        
        # Center the dialog on parent window
        self._center_on_parent()
        
        # Create widgets
        self._create_widgets()
        
        # Set focus to title field
        self.titulo_entry.focus_set()
        
        # Bind Escape key to cancel
        self.bind('<Escape>', lambda e: self._cancel())
        
        # Handle window close button
        self.protocol("WM_DELETE_WINDOW", self._cancel)
    
    def _center_on_parent(self):
        """Center the dialog on the parent window."""
        self.update_idletasks()
        
        # Get parent window geometry
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Calculate center position
        dialog_width = 600
        dialog_height = 500
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        # Set geometry
        self.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def _create_widgets(self):
        """Create and layout all dialog widgets."""
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid weights for resizing
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title field
        ttk.Label(main_frame, text="Título del Escrito:").grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        self.titulo_var = tk.StringVar()
        self.titulo_entry = ttk.Entry(
            main_frame, 
            textvariable=self.titulo_var, 
            font=('TkDefaultFont', 10)
        )
        self.titulo_entry.grid(
            row=0, column=1, sticky=tk.EW, pady=(0, 15)
        )
        
        # Header type selection
        ttk.Label(main_frame, text="Tipo de Encabezado:").grid(
            row=1, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=1, column=1, sticky=tk.W, pady=(0, 15))
        
        self.header_type_var = tk.StringVar(value="PJN")
        
        self.pjn_radio = ttk.Radiobutton(
            header_frame,
            text="PJN (Poder Judicial de la Nación)",
            variable=self.header_type_var,
            value="PJN"
        )
        self.pjn_radio.pack(side=tk.LEFT, padx=(0, 15))
        
        self.scba_radio = ttk.Radiobutton(
            header_frame,
            text="SCBA (Suprema Corte de Buenos Aires)",
            variable=self.header_type_var,
            value="SCBA"
        )
        self.scba_radio.pack(side=tk.LEFT)
        
        # Body content field
        ttk.Label(main_frame, text="Cuerpo del Escrito (I.-):").grid(
            row=2, column=0, sticky=tk.NW, pady=(0, 5)
        )
        
        # Text area with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.grid(row=3, column=0, columnspan=2, sticky=tk.NSEW, pady=(0, 15))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.cuerpo_text = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=('TkDefaultFont', 10),
            height=15,
            width=60
        )
        self.cuerpo_text.grid(row=0, column=0, sticky=tk.NSEW)
        
        # Scrollbar for text area
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.cuerpo_text.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.cuerpo_text.config(yscrollcommand=scrollbar.set)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, sticky=tk.E, pady=(10, 0))
        
        # Buttons
        self.generar_btn = ttk.Button(
            button_frame,
            text="Generar y Guardar Borrador",
            command=self._generar_documento
        )
        self.generar_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        self.cancelar_btn = ttk.Button(
            button_frame,
            text="Cancelar",
            command=self._cancel
        )
        self.cancelar_btn.pack(side=tk.RIGHT)
    
    def _generar_documento(self):
        """Validate input and generate document."""
        # Get input values
        titulo = self.titulo_var.get().strip()
        cuerpo = self.cuerpo_text.get("1.0", tk.END).strip()
        header_type = self.header_type_var.get()
        
        # Validate required fields
        if not titulo:
            messagebox.showerror(
                "Error de Validación",
                "El título del escrito es obligatorio.",
                parent=self
            )
            self.titulo_entry.focus_set()
            return
        
        if not cuerpo:
            messagebox.showerror(
                "Error de Validación", 
                "El cuerpo del escrito es obligatorio.",
                parent=self
            )
            self.cuerpo_text.focus_set()
            return
        
        # Store result
        self.result = {
            'titulo': titulo,
            'cuerpo': cuerpo,
            'header_type': header_type
        }
        
        # Close dialog
        self.destroy()
    
    def _cancel(self):
        """Cancel dialog and discard input."""
        self.result = None
        self.destroy()
    
    def get_user_input(self):
        """
        Show dialog and return user input.
        
        Returns:
            dict: Dictionary with 'titulo', 'cuerpo', and 'header_type' keys if user confirmed,
                  None if user cancelled
        """
        # Wait for dialog to close
        self.wait_window()
        
        # Return result
        return self.result


# Convenience function for easy dialog usage
def show_escrito_generico_dialog(parent):
    """
    Show the generic document dialog and return user input.
    
    Args:
        parent: Parent window
        
    Returns:
        dict: User input data or None if cancelled
    """
    dialog = EscritoGenericoDialog(parent)
    return dialog.get_user_input()