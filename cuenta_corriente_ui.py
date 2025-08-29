# cuenta_corriente_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
import datetime
from movimiento_dialog import show_add_ingreso_dialog, show_add_gasto_dialog, show_edit_movimiento_dialog

class CuentaCorrienteTab(ttk.Frame):
    def __init__(self, parent, app_controller, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app_controller = app_controller
        self.db_crm = self.app_controller.db_crm
        self.selected_movimiento_id = None
        self.caso_id = None
        
        try:
            self._create_widgets()
            print("[Cuenta Corriente] Módulo económico inicializado correctamente")
        except Exception as e:
            print(f"[Cuenta Corriente] Error en inicialización: {e}")
            # Create a minimal error display
            error_label = tk.Label(self, text=f"Error inicializando módulo económico: {e}")
            error_label.pack(pady=20)
    
    def _create_widgets(self):
        """Create the main interface widgets."""
        # Configure main grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Summary section
        self.rowconfigure(1, weight=1)  # History section
        self.rowconfigure(2, weight=0)  # Actions section
        self.rowconfigure(3, weight=0)  # Help section
        
        # Create sections
        self._create_summary_section()
        self._create_history_section()
        self._create_actions_section()
        self._create_help_section()
    
    def _create_summary_section(self):
        """Create the financial summary section."""
        summary_frame = ttk.LabelFrame(self, text="Resumen Financiero", padding="15")
        summary_frame.grid(row=0, column=0, sticky='ew', padx=10, pady=(10, 5))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)
        summary_frame.columnconfigure(2, weight=1)
        
        # Total Income
        income_frame = ttk.Frame(summary_frame)
        income_frame.grid(row=0, column=0, padx=10, pady=5)
        
        ttk.Label(income_frame, text="Total Ingresos:", font=("Arial", 10)).pack()
        self.total_ingresos_label = tk.Label(
            income_frame, 
            text="$0.00", 
            font=("Arial", 12, "bold"),
            fg="#2E8B57"  # Green
        )
        self.total_ingresos_label.pack()
        
        # Total Expenses
        expenses_frame = ttk.Frame(summary_frame)
        expenses_frame.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(expenses_frame, text="Total Gastos:", font=("Arial", 10)).pack()
        self.total_gastos_label = tk.Label(
            expenses_frame, 
            text="$0.00", 
            font=("Arial", 12, "bold"),
            fg="#DC143C"  # Red
        )
        self.total_gastos_label.pack()
        
        # Current Balance
        balance_frame = ttk.Frame(summary_frame)
        balance_frame.grid(row=0, column=2, padx=10, pady=5)
        
        ttk.Label(balance_frame, text="Saldo Actual:", font=("Arial", 10)).pack()
        self.saldo_actual_label = tk.Label(
            balance_frame, 
            text="$0.00", 
            font=("Arial", 14, "bold")
        )
        self.saldo_actual_label.pack()
    
    def _create_history_section(self):
        """Create the transaction history section."""
        history_frame = ttk.LabelFrame(self, text="Historial de Movimientos", padding="10")
        history_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=5)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Create Treeview with hidden ID column
        columns = ('ID', 'Fecha', 'Concepto', 'Ingreso', 'Gasto')
        self.movimientos_tree = ttk.Treeview(
            history_frame, 
            columns=columns, 
            show='headings', 
            selectmode='browse'
        )
        
        # Configure columns
        self.movimientos_tree.heading('ID', text='ID')
        self.movimientos_tree.heading('Fecha', text='Fecha')
        self.movimientos_tree.heading('Concepto', text='Concepto')
        self.movimientos_tree.heading('Ingreso', text='Ingreso ($)')
        self.movimientos_tree.heading('Gasto', text='Gasto ($)')
        
        # Hide the ID column
        self.movimientos_tree.column('ID', width=0, stretch=False)
        self.movimientos_tree.column('Fecha', width=100, stretch=False, anchor=tk.CENTER)
        self.movimientos_tree.column('Concepto', width=300, stretch=True)
        self.movimientos_tree.column('Ingreso', width=100, stretch=False, anchor=tk.E)
        self.movimientos_tree.column('Gasto', width=100, stretch=False, anchor=tk.E)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.movimientos_tree.yview)
        self.movimientos_tree.configure(yscrollcommand=v_scrollbar.set)
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        
        h_scrollbar = ttk.Scrollbar(history_frame, orient=tk.HORIZONTAL, command=self.movimientos_tree.xview)
        self.movimientos_tree.configure(xscrollcommand=h_scrollbar.set)
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        self.movimientos_tree.grid(row=0, column=0, sticky='nsew')
        
        # Bind events
        self.movimientos_tree.bind('<<TreeviewSelect>>', self._on_movimiento_select)
        self.movimientos_tree.bind('<Double-1>', self._on_edit_movimiento)
        self.movimientos_tree.bind('<Button-3>', self._show_context_menu)  # Right click
    
    def _create_actions_section(self):
        """Create the action buttons section."""
        actions_frame = ttk.Frame(self)
        actions_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(5, 10))
        actions_frame.columnconfigure(0, weight=1)
        actions_frame.columnconfigure(1, weight=1)
        actions_frame.columnconfigure(2, weight=1)
        actions_frame.columnconfigure(3, weight=1)
        actions_frame.columnconfigure(4, weight=1)
        
        # Register Income button
        self.add_ingreso_btn = ttk.Button(
            actions_frame,
            text="Registrar Ingreso (F1)",
            command=self._add_ingreso,
            state=tk.DISABLED
        )
        self.add_ingreso_btn.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self._create_tooltip(self.add_ingreso_btn, "Agregar un nuevo ingreso al caso (F1)")
        
        # Register Expense button
        self.add_gasto_btn = ttk.Button(
            actions_frame,
            text="Registrar Gasto (F2)",
            command=self._add_gasto,
            state=tk.DISABLED
        )
        self.add_gasto_btn.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        self._create_tooltip(self.add_gasto_btn, "Agregar un nuevo gasto al caso (F2)")
        
        # Edit button
        self.edit_btn = ttk.Button(
            actions_frame,
            text="Editar (F3)",
            command=self._edit_movimiento,
            state=tk.DISABLED
        )
        self.edit_btn.grid(row=0, column=2, padx=5, pady=5, sticky='ew')
        self._create_tooltip(self.edit_btn, "Editar el movimiento seleccionado (F3)")
        
        # Delete button
        self.delete_btn = ttk.Button(
            actions_frame,
            text="Eliminar (Del)",
            command=self._delete_movimiento,
            state=tk.DISABLED
        )
        self.delete_btn.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
        self._create_tooltip(self.delete_btn, "Eliminar el movimiento seleccionado (Del)")
        
        # Refresh button
        self.refresh_btn = ttk.Button(
            actions_frame,
            text="Actualizar (F5)",
            command=self._refresh_data,
            state=tk.DISABLED
        )
        self.refresh_btn.grid(row=0, column=4, padx=5, pady=5, sticky='ew')
        self._create_tooltip(self.refresh_btn, "Actualizar datos financieros (F5)")
        
        # Setup keyboard navigation and shortcuts
        self._setup_keyboard_navigation()
        
    def _setup_keyboard_navigation(self):
        """Setup comprehensive keyboard navigation and shortcuts."""
        # Global keyboard shortcuts
        self.bind_all('<F1>', lambda e: self._handle_shortcut('add_ingreso'))
        self.bind_all('<F2>', lambda e: self._handle_shortcut('add_gasto'))
        self.bind_all('<F3>', lambda e: self._handle_shortcut('edit'))
        self.bind_all('<F5>', lambda e: self._handle_shortcut('refresh'))
        self.bind_all('<Delete>', lambda e: self._handle_shortcut('delete'))
        self.bind_all('<Control-r>', lambda e: self._handle_shortcut('refresh'))
        
        # Treeview navigation shortcuts
        self.movimientos_tree.bind('<Return>', lambda e: self._edit_movimiento())
        self.movimientos_tree.bind('<space>', lambda e: self._edit_movimiento())
        self.movimientos_tree.bind('<Up>', self._on_tree_navigation)
        self.movimientos_tree.bind('<Down>', self._on_tree_navigation)
        self.movimientos_tree.bind('<Home>', lambda e: self._select_first_item())
        self.movimientos_tree.bind('<End>', lambda e: self._select_last_item())
        
        # Tab navigation improvements
        self.movimientos_tree.bind('<Tab>', self._on_tab_navigation)
        self.movimientos_tree.bind('<Shift-Tab>', self._on_shift_tab_navigation)
        
    def _handle_shortcut(self, action):
        """Handle keyboard shortcuts with proper state checking."""
        if action == 'add_ingreso' and self.add_ingreso_btn['state'] == 'normal':
            self._add_ingreso()
        elif action == 'add_gasto' and self.add_gasto_btn['state'] == 'normal':
            self._add_gasto()
        elif action == 'edit' and self.edit_btn['state'] == 'normal':
            self._edit_movimiento()
        elif action == 'delete' and self.delete_btn['state'] == 'normal':
            self._delete_movimiento()
        elif action == 'refresh' and self.refresh_btn['state'] == 'normal':
            self._refresh_data()
            
    def _on_tree_navigation(self, event):
        """Handle tree navigation to update selection properly."""
        # Let the default navigation happen first
        self.after_idle(self._on_movimiento_select)
        
    def _select_first_item(self):
        """Select the first item in the tree."""
        children = self.movimientos_tree.get_children()
        if children:
            first_item = children[0]
            # Don't select the "no data" message
            values = self.movimientos_tree.item(first_item, 'values')
            if values and values[0] != 'no_data':
                self.movimientos_tree.selection_set(first_item)
                self.movimientos_tree.focus(first_item)
                self._on_movimiento_select()
                
    def _select_last_item(self):
        """Select the last item in the tree."""
        children = self.movimientos_tree.get_children()
        if children:
            last_item = children[-1]
            # Don't select the "no data" message
            values = self.movimientos_tree.item(last_item, 'values')
            if values and values[0] != 'no_data':
                self.movimientos_tree.selection_set(last_item)
                self.movimientos_tree.focus(last_item)
                self._on_movimiento_select()
                
    def _on_tab_navigation(self, event):
        """Handle Tab key navigation from treeview to buttons."""
        self.add_ingreso_btn.focus_set()
        return 'break'  # Prevent default tab behavior
        
    def _on_shift_tab_navigation(self, event):
        """Handle Shift+Tab navigation from treeview."""
        # Focus on the last focusable element before the tree
        return 'break'  # Prevent default behavior
        
    def _refresh_data(self):
        """Refresh financial data manually."""
        if self.caso_id:
            self.load_movimientos(self.caso_id)
    
    def load_movimientos(self, caso_id, show_loading=True):
        """Load financial movements for a case with performance optimizations."""
        self.caso_id = caso_id
        self.selected_movimiento_id = None
        
        # Show loading indicator for large datasets
        if show_loading:
            self._show_loading_indicator()
        
        try:
            # Clear existing data efficiently
            self.movimientos_tree.delete(*self.movimientos_tree.get_children())
            
            if not caso_id:
                self._update_summary(0, 0, 0)
                self._update_button_states()
                return
            
            # Load movements with pagination for large datasets
            movimientos = self.db_crm.get_movimientos_by_caso_id(caso_id)
            
            # Performance optimization: batch insert for large datasets
            try:
                movimientos_list = list(movimientos) if movimientos else []
                if len(movimientos_list) > 100:
                    self._populate_treeview_batch(movimientos_list)
                else:
                    self._populate_treeview_standard(movimientos_list)
            except (TypeError, AttributeError):
                # Handle case where movimientos is not iterable
                self._show_no_data_message()
            
            # Update financial summary
            resumen = self.db_crm.get_resumen_financiero_caso(caso_id)
            self._update_summary(
                resumen['total_ingresos'],
                resumen['total_gastos'],
                resumen['saldo_actual']
            )
            
        except Exception as e:
            print(f"Error loading movements: {e}")
            # Don't show error dialog in production to avoid interrupting user workflow
            # messagebox.showerror("Error", f"Error al cargar movimientos: {str(e)}", parent=self)
        finally:
            # Hide loading indicator
            if show_loading:
                try:
                    self._hide_loading_indicator()
                except:
                    pass  # Ignore errors in cleanup
            
            # Always update button states, even if there was an error
            try:
                self._update_button_states()
                print(f"[Cuenta Corriente] Botones actualizados para caso {caso_id}")
            except Exception as e:
                print(f"[Cuenta Corriente] Error actualizando botones: {e}")
            
    def _show_loading_indicator(self):
        """Show loading indicator for better user experience."""
        # Create a temporary loading message
        self.movimientos_tree.insert('', tk.END, values=(
            'loading', "", "Cargando movimientos...", "", ""
        ))
        self.update_idletasks()
        
    def _hide_loading_indicator(self):
        """Hide loading indicator."""
        # Remove loading message if it exists
        for item in self.movimientos_tree.get_children():
            values = self.movimientos_tree.item(item, 'values')
            if values and values[0] == 'loading':
                self.movimientos_tree.delete(item)
                break
                
    def _populate_treeview_standard(self, movimientos):
        """Standard population for smaller datasets."""
        try:
            movimientos_list = list(movimientos) if movimientos else []
        except TypeError:
            movimientos_list = []
            
        if movimientos_list:
            for mov in movimientos_list:
                self._insert_movement_row(mov)
        else:
            self._show_no_data_message()
            
    def _populate_treeview_batch(self, movimientos):
        """Batch population for large datasets with progress indication."""
        if not movimientos:
            self._show_no_data_message()
            return
            
        # Check if movimientos is a list-like object
        try:
            movimientos_list = list(movimientos)
        except TypeError:
            # If it's not iterable, treat as empty
            self._show_no_data_message()
            return
            
        batch_size = 50
        total_batches = (len(movimientos_list) + batch_size - 1) // batch_size
        
        for i in range(0, len(movimientos_list), batch_size):
            batch = movimientos_list[i:i + batch_size]
            
            # Process batch
            for mov in batch:
                self._insert_movement_row(mov)
            
            # Update progress and allow UI to refresh
            current_batch = (i // batch_size) + 1
            if current_batch % 5 == 0:  # Update every 5 batches
                try:
                    self.update_idletasks()
                except:
                    pass  # Ignore if widget is destroyed
                
    def _insert_movement_row(self, mov):
        """Insert a single movement row into the treeview."""
        fecha_display = self._format_date(mov['fecha'])
        concepto = mov['concepto'][:50] + "..." if len(mov['concepto']) > 50 else mov['concepto']
        
        if mov['tipo_movimiento'] == 'Ingreso':
            ingreso = f"${mov['monto']:.2f}"
            gasto = ""
        else:
            ingreso = ""
            gasto = f"${mov['monto']:.2f}"
        
        # Insert with ID in the first (hidden) column
        self.movimientos_tree.insert('', tk.END, values=(
            mov['id'], fecha_display, concepto, ingreso, gasto
        ))
        
    def _show_no_data_message(self):
        """Show message when there are no movements."""
        self.movimientos_tree.insert('', tk.END, values=(
            'no_data', "", "No hay movimientos registrados", "", ""
        ))
    
    def _format_date(self, fecha):
        """Format date for display."""
        if isinstance(fecha, str):
            try:
                fecha_obj = datetime.datetime.strptime(fecha, '%Y-%m-%d').date()
                return fecha_obj.strftime('%d/%m/%Y')
            except ValueError:
                return fecha
        elif hasattr(fecha, 'strftime'):
            return fecha.strftime('%d/%m/%Y')
        else:
            return str(fecha)
    
    def _update_summary(self, total_ingresos, total_gastos, saldo_actual):
        """Update the financial summary display."""
        self.total_ingresos_label.config(text=f"${total_ingresos:.2f}")
        self.total_gastos_label.config(text=f"${total_gastos:.2f}")
        
        # Color code the balance
        if saldo_actual > 0:
            color = "#2E8B57"  # Green
        elif saldo_actual < 0:
            color = "#DC143C"  # Red
        else:
            color = "#000000"  # Black
        
        self.saldo_actual_label.config(text=f"${saldo_actual:.2f}", fg=color)
    
    def _update_button_states(self):
        """Update the state of action buttons with accessibility support."""
        # Add buttons are enabled if there's a case loaded
        add_state = tk.NORMAL if self.caso_id else tk.DISABLED
        self.add_ingreso_btn.config(state=add_state)
        self.add_gasto_btn.config(state=add_state)
        self.refresh_btn.config(state=add_state)
        
        # Edit/Delete buttons are enabled if there's a movement selected
        edit_delete_state = tk.NORMAL if self.selected_movimiento_id else tk.DISABLED
        self.edit_btn.config(state=edit_delete_state)
        self.delete_btn.config(state=edit_delete_state)
        
        # Update accessibility attributes
        self._update_accessibility_attributes()
    
    def _on_movimiento_select(self, event=None):
        """Handle movement selection in treeview."""
        selected_items = self.movimientos_tree.selection()
        if selected_items:
            item = selected_items[0]
            # Get the movement ID from the first (hidden) column
            values = self.movimientos_tree.item(item, 'values')
            if values:
                movement_id_str = values[0]  # First column contains the ID
                
                # Don't allow selection of the "no data" message
                if movement_id_str == 'no_data':
                    self.movimientos_tree.selection_remove(item)
                    self.selected_movimiento_id = None
                else:
                    try:
                        self.selected_movimiento_id = int(movement_id_str)
                    except (ValueError, TypeError):
                        self.selected_movimiento_id = None
            else:
                self.selected_movimiento_id = None
        else:
            self.selected_movimiento_id = None
        
        self._update_button_states()
    
    def _add_ingreso(self):
        """Add a new income movement."""
        if not self.caso_id:
            return
        
        result = show_add_ingreso_dialog(self, self.app_controller, self.caso_id)
        if result:
            self.load_movimientos(self.caso_id)  # Refresh the display
            # Notify parent window to refresh other tabs if needed
            if hasattr(self.app_controller, 'refresh_case_window'):
                self.app_controller.refresh_case_window(self.caso_id)
    
    def _add_gasto(self):
        """Add a new expense movement."""
        if not self.caso_id:
            return
        
        result = show_add_gasto_dialog(self, self.app_controller, self.caso_id)
        if result:
            self.load_movimientos(self.caso_id)  # Refresh the display
            # Notify parent window to refresh other tabs if needed
            if hasattr(self.app_controller, 'refresh_case_window'):
                self.app_controller.refresh_case_window(self.caso_id)
    
    def _edit_movimiento(self):
        """Edit the selected movement."""
        if not self.selected_movimiento_id:
            return
        
        # Get movement data
        movimiento_data = self.db_crm.get_movimiento_by_id(self.selected_movimiento_id)
        if not movimiento_data:
            messagebox.showerror("Error", "No se pudo cargar los datos del movimiento.", parent=self)
            return
        
        result = show_edit_movimiento_dialog(self, self.app_controller, movimiento_data)
        if result:
            self.load_movimientos(self.caso_id)  # Refresh the display
            # Notify parent window to refresh other tabs if needed
            if hasattr(self.app_controller, 'refresh_case_window'):
                self.app_controller.refresh_case_window(self.caso_id)
    
    def _on_edit_movimiento(self, event=None):
        """Handle double-click to edit movement."""
        self._edit_movimiento()
    
    def _delete_movimiento(self):
        """Delete the selected movement."""
        if not self.selected_movimiento_id:
            return
        
        # Get movement data for confirmation
        movimiento_data = self.db_crm.get_movimiento_by_id(self.selected_movimiento_id)
        if not movimiento_data:
            messagebox.showerror("Error", "No se pudo cargar los datos del movimiento.", parent=self)
            return
        
        # Confirm deletion
        tipo = movimiento_data['tipo_movimiento'].lower()
        concepto = movimiento_data['concepto']
        monto = movimiento_data['monto']
        
        confirm_msg = f"¿Está seguro de que desea eliminar este {tipo}?\n\n"
        confirm_msg += f"Concepto: {concepto}\n"
        confirm_msg += f"Monto: ${monto}\n\n"
        confirm_msg += "Esta acción no se puede deshacer."
        
        if messagebox.askyesno("Confirmar Eliminación", confirm_msg, parent=self):
            success = self.db_crm.delete_movimiento(self.selected_movimiento_id)
            if success:
                messagebox.showinfo("Éxito", f"El {tipo} ha sido eliminado correctamente.", parent=self)
                self.load_movimientos(self.caso_id)  # Refresh the display
                # Notify parent window to refresh other tabs if needed
                if hasattr(self.app_controller, 'refresh_case_window'):
                    self.app_controller.refresh_case_window(self.caso_id)
            else:
                messagebox.showerror("Error", f"No se pudo eliminar el {tipo}.", parent=self)
    
    def _show_context_menu(self, event):
        """Show context menu on right-click."""
        if not self.selected_movimiento_id:
            return
        
        # Create context menu
        context_menu = tk.Menu(self, tearoff=0)
        context_menu.add_command(label="Editar", command=self._edit_movimiento)
        context_menu.add_separator()
        context_menu.add_command(label="Eliminar", command=self._delete_movimiento)
        
        # Show menu
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def refresh_financial_summary(self):
        """Refresh only the financial summary without reloading all data."""
        if not self.caso_id:
            return
        
        resumen = self.db_crm.get_resumen_financiero_caso(self.caso_id)
        self._update_summary(
            resumen['total_ingresos'],
            resumen['total_gastos'],
            resumen['saldo_actual']
        )
    
    def _update_accessibility_attributes(self):
        """Update accessibility attributes for screen readers."""
        # Set accessible names and descriptions
        if self.caso_id:
            case_info = f"Caso ID {self.caso_id}"
            self.add_ingreso_btn.configure(text="Registrar Ingreso (F1)")
            self.add_gasto_btn.configure(text="Registrar Gasto (F2)")
            self.refresh_btn.configure(text="Actualizar (F5)")
        else:
            self.add_ingreso_btn.configure(text="Registrar Ingreso (F1) - Sin caso")
            self.add_gasto_btn.configure(text="Registrar Gasto (F2) - Sin caso")
            self.refresh_btn.configure(text="Actualizar (F5) - Sin caso")
            
        # Update edit/delete button text based on selection
        if self.selected_movimiento_id:
            self.edit_btn.configure(text="Editar (F3)")
            self.delete_btn.configure(text="Eliminar (Del)")
        else:
            self.edit_btn.configure(text="Editar (F3) - Sin selección")
            self.delete_btn.configure(text="Eliminar (Del) - Sin selección")
    
    def _create_tooltip(self, widget, text):
        """Create an enhanced tooltip for a widget with better positioning."""
        def on_enter(event):
            # Don't show tooltip if widget is disabled
            if widget['state'] == 'disabled':
                return
                
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            
            # Better positioning to avoid screen edges
            x = event.x_root + 10
            y = event.y_root + 10
            
            # Adjust if tooltip would go off screen
            screen_width = tooltip.winfo_screenwidth()
            screen_height = tooltip.winfo_screenheight()
            
            if x + 200 > screen_width:
                x = event.x_root - 210
            if y + 50 > screen_height:
                y = event.y_root - 60
                
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Enhanced tooltip styling
            frame = tk.Frame(tooltip, background="lightyellow", relief="solid", borderwidth=1)
            frame.pack()
            
            label = tk.Label(
                frame,
                text=text,
                background="lightyellow",
                font=("Arial", 9),
                padx=8,
                pady=4,
                justify=tk.LEFT
            )
            label.pack()
            
            widget.tooltip = tooltip
            
            # Auto-hide tooltip after 5 seconds
            tooltip.after(5000, lambda: on_leave(None))
        
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                try:
                    widget.tooltip.destroy()
                    del widget.tooltip
                except:
                    pass  # Tooltip might already be destroyed
        
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
        
    def _create_help_section(self):
        """Create a help section with keyboard shortcuts and usage tips."""
        help_frame = ttk.LabelFrame(self, text="Ayuda y Atajos de Teclado", padding="10")
        help_frame.grid(row=3, column=0, sticky='ew', padx=10, pady=(0, 10))
        
        help_text = """
Atajos de Teclado:
• F1: Registrar Ingreso
• F2: Registrar Gasto  
• F3: Editar movimiento seleccionado
• F5 o Ctrl+R: Actualizar datos
• Del: Eliminar movimiento seleccionado
• Enter/Espacio: Editar movimiento (en lista)
• Inicio/Fin: Ir al primer/último movimiento
• ↑/↓: Navegar por la lista

Consejos:
• Haga doble clic en un movimiento para editarlo
• Use clic derecho para ver opciones adicionales
• Los saldos positivos se muestran en verde, negativos en rojo
        """.strip()
        
        help_label = tk.Label(
            help_frame,
            text=help_text,
            font=("Arial", 8),
            justify=tk.LEFT,
            anchor=tk.NW
        )
        help_label.pack(fill=tk.BOTH, expand=True)
        
        # Toggle button to show/hide help
        self.help_visible = False
        self.toggle_help_btn = ttk.Button(
            help_frame,
            text="Ocultar Ayuda",
            command=self._toggle_help
        )
        self.toggle_help_btn.pack(pady=(5, 0))
        
    def _toggle_help(self):
        """Toggle help section visibility."""
        help_frame = self.grid_slaves(row=3, column=0)[0] if self.grid_slaves(row=3, column=0) else None
        if help_frame:
            if self.help_visible:
                help_frame.grid_remove()
                self.toggle_help_btn.configure(text="Mostrar Ayuda")
                self.help_visible = False
            else:
                help_frame.grid()
                self.toggle_help_btn.configure(text="Ocultar Ayuda")
                self.help_visible = True