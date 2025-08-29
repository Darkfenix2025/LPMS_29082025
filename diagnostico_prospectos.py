#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas en el módulo de Prospectos
"""

import sys
import os
import traceback

# Add current directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Prueba todos los imports necesarios para el módulo de Prospectos"""
    print("=== DIAGNÓSTICO DE IMPORTS DEL MÓDULO DE PROSPECTOS ===\n")
    
    imports_to_test = [
        ("tkinter", "import tkinter as tk"),
        ("tkinter.ttk", "from tkinter import ttk, messagebox, filedialog"),
        ("datetime", "import datetime"),
        ("os", "import os"),
        ("date_utils", "import date_utils"),
        ("entidad_base", "from entidad_base import EntidadBase, EntidadFactory"),
        ("conversion_service", "from conversion_service import ConversionService"),
        ("prospect_service", "from prospect_service import ProspectService"),
        ("prospect_manager", "from prospect_manager import ProspectManager"),
        ("crm_database", "import crm_database as db"),
    ]
    
    failed_imports = []
    
    for name, import_statement in imports_to_test:
        try:
            exec(import_statement)
            print(f"✓ {name}: Import successful")
        except Exception as e:
            print(f"✗ {name}: Import failed - {e}")
            failed_imports.append((name, str(e)))
    
    return failed_imports

def test_prospect_service_creation():
    """Prueba la creación del ProspectService"""
    print("\n=== DIAGNÓSTICO DE PROSPECT SERVICE ===\n")
    
    try:
        from prospect_service import ProspectService
        service = ProspectService()
        print("✓ ProspectService created successfully")
        return True
    except Exception as e:
        print(f"✗ ProspectService creation failed: {e}")
        traceback.print_exc()
        return False

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    print("\n=== DIAGNÓSTICO DE BASE DE DATOS ===\n")
    
    try:
        import crm_database as db
        conn = db.connect_db()
        if conn:
            print("✓ Database connection successful")
            conn.close()
            return True
        else:
            print("✗ Database connection failed")
            return False
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        traceback.print_exc()
        return False

def test_prospects_window_creation():
    """Prueba la creación de ProspectsWindow (simulada)"""
    print("\n=== DIAGNÓSTICO DE PROSPECTS WINDOW ===\n")
    
    try:
        # Simular parent_app básico
        class MockParentApp:
            def __init__(self):
                import tkinter as tk
                self.root = tk.Tk()
                self.root.withdraw()  # Ocultar ventana principal
        
        # Intentar importar ProspectsWindow
        from prospects_window import ProspectsWindow
        print("✓ ProspectsWindow import successful")
        
        # Intentar crear instancia (pero no mostrarla)
        mock_parent = MockParentApp()
        try:
            window = ProspectsWindow(mock_parent)
            print("✓ ProspectsWindow creation successful")
            window.window.destroy()  # Cerrar ventana de prueba
            mock_parent.root.destroy()  # Cerrar ventana mock
            return True
        except Exception as e:
            print(f"✗ ProspectsWindow creation failed: {e}")
            traceback.print_exc()
            mock_parent.root.destroy()
            return False
            
    except Exception as e:
        print(f"✗ ProspectsWindow import failed: {e}")
        traceback.print_exc()
        return False

def test_prospect_manager_creation():
    """Prueba la creación del ProspectManager"""
    print("\n=== DIAGNÓSTICO DE PROSPECT MANAGER ===\n")
    
    try:
        from prospect_manager import ProspectManager
        
        # Crear mock app controller
        class MockAppController:
            def __init__(self):
                import tkinter as tk
                self.root = tk.Tk()
                self.root.withdraw()
                # Crear mock prospect_tree
                self.prospect_tree = tk.Frame(self.root)  # Mock simple
        
        mock_controller = MockAppController()
        manager = ProspectManager(mock_controller)
        print("✓ ProspectManager created successfully")
        mock_controller.root.destroy()
        return True
        
    except Exception as e:
        print(f"✗ ProspectManager creation failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Ejecuta todos los diagnósticos"""
    print("INICIANDO DIAGNÓSTICO DEL MÓDULO DE PROSPECTOS")
    print("=" * 60)
    
    # Test 1: Imports
    failed_imports = test_imports()
    
    # Test 2: Database
    db_ok = test_database_connection()
    
    # Test 3: ProspectService
    service_ok = test_prospect_service_creation()
    
    # Test 4: ProspectManager
    manager_ok = test_prospect_manager_creation()
    
    # Test 5: ProspectsWindow
    window_ok = test_prospects_window_creation()
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DEL DIAGNÓSTICO")
    print("=" * 60)
    
    if failed_imports:
        print(f"❌ IMPORTS: {len(failed_imports)} imports fallaron")
        for name, error in failed_imports:
            print(f"   - {name}: {error}")
    else:
        print("✅ IMPORTS: Todos los imports exitosos")
    
    print(f"{'✅' if db_ok else '❌'} DATABASE: {'Conexión exitosa' if db_ok else 'Error de conexión'}")
    print(f"{'✅' if service_ok else '❌'} PROSPECT SERVICE: {'Creación exitosa' if service_ok else 'Error de creación'}")
    print(f"{'✅' if manager_ok else '❌'} PROSPECT MANAGER: {'Creación exitosa' if manager_ok else 'Error de creación'}")
    print(f"{'✅' if window_ok else '❌'} PROSPECTS WINDOW: {'Creación exitosa' if window_ok else 'Error de creación'}")
    
    all_ok = not failed_imports and db_ok and service_ok and manager_ok and window_ok
    
    if all_ok:
        print("\n🎉 DIAGNÓSTICO EXITOSO: El módulo de Prospectos debería funcionar correctamente")
    else:
        print("\n⚠️ PROBLEMAS DETECTADOS: Revisar los errores arriba para solucionar el problema")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)