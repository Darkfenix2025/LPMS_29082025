#!/usr/bin/env python3
"""
Test script for case list loading functionality.
Tests the improved load_cases_by_client method and get_cases_by_client function.
"""

import sys
import os
import traceback
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import required modules
try:
    import crm_database as db
    print("[OK] crm_database module imported successfully")
except ImportError as e:
    print(f"[ERROR] Error importing crm_database: {e}")
    sys.exit(1)

# Mock CaseDialogManager for testing
class MockAppController:
    def __init__(self):
        self.selected_case = None
        self.case_tree_items = []

    def clear_case_list(self):
        self.case_tree_items = []
        print("[OK] Case list cleared")

    def disable_case_buttons(self):
        print("[OK] Case buttons disabled")

    def update_add_audiencia_button_state(self):
        print("[OK] Add audiencia button state updated")

class MockCaseTree:
    def __init__(self):
        self.items = []

    def insert(self, parent, index, values=None, iid=None):
        item = {
            'parent': parent,
            'index': index,
            'values': values,
            'iid': iid
        }
        self.items.append(item)
        print(f"[OK] Case inserted in TreeView: ID={values[0]}, Expediente={values[1]}, Carátula={values[2]}")

class MockCaseDialogManager:
    def __init__(self):
        self.app_controller = MockAppController()
        self.app_controller.case_tree = MockCaseTree()
        self.db = db

    def clear_case_list(self):
        self.app_controller.clear_case_list()

    def disable_case_buttons(self):
        self.app_controller.disable_case_buttons()

    def load_cases_by_client(self, client_id):
        """Carga la lista de casos de un cliente en el TreeView"""
        try:
            # Validar parámetro de entrada
            if client_id is None or client_id == "":
                print(f"Error: client_id inválido: {client_id}")
                return False

            # Convertir a entero si es necesario
            try:
                client_id = int(client_id)
            except (ValueError, TypeError):
                print(f"Error: client_id debe ser un número entero válido: {client_id}")
                return False

            print(f"Cargando casos para cliente ID: {client_id}")

            # Limpiar estado anterior
            self.clear_case_list()
            self.app_controller.selected_case = None

            # Obtener casos de la base de datos
            try:
                cases = self.db.get_cases_by_client(client_id)
                if cases is None:
                    print(f"Error: No se pudieron obtener casos para cliente {client_id}")
                    return False
            except Exception as db_error:
                print(f"Error de base de datos al obtener casos para cliente {client_id}: {db_error}")
                return False

            print(f"Encontrados {len(cases)} casos para cliente {client_id}")

            # Procesar cada caso
            cases_loaded = 0
            for case in cases:
                try:
                    # Validar que el caso tenga los campos requeridos
                    if not isinstance(case, dict) or "id" not in case or "caratula" not in case:
                        print(f"Advertencia: Caso inválido encontrado: {case}")
                        continue

                    case_id = case["id"]
                    caratula = case.get("caratula", "Sin carátula")

                    # Obtener etiquetas del caso
                    try:
                        etiquetas_obj = self.db.get_etiquetas_de_caso(case_id)
                        if etiquetas_obj:
                            etiquetas_nombres = [e.get("nombre_etiqueta", "") for e in etiquetas_obj if e]
                            etiquetas_str = ", ".join(etiquetas_nombres) if etiquetas_nombres else ""
                        else:
                            etiquetas_str = ""
                    except Exception as tag_error:
                        print(f"Error al obtener etiquetas para caso {case_id}: {tag_error}")
                        etiquetas_str = ""

                    # Formatear número de expediente y año
                    num_exp = case.get("numero_expediente", "")
                    anio_car = case.get("anio_caratula", "")
                    nro_anio = ""
                    if num_exp and anio_car:
                        nro_anio = f"{num_exp}/{anio_car}"
                    elif num_exp:
                        nro_anio = num_exp
                    elif anio_car:
                        nro_anio = f"/{anio_car}"

                    # Insertar en el TreeView con las 3 columnas
                    try:
                        self.app_controller.case_tree.insert(
                            "", "end", values=(case_id, nro_anio, caratula), iid=str(case_id)
                        )
                        cases_loaded += 1
                    except Exception as tree_error:
                        print(f"Error al insertar caso {case_id} en TreeView: {tree_error}")
                        continue

                except Exception as case_error:
                    print(f"Error procesando caso {case.get('id', 'desconocido')}: {case_error}")
                    continue

            print(f"Casos cargados exitosamente: {cases_loaded} de {len(cases)}")

            # Limpiar selección y detalles
            self.app_controller.selected_case = None
            self.disable_case_buttons()
            self.app_controller.update_add_audiencia_button_state()

            return cases_loaded > 0

        except Exception as e:
            print(f"Error general al cargar casos para cliente {client_id}: {e}")
            traceback.print_exc()
            return False

