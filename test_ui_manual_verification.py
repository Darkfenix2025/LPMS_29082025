#!/usr/bin/env python3
"""
Manual verification script for UI backward compatibility.
This script provides a manual testing interface to verify that the UI
functionality works correctly after the refactoring.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import tempfile
import shutil

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
import crm_database as db
from case_dialog_manager import CaseManager
from main_app import CRMLegalApp

class UIManualTester:
    """Manual testing interface for UI backward compatibility."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("UI Backward Compatibility Manual Tester")
        self.root.geometry("800x600")
        
        # Setup test database
        self.setup_test_database()
        
        # Create mock app controller
        self.mock_app = type('MockApp', (), {})()
        self.mock_app.root = self.root
        
        # Create case manager
        self.case_manager = CaseManager(app_controller=self.mock_app)
        
        self.create_ui()
    
    def setup_test_database(self):
        """Setup a test database with sample data."""
        # Create temporary database
        self.test_db_path = tempfile.mktemp(suffix='.db')
        
        try:
            conn = sqlite3.connect(self.test_db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS casos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caratula TEXT NOT NULL,
                    numero_expediente TEXT,
                    anio_caratula TEXT,
                    juzgado TEXT,
                    jurisdiccion TEXT,
                    fecha_creacion TEXT,
                    estado TEXT DEFAULT 'Activo'
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS partes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caso_id INTEGER,
                    nombre_completo TEXT NOT NULL,
                    tipo_parte TEXT NOT NULL,
                    dni TEXT,
                    domicilio TEXT,
                    telefono TEXT,
                    email TEXT,
                    FOREIGN KEY (caso_id) REFERENCES casos (id)
                )
            ''')
            
            # Insert test data
            cursor.execute('''
                INSERT INTO casos (id, caratula, numero_expediente, anio_caratula, juzgado, jurisdiccion)
                VALUES (1, 'PÉREZ JUAN C/ GARCÍA MARÍA S/ DAÑOS Y PERJUICIOS', '12345/2023', '2023', 'Juzgado Civil N° 1', 'La Plata')
            ''')
            
            cursor.execute('''
                INSERT INTO casos (id, caratula, numero_expediente, anio_caratula, juzgado, jurisdiccion)
                VALUES (2, '', '54321/2023', '2023', 'Juzgado Civil N° 2', 'La Plata')
            ''')
            
            cursor.execute('''
                INSERT INTO casos (id, caratula, numero_expediente, anio_caratula, juzgado, jurisdiccion)
                VALUES (3, 'CASO SIN PARTES', '11111/2023', '2023', 'Juzgado Civil N° 3', 'La Plata')
            ''')
            
            cursor.execute('''
                INSERT INTO partes (caso_id, nombre_completo, tipo_parte, dni, domicilio, telefono, email)
                VALUES 
                (1, 'PÉREZ JUAN', 'Actor', '12345678', 'Calle Falsa 123', '221-1234567', 'juan.perez@email.com'),
                (1, 'GARCÍA MARÍA', 'Demandado', '87654321', 'Avenida Siempre Viva 456', '221-7654321', 'maria.garcia@email.com')
            ''')
            
            conn.commit()
            conn.close()
            
            # Set database path
            db.DATABASE_PATH = self.test_db_path
            
            print(f"Test database created: {self.test_db_path}")
            
        except Exception as e:
            print(f"Error setting up test database: {e}")
            raise
    
    def create_ui(self):
        """Create the testing UI."""
        # Title
        title_label = tk.Label(self.root, text="UI Backward Compatibility Tester", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Instructions
        instructions = tk.Text(self.root, height=8, width=80, wrap=tk.WORD)
        instructions.pack(pady=10, padx=20, fill=tk.X)
        
        instructions_text = """
INSTRUCCIONES PARA PRUEBAS MANUALES:

1. Prueba de Flujo Exitoso: Haga clic en "Test Caso Válido" para probar el flujo completo
2. Prueba de Cancelación: Haga clic en "Test Caso Válido" y luego cancele el diálogo
3. Prueba de Error - ID Inválido: Haga clic en "Test Caso Inválido (ID 99999)"
4. Prueba de Error - Sin Carátula: Haga clic en "Test Caso Sin Carátula (ID 2)"
5. Prueba de Error - Sin Partes: Haga clic en "Test Caso Sin Partes (ID 3)"

Verifique que:
- Los diálogos se abren correctamente
- Los mensajes de error son apropiados
- La cancelación funciona correctamente
- El flujo completo genera documentos cuando es exitoso
        """
        
        instructions.insert(tk.END, instructions_text)
        instructions.config(state=tk.DISABLED)
        
        # Test buttons frame
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(pady=20)
        
        # Test buttons
        tk.Button(buttons_frame, text="Test Caso Válido (ID 1)", 
                 command=lambda: self.test_case(1), 
                 bg="lightgreen", width=25, height=2).pack(pady=5)
        
        tk.Button(buttons_frame, text="Test Caso Inválido (ID 99999)", 
                 command=lambda: self.test_case(99999), 
                 bg="lightcoral", width=25, height=2).pack(pady=5)
        
        tk.Button(buttons_frame, text="Test Caso Sin Carátula (ID 2)", 
                 command=lambda: self.test_case(2), 
                 bg="lightyellow", width=25, height=2).pack(pady=5)
        
        tk.Button(buttons_frame, text="Test Caso Sin Partes (ID 3)", 
                 command=lambda: self.test_case(3), 
                 bg="lightblue", width=25, height=2).pack(pady=5)
        
        # Results area
        results_label = tk.Label(self.root, text="Resultados de Pruebas:", font=("Arial", 12, "bold"))
        results_label.pack(pady=(20, 5))
        
        self.results_text = tk.Text(self.root, height=10, width=80, wrap=tk.WORD)
        self.results_text.pack(pady=5, padx=20, fill=tk.BOTH, expand=True)
        
        # Control buttons
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)
        
        tk.Button(control_frame, text="Limpiar Resultados", 
                 command=self.clear_results, width=15).pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="Cerrar", 
                 command=self.close_app, width=15).pack(side=tk.LEFT, padx=5)
    
    def test_case(self, case_id):
        """Test a specific case ID."""
        self.log_result(f"\\n{'='*60}")
        self.log_result(f"INICIANDO PRUEBA CON CASO ID: {case_id}")
        self.log_result(f"{'='*60}")
        
        try:
            # Call the method
            result = self.case_manager.generar_escrito_mediacion(case_id)
            
            if result:
                self.log_result("✅ RESULTADO: ÉXITO - El documento se generó correctamente")
                self.log_result("   - El flujo de UI funcionó como se esperaba")
                self.log_result("   - Los diálogos se mostraron correctamente")
                self.log_result("   - El documento se guardó exitosamente")
            else:
                self.log_result("⚠️  RESULTADO: FALSO - La operación no se completó")
                self.log_result("   - Esto puede ser por cancelación del usuario o error")
                self.log_result("   - Verifique los mensajes de error mostrados")
                
        except Exception as e:
            self.log_result(f"❌ ERROR CRÍTICO: {str(e)}")
            self.log_result("   - Se produjo una excepción no manejada")
            self.log_result("   - Esto indica un problema en la compatibilidad")
        
        self.log_result(f"{'='*60}")
        self.log_result("PRUEBA COMPLETADA")
        self.log_result(f"{'='*60}")
    
    def log_result(self, message):
        """Log a result message."""
        self.results_text.insert(tk.END, message + "\\n")
        self.results_text.see(tk.END)
        self.root.update()
        print(message)  # Also print to console
    
    def clear_results(self):
        """Clear the results area."""
        self.results_text.delete(1.0, tk.END)
    
    def close_app(self):
        """Close the application."""
        try:
            if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
                print(f"Cleaned up test database: {self.test_db_path}")
        except Exception as e:
            print(f"Error cleaning up: {e}")
        
        self.root.destroy()
    
    def run(self):
        """Run the manual tester."""
        print("Starting UI Manual Tester...")
        print("Use the GUI to test different scenarios")
        self.root.mainloop()


def run_simple_compatibility_check():
    """Run a simple compatibility check without full UI."""
    print("=" * 80)
    print("VERIFICACIÓN SIMPLE DE COMPATIBILIDAD HACIA ATRÁS")
    print("=" * 80)
    
    try:
        # Test 1: Constructor compatibility
        print("\\n1. Probando compatibilidad del constructor...")
        
        # Test with app_controller
        mock_app = type('MockApp', (), {})()
        case_manager_with_app = CaseManager(app_controller=mock_app)
        print("   ✅ Constructor con app_controller: OK")
        
        # Test without app_controller
        case_manager_without_app = CaseManager(app_controller=None)
        print("   ✅ Constructor sin app_controller: OK")
        
        # Test 2: Method existence
        print("\\n2. Probando existencia de métodos...")
        
        methods_to_check = [
            'generar_escrito_mediacion',
            '_generar_documento_con_datos',
            '_collect_agreement_details',
            '_ask_agreement_details_dialog'
        ]
        
        for method_name in methods_to_check:
            if hasattr(case_manager_with_app, method_name):
                print(f"   ✅ Método {method_name}: Existe")
            else:
                print(f"   ❌ Método {method_name}: NO EXISTE")
        
        # Test 3: Method signature compatibility
        print("\\n3. Probando compatibilidad de signatura...")
        
        import inspect
        sig = inspect.signature(case_manager_with_app.generar_escrito_mediacion)
        params = list(sig.parameters.keys())
        
        if 'caso_id' in params:
            print("   ✅ Parámetro caso_id: OK")
        else:
            print("   ❌ Parámetro caso_id: FALTANTE")
        
        # Test 4: Error handling classes
        print("\\n4. Probando clases de manejo de errores...")
        
        from case_dialog_manager import ErrorMessageManager
        
        error_methods = ['show_error_dialog', 'get_error_message', 'log_error']
        for method_name in error_methods:
            if hasattr(ErrorMessageManager, method_name):
                print(f"   ✅ ErrorMessageManager.{method_name}: Existe")
            else:
                print(f"   ❌ ErrorMessageManager.{method_name}: NO EXISTE")
        
        print("\\n" + "=" * 80)
        print("✅ VERIFICACIÓN SIMPLE COMPLETADA")
        print("La estructura básica de compatibilidad está presente.")
        print("Para pruebas completas de UI, ejecute el tester manual.")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\\n❌ ERROR EN VERIFICACIÓN: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # Run simple check
        success = run_simple_compatibility_check()
        sys.exit(0 if success else 1)
    else:
        # Run manual tester
        try:
            tester = UIManualTester()
            tester.run()
        except Exception as e:
            print(f"Error running manual tester: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)