# movimiento_dialog.py
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from decimal import Decimal, InvalidOperation
import datetime
import re

class MovimientoDialog:
    def __init__(self, parent, app_controller, caso_id, movimiento_data=None, tipo_movimiento=None):
        """
        Dialog for adding or editing financial movements.
        
        Args:
            parent: Parent window
            app_controller: Main application controller
            caso_id: ID of the case
            movimiento_data: Existing movement data for editing (None for new movement)
            tipo_movimiento: 'Ingreso' or 'Gasto' for new movements (ignored if editing)
        """
        self.parent = parent
        self.app_controller = app_controller
        self.caso_id = caso_id
        self.movimiento_data = movimiento_data
        self.is_editing = movimiento_data is not None
        self.result = None
        
        # Determine movement type
        if self.is_editing:
            self.tipo_movimiento = movimiento_data['tipo_movimiento']
        else:
            self.tipo_movimiento = tipo_movimiento or 'Ingreso'
        
        self._create_dialog()
        self._setup_validation()
        
        if self.is_editing:
            self._load_existing_data()
    
    def _create_dialog(self):
        """Create the dialog window and widgets."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Set title based on operation and type
        if self.is_editing:
            title = f"Editar {self.tipo_movimiento}"
        else:
            title = f"Registrar {self.tipo_movimiento}"
        
        self.dialog.title(title)
        self.dialog.geometry("480x400")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (480 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"480x400+{x}+{y}")
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label with color coding
        title_color = "#2E8B57" if self.tipo_movimiento == "Ingreso" else "#DC143C"  # Green for income, red for expense
        title_label = tk.Label(
            main_frame, 
            text=title, 
            font=("Arial", 14, "bold"),
            fg=title_color
        )
        title_label.pack(pady=(0, 20))
        
        # Form fields
        self._create_form_fields(main_frame)
        
        # Buttons
        self._create_buttons(main_frame)
        
        # Setup keyboard navigation and shortcuts
        self._setup_keyboard_navigation()
        
        # Focus on the first field
        self.fecha_entry.focus_set()
        
    def _setup_keyboard_navigation(self):
        """Setup comprehensive keyboard navigation for the dialog."""
        # Global dialog shortcuts
        self.dialog.bind('<Return>', lambda e: self._on_save())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())
        self.dialog.bind('<Control-s>', lambda e: self._on_save())
        self.dialog.bind('<Alt-F4>', lambda e: self._on_cancel())
        
        # Tab order setup
        self._setup_tab_order()
        
        # Field-specific shortcuts
        self.concepto_entry.bind('<Control-a>', self._select_all_text)
        self.notas_entry.bind('<Control-a>', self._select_all_text)
        self.monto_entry.bind('<Control-a>', lambda e: self.monto_entry.select_range(0, tk.END))
        
    def _setup_tab_order(self):
        """Setup proper tab order for accessibility."""
        # Define tab order
        tab_order = [
            self.fecha_entry,
            self.concepto_entry,
            self.monto_entry,
            self.notas_entry,
            self.save_button
        ]
        
        # Set up tab navigation
        for i, widget in enumerate(tab_order):
            next_widget = tab_order[(i + 1) % len(tab_order)]
            prev_widget = tab_order[i - 1]
            
            # Forward tab navigation
            if hasattr(widget, 'bind'):
                widget.bind('<Tab>', lambda e, next_w=next_widget: self._focus_widget(next_w))
                widget.bind('<Shift-Tab>', lambda e, prev_w=prev_widget: self._focus_widget(prev_w))
                
    def _focus_widget(self, widget):
        """Focus on a specific widget."""
        try:
            widget.focus_set()
            return 'break'  # Prevent default tab behavior
        except:
            pass
            
    def _select_all_text(self, event):
        """Select all text in a text widget."""
        try:
            event.widget.tag_add(tk.SEL, "1.0", tk.END)
            return 'break'
        except:
            pass
    
    def _create_form_fields(self, parent):
        """Create the form input fields."""
        # Create a frame for the form
        form_frame = ttk.Frame(parent)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Configure grid weights
        form_frame.columnconfigure(1, weight=1)
        
        row = 0
        
        # Date field
        ttk.Label(form_frame, text="Fecha:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        self.fecha_entry = DateEntry(
            form_frame,
            width=12,
            date_pattern="dd-mm-yyyy",
            locale="es_ES",
            state="readonly"
        )
        self.fecha_entry.grid(row=row, column=1, sticky=tk.W, pady=5)
        row += 1
        
        # Concept field
        ttk.Label(form_frame, text="Concepto:").grid(row=row, column=0, sticky=tk.NW, pady=5, padx=(0, 10))
        self.concepto_entry = tk.Text(
            form_frame,
            height=3,
            width=40,
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        self.concepto_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        # Add scrollbar for concept
        concepto_scroll = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=self.concepto_entry.yview)
        self.concepto_entry.configure(yscrollcommand=concepto_scroll.set)
        concepto_scroll.grid(row=row, column=2, sticky=tk.NS, pady=5)
        row += 1
        
        # Amount field
        ttk.Label(form_frame, text="Monto ($):").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        amount_frame = ttk.Frame(form_frame)
        amount_frame.grid(row=row, column=1, sticky=tk.W, pady=5)
        
        # Currency symbol
        ttk.Label(amount_frame, text="$", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.monto_entry = ttk.Entry(amount_frame, width=15, font=("Arial", 10))
        self.monto_entry.pack(side=tk.LEFT, padx=(5, 0))
        row += 1
        
        # Notes field
        ttk.Label(form_frame, text="Notas (opcional):").grid(row=row, column=0, sticky=tk.NW, pady=5, padx=(0, 10))
        self.notas_entry = tk.Text(
            form_frame,
            height=4,
            width=40,
            wrap=tk.WORD,
            font=("Arial", 9)
        )
        self.notas_entry.grid(row=row, column=1, sticky=tk.EW, pady=5)
        
        # Add scrollbar for notes
        notas_scroll = ttk.Scrollbar(form_frame, orient=tk.VERTICAL, command=self.notas_entry.yview)
        self.notas_entry.configure(yscrollcommand=notas_scroll.set)
        notas_scroll.grid(row=row, column=2, sticky=tk.NS, pady=5)
        row += 1
        
        # Movement type display (read-only)
        ttk.Label(form_frame, text="Tipo:").grid(row=row, column=0, sticky=tk.W, pady=5, padx=(0, 10))
        tipo_color = "#2E8B57" if self.tipo_movimiento == "Ingreso" else "#DC143C"
        tipo_label = tk.Label(
            form_frame, 
            text=self.tipo_movimiento,
            font=("Arial", 10, "bold"),
            fg=tipo_color
        )
        tipo_label.grid(row=row, column=1, sticky=tk.W, pady=5)
    
    def _create_buttons(self, parent):
        """Create the dialog buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Cancel button (pack first so it appears on the left)
        cancel_button = ttk.Button(
            button_frame,
            text="Cancelar",
            command=self._on_cancel,
            width=12
        )
        cancel_button.pack(side=tk.LEFT)
        
        # Save button
        save_text = "Actualizar" if self.is_editing else "Guardar"
        self.save_button = ttk.Button(
            button_frame,
            text=save_text,
            command=self._on_save,
            width=12
        )
        self.save_button.pack(side=tk.RIGHT)
    
    def _setup_validation(self):
        """Setup input validation."""
        # Register validation function for amount field
        vcmd = (self.dialog.register(self._validate_amount), '%P')
        self.monto_entry.config(validate='key', validatecommand=vcmd)
        
        # Bind events for real-time feedback
        self.concepto_entry.bind('<KeyRelease>', self._on_field_change)
        self.monto_entry.bind('<KeyRelease>', self._on_field_change)
    
    def _validate_amount(self, value):
        """Validate amount input - allow only numbers and decimal point."""
        if value == "":
            return True
        
        # Allow numbers, decimal point, and backspace
        pattern = r'^\d*\.?\d*$'
        return bool(re.match(pattern, value))
    
    def _on_field_change(self, event=None):
        """Handle field changes for validation feedback."""
        # This could be extended to provide real-time validation feedback
        pass
    
    def _load_existing_data(self):
        """Load existing movement data for editing."""
        if not self.movimiento_data:
            return
        
        # Set date
        if self.movimiento_data.get('fecha'):
            try:
                fecha_obj = datetime.datetime.strptime(str(self.movimiento_data['fecha']), '%Y-%m-%d').date()
                self.fecha_entry.set_date(fecha_obj)
            except (ValueError, TypeError):
                pass  # Keep default date
        
        # Set concept
        concepto = self.movimiento_data.get('concepto', '')
        self.concepto_entry.delete('1.0', tk.END)
        self.concepto_entry.insert('1.0', concepto)
        
        # Set amount
        monto = self.movimiento_data.get('monto', '')
        if monto:
            self.monto_entry.delete(0, tk.END)
            self.monto_entry.insert(0, str(monto))
        
        # Set notes
        notas = self.movimiento_data.get('notas', '')
        self.notas_entry.delete('1.0', tk.END)
        self.notas_entry.insert('1.0', notas)
    
    def _validate_form(self):
        """Validate all form fields with enhanced feedback."""
        errors = []
        warnings = []
        
        # Validate concept
        concepto = self.concepto_entry.get('1.0', tk.END).strip()
        if not concepto:
            errors.append("El concepto es obligatorio.")
        elif len(concepto) < 3:
            warnings.append("El concepto es muy corto. Considere ser más descriptivo.")
        elif len(concepto) > 500:
            errors.append("El concepto no puede exceder 500 caracteres.")
        
        # Validate amount
        monto_str = self.monto_entry.get().strip()
        if not monto_str:
            errors.append("El monto es obligatorio.")
        else:
            try:
                monto = Decimal(monto_str)
                if monto <= 0:
                    errors.append("El monto debe ser mayor a cero.")
                elif monto > Decimal('999999999.99'):
                    errors.append("El monto es demasiado grande.")
                elif monto > Decimal('100000.00'):
                    warnings.append("El monto es muy alto. Verifique que sea correcto.")
            except (InvalidOperation, ValueError):
                errors.append("El monto debe ser un número válido.")
        
        # Validate date
        try:
            fecha = self.fecha_entry.get_date()
            if not fecha:
                errors.append("La fecha es obligatoria.")
            else:
                # Check if date is in the future
                today = datetime.date.today()
                if fecha > today:
                    warnings.append("La fecha está en el futuro. ¿Es esto correcto?")
                # Check if date is very old
                elif (today - fecha).days > 365:
                    warnings.append("La fecha es de hace más de un año. ¿Es esto correcto?")
        except:
            errors.append("La fecha no es válida.")
        
        # Validate notes length
        notas = self.notas_entry.get('1.0', tk.END).strip()
        if len(notas) > 1000:
            errors.append("Las notas no pueden exceder 1000 caracteres.")
        
        return errors, warnings
        
    def _show_validation_feedback(self, errors, warnings):
        """Show validation feedback to the user."""
        if errors:
            error_message = "Por favor corrija los siguientes errores:\n\n"
            error_message += "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Errores de Validación", error_message, parent=self.dialog)
            return False
            
        if warnings:
            warning_message = "Advertencias:\n\n"
            warning_message += "\n".join(f"• {warning}" for warning in warnings)
            warning_message += "\n\n¿Desea continuar?"
            
            result = messagebox.askyesno("Advertencias", warning_message, parent=self.dialog)
            return result
            
        return True
    
    def _on_save(self):
        """Handle save button click with enhanced validation."""
        # Validate form
        errors, warnings = self._validate_form()
        if not self._show_validation_feedback(errors, warnings):
            return
        
        # Collect form data
        try:
            fecha = self.fecha_entry.get_date()
            concepto = self.concepto_entry.get('1.0', tk.END).strip()
            monto = Decimal(self.monto_entry.get().strip())
            notas = self.notas_entry.get('1.0', tk.END).strip()
            
            movement_data = {
                'caso_id': self.caso_id,
                'fecha': fecha.strftime('%Y-%m-%d'),
                'concepto': concepto,
                'tipo_movimiento': self.tipo_movimiento,
                'monto': monto,
                'notas': notas
            }
            
            # Save or update the movement
            success = False
            if self.is_editing:
                success = self.app_controller.db_crm.update_movimiento(
                    self.movimiento_data['id'], 
                    movement_data
                )
                operation = "actualizado"
            else:
                movement_id = self.app_controller.db_crm.add_movimiento(movement_data)
                success = movement_id is not None
                operation = "guardado"
            
            if success:
                self.result = movement_data
                messagebox.showinfo(
                    "Éxito", 
                    f"El {self.tipo_movimiento.lower()} ha sido {operation} correctamente.",
                    parent=self.dialog
                )
                self.dialog.destroy()
            else:
                messagebox.showerror(
                    "Error", 
                    f"No se pudo {operation.replace('ado', 'ar')} el {self.tipo_movimiento.lower()}. Intente nuevamente.",
                    parent=self.dialog
                )
                
        except Exception as e:
            messagebox.showerror(
                "Error Inesperado", 
                f"Ocurrió un error inesperado: {str(e)}",
                parent=self.dialog
            )
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and return the result."""
        # Wait for the dialog to be closed
        self.dialog.wait_window()
        return self.result

# Convenience functions for easier usage
def show_add_ingreso_dialog(parent, app_controller, caso_id):
    """Show dialog to add a new income movement."""
    dialog = MovimientoDialog(parent, app_controller, caso_id, tipo_movimiento="Ingreso")
    return dialog.show()

def show_add_gasto_dialog(parent, app_controller, caso_id):
    """Show dialog to add a new expense movement."""
    dialog = MovimientoDialog(parent, app_controller, caso_id, tipo_movimiento="Gasto")
    return dialog.show()

def show_edit_movimiento_dialog(parent, app_controller, movimiento_data):
    """Show dialog to edit an existing movement."""
    dialog = MovimientoDialog(parent, app_controller, movimiento_data['caso_id'], movimiento_data)
    return dialog.show()