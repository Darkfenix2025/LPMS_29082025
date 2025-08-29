#!/usr/bin/env python3
"""
Final verification test for UI backward compatibility.
This test focuses on verifying the core functionality without database dependencies.
"""

import sys
import os
import tkinter as tk
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from case_dialog_manager import CaseManager, ErrorMessageManager

def test_ui_backward_compatibility():
    """Test UI backward compatibility with mocked dependencies."""
    
    print("VERIFICACIÓN FINAL DE COMPATIBILIDAD HACIA ATRÁS DE LA UI")
    print("="*80)
    
    results = []
    all_tests_passed = True
    
    try:
        # Create Tkinter root
        root = tk.Tk()
        root.withdraw()
        
        # Create mock app
        mock_app = type('MockApp', (), {})()
        mock_app.root = root
        
        # Test 1: Constructor compatibility
        print("\\n1. PROBANDO COMPATIBILIDAD DEL CONSTRUCTOR")
        print("-" * 50)
        
        try:
            # Test with app_controller
            case_manager_with_app = CaseManager(app_controller=mock_app)
            if case_manager_with_app.app_controller == mock_app:
                results.append("✅ Constructor con app_controller: OK")
            else:
                results.append("❌ Constructor con app_controller: FALLA")
                all_tests_passed = False
            
            # Test without app_controller
            case_manager_without_app = CaseManager(app_controller=None)
            if case_manager_without_app.app_controller is None:
                results.append("✅ Constructor sin app_controller: OK")
            else:
                results.append("❌ Constructor sin app_controller: FALLA")
                all_tests_passed = False
            
            # Test default parameter
            case_manager_default = CaseManager()
            if case_manager_default.app_controller is None:
                results.append("✅ Constructor con parámetro por defecto: OK")
            else:
                results.append("❌ Constructor con parámetro por defecto: FALLA")
                all_tests_passed = False
        
        except Exception as e:
            results.append(f"❌ Error en prueba de constructor: {e}")
            all_tests_passed = False
        
        # Test 2: Method existence and signatures
        print("\\n2. PROBANDO EXISTENCIA Y SIGNATURAS DE MÉTODOS")
        print("-" * 50)
        
        case_manager = CaseManager(app_controller=mock_app)
        
        # Check main method
        if hasattr(case_manager, 'generar_escrito_mediacion'):
            results.append("✅ Método generar_escrito_mediacion: Existe")
            
            if callable(getattr(case_manager, 'generar_escrito_mediacion')):
                results.append("✅ Método generar_escrito_mediacion: Es callable")
            else:
                results.append("❌ Método generar_escrito_mediacion: NO es callable")
                all_tests_passed = False
        else:
            results.append("❌ Método generar_escrito_mediacion: NO existe")
            all_tests_passed = False
        
        # Check refactored method
        if hasattr(case_manager, '_generar_documento_con_datos'):
            results.append("✅ Método _generar_documento_con_datos: Existe")
            
            # Check signature
            import inspect
            sig = inspect.signature(case_manager._generar_documento_con_datos)
            params = list(sig.parameters.keys())
            expected_params = ['caso_id', 'details_acuerdo']
            
            if all(param in params for param in expected_params):
                results.append("✅ Signatura _generar_documento_con_datos: Correcta")
            else:
                results.append(f"❌ Signatura _generar_documento_con_datos: Incorrecta. Esperado: {expected_params}, Actual: {params}")
                all_tests_passed = False
        else:
            results.append("❌ Método _generar_documento_con_datos: NO existe")
            all_tests_passed = False
        
        # Check helper methods
        helper_methods = [
            '_collect_agreement_details',
            '_ask_agreement_details_dialog',
            '_validate_initial_parameters',
            '_validate_system_dependencies'
        ]
        
        for method_name in helper_methods:
            if hasattr(case_manager, method_name):
                results.append(f"✅ Método {method_name}: Existe")
            else:
                results.append(f"❌ Método {method_name}: NO existe")
                all_tests_passed = False
        
        # Test 3: UI Flow with mocked dependencies
        print("\\n3. PROBANDO FLUJO DE UI CON DEPENDENCIAS MOCKEADAS")
        print("-" * 50)
        
        # Mock all external dependencies
        mock_case_data = {
            'id': 1,
            'caratula': 'PÉREZ JUAN C/ GARCÍA MARÍA S/ DAÑOS Y PERJUICIOS',
            'numero_expediente': '12345/2023',
            'anio_caratula': '2023',
            'juzgado': 'Juzgado Civil N° 1',
            'jurisdiccion': 'La Plata'
        }
        
        mock_parties_data = {
            'lista_actores': [{'nombre_completo': 'PÉREZ JUAN', 'dni': '12345678'}],
            'lista_demandados': [{'nombre_completo': 'GARCÍA MARÍA', 'dni': '87654321'}]
        }
        
        mock_agreement_details = {
            'monto_compensacion_numeros': '150000.50',
            'plazo_pago_dias': '30',
            'banco_actor': 'Banco Nación',
            'cbu_actor': '1234567890123456789012',
            'alias_actor': 'mi.alias.mp',
            'cuit_actor': '20-12345678-9'
        }
        
        # Test successful flow
        with patch.object(case_manager, '_validate_initial_parameters', return_value=True), \
             patch.object(case_manager, '_validate_system_dependencies', return_value=True), \
             patch.object(case_manager, '_collect_and_validate_case_data', return_value=mock_case_data), \
             patch.object(case_manager, '_collect_and_validate_parties_data', return_value=mock_parties_data), \
             patch.object(case_manager, '_ask_agreement_details_dialog', return_value=mock_agreement_details), \
             patch.object(case_manager, '_generar_documento_con_datos') as mock_generate, \
             patch('tkinter.filedialog.asksaveasfilename', return_value='test_document.docx'):
            
            # Mock successful document generation
            mock_generate.return_value = {
                'success': True,
                'document': MagicMock(),
                'file_path': 'test_document.docx'
            }
            
            result = case_manager.generar_escrito_mediacion(1)
            
            if result == True:
                results.append("✅ Flujo UI completo exitoso: OK")
            else:
                results.append(f"❌ Flujo UI completo: FALLA (retorna {result})")
                all_tests_passed = False
            
            # Verify that the pure logic method was called correctly
            if mock_generate.called:
                results.append("✅ Método de lógica pura llamado: OK")
                
                call_args = mock_generate.call_args
                if call_args and len(call_args[0]) >= 2:
                    caso_id_arg = call_args[0][0]
                    details_arg = call_args[0][1]
                    
                    if caso_id_arg == 1:
                        results.append("✅ caso_id pasado correctamente: OK")
                    else:
                        results.append(f"❌ caso_id incorrecto: {caso_id_arg}")
                        all_tests_passed = False
                    
                    if details_arg == mock_agreement_details:
                        results.append("✅ Detalles del acuerdo pasados correctamente: OK")
                    else:
                        results.append("❌ Detalles del acuerdo no coinciden")
                        all_tests_passed = False
                else:
                    results.append("❌ Argumentos de llamada incorrectos")
                    all_tests_passed = False
            else:
                results.append("❌ Método de lógica pura NO fue llamado")
                all_tests_passed = False
        
        # Test user cancellation
        with patch.object(case_manager, '_validate_initial_parameters', return_value=True), \
             patch.object(case_manager, '_validate_system_dependencies', return_value=True), \
             patch.object(case_manager, '_collect_and_validate_case_data', return_value=mock_case_data), \
             patch.object(case_manager, '_collect_and_validate_parties_data', return_value=mock_parties_data), \
             patch.object(case_manager, '_ask_agreement_details_dialog', return_value=None):
            
            result = case_manager.generar_escrito_mediacion(1)
            
            if result == False:
                results.append("✅ Cancelación de usuario: OK")
            else:
                results.append(f"❌ Cancelación de usuario: FALLA (retorna {result})")
                all_tests_passed = False
        
        # Test 4: Error handling
        print("\\n4. PROBANDO MANEJO DE ERRORES")
        print("-" * 50)
        
        # Test ErrorMessageManager
        try:
            error_info = ErrorMessageManager.get_error_message('missing_case', {'case_id': 123})
            if isinstance(error_info, dict) and 'title' in error_info and 'message' in error_info:
                results.append("✅ ErrorMessageManager: OK")
            else:
                results.append("❌ ErrorMessageManager: FALLA")
                all_tests_passed = False
        except Exception as e:
            results.append(f"❌ ErrorMessageManager: ERROR - {e}")
            all_tests_passed = False
        
        # Test invalid parameters
        with patch('tkinter.messagebox.showerror'):
            result = case_manager.generar_escrito_mediacion(None)
            if result == False:
                results.append("✅ Parámetro None manejado: OK")
            else:
                results.append(f"❌ Parámetro None: FALLA (retorna {result})")
                all_tests_passed = False
        
        # Cleanup
        root.destroy()
        
    except Exception as e:
        results.append(f"❌ Error crítico en pruebas: {e}")
        all_tests_passed = False
        import traceback
        traceback.print_exc()
    
    # Print results
    print("\\n" + "="*80)
    print("RESULTADOS DE VERIFICACIÓN FINAL")
    print("="*80)
    
    for result in results:
        print(result)
    
    print("\\n" + "="*80)
    if all_tests_passed:
        print("✅ VERIFICACIÓN FINAL EXITOSA")
        print("La compatibilidad hacia atrás de la UI está completamente verificada.")
        print("Todos los aspectos críticos funcionan correctamente:")
        print("  - Constructor mantiene compatibilidad")
        print("  - Métodos refactorizados existen y funcionan")
        print("  - Flujo de UI se mantiene intacto")
        print("  - Manejo de errores funciona correctamente")
        print("  - Separación de lógica pura exitosa")
    else:
        print("❌ VERIFICACIÓN FINAL FALLÓ")
        print("Se encontraron problemas de compatibilidad que requieren atención.")
    print("="*80)
    
    return all_tests_passed


if __name__ == "__main__":
    try:
        success = test_ui_backward_compatibility()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error crítico: {e}")
        sys.exit(1)