def test_parameter_validation():
    """Test parameter validation in both functions"""
    print("\n" + "="*60)
    print("TESTING PARAMETER VALIDATION")
    print("="*60)

    success = True

    # Test invalid parameters
    invalid_params = [None, "", "abc", -1, 0]

    for param in invalid_params:
        print(f"\nTesting invalid parameter: {param}")

        # Test get_cases_by_client
        result = db.get_cases_by_client(param)
        if result is None:
            print("[OK] get_cases_by_client correctly returned None for invalid parameter")
        else:
            print(f"[ERROR] get_cases_by_client should return None for invalid parameter, got: {result}")
            success = False

        # Test load_cases_by_client
        manager = MockCaseDialogManager()
        result = manager.load_cases_by_client(param)
        if result is False:
            print("[OK] load_cases_by_client correctly returned False for invalid parameter")
        else:
            print(f"[ERROR] load_cases_by_client should return False for invalid parameter, got: {result}")
            success = False

    return success

def test_database_connection():
    """Test database connection and basic functionality"""
    print("\n" + "="*60)
    print("TESTING DATABASE CONNECTION")
    print("="*60)

    try:
        # Test basic connection
        conn = db.connect_db()
        if conn:
            print("[OK] Database connection successful")
            conn.close()
        else:
            print("[ERROR] Database connection failed")
            return False

        # Test get_clients function
        clients = db.get_clients()
        if clients is not None:
            print(f"[OK] get_clients returned {len(clients)} clients")
        else:
            print("[ERROR] get_clients returned None")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Database connection test failed: {e}")
        traceback.print_exc()
        return False

def test_case_loading():
    """Test the complete case loading functionality"""
    print("\n" + "="*60)
    print("TESTING CASE LOADING FUNCTIONALITY")
    print("="*60)

    try:
        # Get first client for testing
        clients = db.get_clients()
        if not clients:
            print("[ERROR] No clients found in database for testing")
            return False

        test_client = clients[0]
        client_id = test_client['id']
        client_name = test_client['nombre']

        print(f"Testing with client: {client_name} (ID: {client_id})")

        # Test get_cases_by_client
        cases = db.get_cases_by_client(client_id)
        if cases is None:
            print("[ERROR] get_cases_by_client returned None")
            return False
        elif cases == []:
            print(f"[OK] get_cases_by_client returned empty list (client has no cases)")
        else:
            print(f"[OK] get_cases_by_client returned {len(cases)} cases")

        # Test load_cases_by_client
        manager = MockCaseDialogManager()
        result = manager.load_cases_by_client(client_id)

        if result:
            print(f"[OK] load_cases_by_client completed successfully")
            print(f"  - Cases in TreeView: {len(manager.app_controller.case_tree.items)}")
        else:
            print(f"[ERROR] load_cases_by_client failed")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Case loading test failed: {e}")
        traceback.print_exc()
        return False

def test_error_scenarios():
    """Test error handling scenarios"""
    print("\n" + "="*60)
    print("TESTING ERROR SCENARIOS")
    print("="*60)

    success = True

    # Test with non-existent client ID
    print("\nTesting with non-existent client ID (999999):")
    cases = db.get_cases_by_client(999999)
    if cases == []:
        print("[OK] get_cases_by_client correctly returned empty list for non-existent client")
    else:
        print(f"[ERROR] get_cases_by_client should return empty list for non-existent client, got: {cases}")
        success = False

    manager = MockCaseDialogManager()
    result = manager.load_cases_by_client(999999)
    if result is False:
        print("[OK] load_cases_by_client correctly returned False for non-existent client (no cases to load)")
    else:
        print(f"[ERROR] load_cases_by_client should return False for non-existent client, got: {result}")
        success = False

    return success

def main():
    """Main test function"""
    print("TESTING CASE LIST LOADING FUNCTIONALITY")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Run all tests
    tests = [
        ("Parameter Validation", test_parameter_validation),
        ("Database Connection", test_database_connection),
        ("Case Loading", test_case_loading),
        ("Error Scenarios", test_error_scenarios)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name.upper()} {'='*20}")
            result = test_func()
            results.append((test_name, result))
            print(f"{'[OK] PASSED' if result else '[ERROR] FAILED'}: {test_name}")
        except Exception as e:
            print(f"[ERROR] ERROR in {test_name}: {e}")
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] All tests passed! Case list loading functionality is working correctly.")
        return True
    else:
        print("[FAILED] Some tests failed. Please check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)