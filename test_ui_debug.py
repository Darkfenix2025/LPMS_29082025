#!/usr/bin/env python3
"""
Debug test to understand why the UI flow is not completing successfully.
"""

import sys
import os
import tkinter as tk
import sqlite3
import tempfile
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
import crm_database as db
from case_dialog_manager import CaseManager

def debug_ui_flow():
    """Debug the UI flow to understand where it's failing."""
    print("DEBUGGING UI FLOW")
    print("="*50)
    
    # Setup test database
    test_db_path = tempfile.mktemp(suffix='.db')
    
    try:
        conn = sqlite3.connect(test_db_path)
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
        db.DATABASE_PATH = test_db_path
        
        # Create Tkinter root
        root = tk.Tk()
        root.withdraw()
        
        # Create mock app
        mock_app = type('MockApp', (), {})()
        mock_app.root = root
        
        # Create case manager
        case_manager = CaseManager(app_controller=mock_app)
        
        # Mock agreement details
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
        
        print("\\n1. Testing individual method calls...")
        
        # Test _validate_initial_parameters
        try:
            result = case_manager._validate_initial_parameters(1)
            print(f"   _validate_initial_parameters(1): {result}")
        except Exception as e:
            print(f"   _validate_initial_parameters(1): ERROR - {e}")
        
        # Test _validate_system_dependencies
        try:
            with patch('tkinter.messagebox.showerror'):
                result = case_manager._validate_system_dependencies()
                print(f"   _validate_system_dependencies(): {result}")
        except Exception as e:
            print(f"   _validate_system_dependencies(): ERROR - {e}")
        
        # Test _collect_and_validate_case_data
        try:
            with patch('tkinter.messagebox.showerror'):
                result = case_manager._collect_and_validate_case_data(1)
                print(f"   _collect_and_validate_case_data(1): {result is not None}")
                if result:
                    print(f"      Case data keys: {list(result.keys())}")
        except Exception as e:
            print(f"   _collect_and_validate_case_data(1): ERROR - {e}")
        
        # Test _collect_and_validate_parties_data
        try:
            with patch('tkinter.messagebox.showerror'):
                result = case_manager._collect_and_validate_parties_data(1)
                print(f"   _collect_and_validate_parties_data(1): {result is not None}")
                if result:
                    print(f"      Parties data keys: {list(result.keys())}")
        except Exception as e:
            print(f"   _collect_and_validate_parties_data(1): ERROR - {e}")
        
        print("\\n2. Testing with mocked dialog...")
        
        # Test with mocked dialog
        with patch.object(case_manager, '_ask_agreement_details_dialog', return_value=mock_agreement_details) as mock_dialog, \
             patch.object(case_manager, '_generar_documento_con_datos') as mock_generate, \
             patch('tkinter.filedialog.asksaveasfilename', return_value='test_document.docx') as mock_save, \
             patch('tkinter.messagebox.showerror') as mock_error:
            
            # Mock successful document generation
            mock_generate.return_value = {
                'success': True,
                'document': MagicMock(),
                'file_path': 'test_document.docx'
            }
            
            print("   Calling generar_escrito_mediacion(1)...")
            result = case_manager.generar_escrito_mediacion(1)
            
            print(f"   Result: {result}")
            print(f"   Dialog called: {mock_dialog.called}")
            print(f"   Generate called: {mock_generate.called}")
            print(f"   Save dialog called: {mock_save.called}")
            print(f"   Error dialog called: {mock_error.called}")
            
            if mock_generate.called:
                print(f"   Generate call args: {mock_generate.call_args}")
            
            if mock_error.called:
                print(f"   Error calls: {mock_error.call_args_list}")
        
        print("\\n3. Testing without mocked document generation...")
        
        # Test without mocking document generation to see what happens
        with patch.object(case_manager, '_ask_agreement_details_dialog', return_value=mock_agreement_details) as mock_dialog, \
             patch('tkinter.filedialog.asksaveasfilename', return_value='test_document.docx') as mock_save, \
             patch('tkinter.messagebox.showerror') as mock_error:
            
            print("   Calling generar_escrito_mediacion(1) without mocked generation...")
            result = case_manager.generar_escrito_mediacion(1)
            
            print(f"   Result: {result}")
            print(f"   Dialog called: {mock_dialog.called}")
            print(f"   Save dialog called: {mock_save.called}")
            print(f"   Error dialog called: {mock_error.called}")
            
            if mock_error.called:
                print(f"   Error calls: {mock_error.call_args_list}")
        
        # Cleanup
        root.destroy()
        
    except Exception as e:
        print(f"Error in debug: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
        except:
            pass

if __name__ == "__main__":
    debug_ui_flow()