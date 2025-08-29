#!/usr/bin/env python3
"""
Integration test for UI backward compatibility.
This test creates a real Tkinter application and tests the actual UI flow.
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import sqlite3
import tempfile
import threading
import time
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
import crm_database as db
from case_dialog_manager import CaseManager

class UIIntegrationTest:
    """Integration test for UI backward compatibility."""
    
    def __init__(self):
        self.test_results = []
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Setup test environment with real database and UI."""
        # Create test database
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.setup_test_database()
        
        # Create real Tkinter root
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window
        
        # Create mock app controller with real root
        self.mock_app = type('MockApp', (), {})()
        self.mock_app.root = self.root
        
        # Create case manager
        self.case_manager = CaseManager(app_controller=self.mock_app)
    
    def setup_test_database(self):
        """Setup test database with sample data."""
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
                INSERT INTO partes (caso_id, nombre_completo, tipo_parte, dni, domicilio, telefono, email)
                VALUES 
                (1, 'PÉREZ JUAN', 'Actor', '12345678', 'Calle Falsa 123', '221-1234567', 'juan.perez@email.com'),
                (1, 'GARCÍA MARÍA', 'Demandado', '87654321', 'Avenida Siempre Viva 456', '221-7654321', 'maria.garcia@email.com')
            ''')
            
            conn.commit()
            conn.close()
            
            # Set database path
            db.DATABASE_PATH = self.test_db_path
            
        except Exception as e:
            print(f"Error setting up test database: {e}")
            raise
    
    def test_ui_method_calls(self):
        """Test that UI methods are called correctly."""
        print("\\n" + "="*60)
        print("PRUEBA: Verificación de llamadas a métodos de UI")
        print("="*60)
        
        test_passed = True
        
        try:
            # Test 1: Verify method exists and is callable
            if not hasattr(self.case_manager, 'generar_escrito_mediacion'):
                self.test_results.append("❌ Método generar_escrito_mediacion no existe")
                test_passed = False
            else:
                self.test_results.append("✅ Método generar_escrito_mediacion existe")
            
            if not callable(getattr(self.case_manager, 'generar_escrito_mediacion', None)):
                self.test_results.append("❌ Método generar_escrito_mediacion no es callable")
                test_passed = False
            else:
                self.test_results.append("✅ Método generar_escrito_mediacion es callable")
            
            # Test 2: Verify helper methods exist
            helper_methods = [
                '_generar_documento_con_datos',
                '_collect_agreement_details',
                '_ask_agreement_details_dialog',
                '_validate_initial_parameters',
                '_validate_system_dependencies'
            ]
            
            for method_name in helper_methods:
                if hasattr(self.case_manager, method_name):
                    self.test_results.append(f"✅ Método helper {method_name} existe")
                else:
                    self.test_results.append(f"❌ Método helper {method_name} NO existe")
                    test_passed = False
            
            # Test 3: Test method signature
            import inspect
            sig = inspect.signature(self.case_manager.generar_escrito_mediacion)
            params = list(sig.parameters.keys())
            
            if 'caso_id' in params:
                self.test_results.append("✅ Parámetro caso_id presente en signatura")
            else:
                self.test_results.append("❌ Parámetro caso_id FALTANTE en signatura")
                test_passed = False
            
            if len(params) == 1:  # Should only have caso_id
                self.test_results.append("✅ Signatura del método es correcta (solo caso_id)")
            else:
                self.test_results.append(f"⚠️  Signatura tiene {len(params)} parámetros: {params}")
            
        except Exception as e:
            self.test_results.append(f"❌ Error en prueba de métodos UI: {e}")
            test_passed = False
        
        return test_passed
    
    def test_error_handling_integration(self):
        """Test error handling integration."""
        print("\\n" + "="*60)
        print("PRUEBA: Integración de manejo de errores")
        print("="*60)
        
        test_passed = True
        
        try:
            # Test with invalid case ID
            with patch('tkinter.messagebox.showerror') as mock_error:
                result = self.case_manager.generar_escrito_mediacion(99999)
                
                if result == False:
                    self.test_results.append("✅ Método retorna False para caso inválido")
                else:
                    self.test_results.append(f"❌ Método retorna {result} para caso inválido (esperado: False)")
                    test_passed = False
                
                # Check if error dialog was called
                if mock_error.called:
                    self.test_results.append("✅ Diálogo de error fue llamado para caso inválido")
                else:
                    self.test_results.append("⚠️  Diálogo de error NO fue llamado (puede ser por validación temprana)")
        
        except Exception as e:
            self.test_results.append(f"❌ Error en prueba de manejo de errores: {e}")
            test_passed = False
        
        return test_passed
    
    def test_dialog_flow_simulation(self):
        """Test dialog flow with mocked user interactions."""
        print("\\n" + "="*60)
        print("PRUEBA: Simulación de flujo de diálogos")
        print("="*60)
        
        test_passed = True
        
        try:
            # Mock the agreement details dialog to simulate user input
            mock_agreement_details = {
                'monto_compensacion_numeros': '150000.50',
                'monto_compensacion_letras': 'CIENTO CINCUENTA MIL PESOS CON CINCUENTA CENTAVOS',
                'plazo_pago_dias': '30',
                'plazo_pago_letras': 'TREINTA',
                'banco_actor': 'Banco Nación',
                'cbu_actor': '1234567890123456789012',
                'alias_actor': 'mi.alias.mp',
                'cuit_actor': '20-12345678-9'
            }
            
            # Test 1: User cancellation
            with patch.object(self.case_manager, '_ask_agreement_details_dialog', return_value=None):
                result = self.case_manager.generar_escrito_mediacion(1)
                
                if result == False:
                    self.test_results.append("✅ Cancelación de usuario manejada correctamente")
                else:
                    self.test_results.append(f"❌ Cancelación retorna {result} (esperado: False)")
                    test_passed = False
            
            # Test 2: Successful dialog completion (mock the document generation)
            with patch.object(self.case_manager, '_ask_agreement_details_dialog', return_value=mock_agreement_details), \
                 patch.object(self.case_manager, '_generar_documento_con_datos') as mock_generate, \
                 patch('tkinter.filedialog.asksaveasfilename', return_value='test_document.docx'):
                
                # Mock successful document generation
                mock_generate.return_value = {
                    'success': True,
                    'document': MagicMock(),
                    'file_path': 'test_document.docx'
                }
                
                result = self.case_manager.generar_escrito_mediacion(1)
                
                if result == True:
                    self.test_results.append("✅ Flujo completo exitoso simulado correctamente")
                else:
                    self.test_results.append(f"❌ Flujo completo retorna {result} (esperado: True)")
                    test_passed = False
                
                # Verify that the pure logic method was called
                if mock_generate.called:
                    self.test_results.append("✅ Método de lógica pura fue llamado")
                    
                    # Check call arguments
                    call_args = mock_generate.call_args
                    if call_args and len(call_args[0]) >= 2:
                        caso_id_arg = call_args[0][0]
                        details_arg = call_args[0][1]
                        
                        if caso_id_arg == 1:
                            self.test_results.append("✅ caso_id pasado correctamente al método de lógica pura")
                        else:
                            self.test_results.append(f"❌ caso_id incorrecto: {caso_id_arg}")
                            test_passed = False
                        
                        if details_arg == mock_agreement_details:
                            self.test_results.append("✅ Detalles del acuerdo pasados correctamente")
                        else:
                            self.test_results.append("❌ Detalles del acuerdo no coinciden")
                            test_passed = False
                    else:
                        self.test_results.append("❌ Argumentos de llamada incorrectos")
                        test_passed = False
                else:
                    self.test_results.append("❌ Método de lógica pura NO fue llamado")
                    test_passed = False
        
        except Exception as e:
            self.test_results.append(f"❌ Error en prueba de flujo de diálogos: {e}")
            test_passed = False
        
        return test_passed
    
    def test_constructor_compatibility(self):
        """Test constructor backward compatibility."""
        print("\\n" + "="*60)
        print("PRUEBA: Compatibilidad del constructor")
        print("="*60)
        
        test_passed = True
        
        try:
            # Test 1: Constructor with app_controller
            case_manager_with_app = CaseManager(app_controller=self.mock_app)
            if case_manager_with_app.app_controller == self.mock_app:
                self.test_results.append("✅ Constructor con app_controller funciona")
            else:
                self.test_results.append("❌ Constructor con app_controller falla")
                test_passed = False
            
            # Test 2: Constructor without app_controller (None)
            case_manager_without_app = CaseManager(app_controller=None)
            if case_manager_without_app.app_controller is None:
                self.test_results.append("✅ Constructor sin app_controller funciona")
            else:
                self.test_results.append("❌ Constructor sin app_controller falla")
                test_passed = False
            
            # Test 3: Constructor with default parameter
            case_manager_default = CaseManager()
            if case_manager_default.app_controller is None:
                self.test_results.append("✅ Constructor con parámetro por defecto funciona")
            else:
                self.test_results.append("❌ Constructor con parámetro por defecto falla")
                test_passed = False
        
        except Exception as e:
            self.test_results.append(f"❌ Error en prueba de constructor: {e}")
            test_passed = False
        
        return test_passed
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("INICIANDO PRUEBAS DE INTEGRACIÓN DE UI")
        print("="*80)
        
        all_tests_passed = True
        
        # Run individual tests
        tests = [
            ("Constructor Compatibility", self.test_constructor_compatibility),
            ("UI Method Calls", self.test_ui_method_calls),
            ("Error Handling Integration", self.test_error_handling_integration),
            ("Dialog Flow Simulation", self.test_dialog_flow_simulation)
        ]
        
        for test_name, test_func in tests:
            print(f"\\nEjecutando: {test_name}")
            try:
                test_result = test_func()
                if not test_result:
                    all_tests_passed = False
            except Exception as e:
                print(f"Error ejecutando {test_name}: {e}")
                self.test_results.append(f"❌ Error crítico en {test_name}: {e}")
                all_tests_passed = False
        
        # Print results
        print("\\n" + "="*80)
        print("RESULTADOS DE PRUEBAS DE INTEGRACIÓN")
        print("="*80)
        
        for result in self.test_results:
            print(result)
        
        print("\\n" + "="*80)
        if all_tests_passed:
            print("✅ TODAS LAS PRUEBAS DE INTEGRACIÓN PASARON")
            print("La compatibilidad hacia atrás de la UI está verificada.")
        else:
            print("❌ ALGUNAS PRUEBAS DE INTEGRACIÓN FALLARON")
            print("Se requiere revisión de la implementación.")
        print("="*80)
        
        return all_tests_passed
    
    def cleanup(self):
        """Clean up test resources."""
        try:
            if hasattr(self, 'root'):
                self.root.destroy()
            if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
        except Exception as e:
            print(f"Error during cleanup: {e}")


def run_ui_integration_tests():
    """Run UI integration tests."""
    tester = None
    try:
        tester = UIIntegrationTest()
        success = tester.run_all_tests()
        return success
    except Exception as e:
        print(f"Error running integration tests: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if tester:
            tester.cleanup()


if __name__ == "__main__":
    try:
        success = run_ui_integration_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)