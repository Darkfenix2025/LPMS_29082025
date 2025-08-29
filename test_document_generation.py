#!/usr/bin/env python3
"""
Test script for document generation functionality.
Tests the pure document generation method with sample data.
"""

import sys
import os
import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from case_dialog_manager import CaseManager
import crm_database as db

def create_test_data():
    """Create test data if it doesn't exist"""
    print("\n2. Creating test data...")

    try:
        # Check if we have any cases
        cases = db.get_cases_by_client(1)
        if not cases:
            print("No cases found, creating test case...")

            # Create a test client first
            client_id = db.add_client(
                nombre="Cliente de Prueba",
                direccion="Dirección de Prueba",
                email="cliente.prueba@email.com",
                whatsapp="123456789"
            )

            if client_id:
                print(f"Created test client with ID: {client_id}")

                # Create a test case
                case_id = db.add_case(
                    cliente_id=client_id,
                    caratula="Prueba Generación Documentos",
                    numero_expediente="1234",
                    anio_caratula="2024",
                    juzgado="Juzgado de Prueba",
                    jurisdiccion="Ciudad Autónoma de Buenos Aires",
                    etapa_procesal="Mediación",
                    notas="Caso de prueba para generación de documentos",
                    ruta_carpeta="",
                    inactivity_threshold_days=30,
                    inactivity_enabled=1
                )

                if case_id:
                    print(f"Created test case with ID: {case_id}")
                    return case_id
                else:
                    print("Failed to create test case")
                    return None
            else:
                print("Failed to create test client")
                return None
        else:
            case_id = cases[0]['id']
            print(f"Using existing case ID: {case_id}")
            return case_id

    except Exception as e:
        print(f"Error creating test data: {e}")
        import traceback
        traceback.print_exc()
        return None

def ensure_test_parties(case_id):
    """Ensure the test case has the required parties (actors and defendants)"""
    print(f"\n3. Ensuring test parties for case ID: {case_id}")

    try:
        # Check existing parties
        parties = db.get_parties_by_case_id(case_id)
        if not parties:
            print("No parties found, creating test parties...")

            # Create test parties (actors and defendants)
            # Actor
            actor_contacto_id = db.add_contacto({
                'nombre_completo': "Juan Pérez",
                'es_persona_juridica': False,
                'dni': "12345678",
                'cuit': "20123456789",
                'domicilio_real': "Calle Falsa 123",
                'domicilio_legal': "Calle Falsa 123",
                'email': "juan.perez@email.com",
                'telefono': "123456789",
                'notas_generales': "Actor de prueba"
            })

            if actor_contacto_id:
                actor_rol_id = db.add_rol_a_caso({
                    'caso_id': case_id,
                    'contacto_id': actor_contacto_id,
                    'rol_principal': 'Actor',
                    'datos_bancarios': 'CBU: 1234567890123456789012, Alias: JUAN.PEREZ.CUENTA'
                })

            # Demandado
            defendant_contacto_id = db.add_contacto({
                'nombre_completo': "Empresa XYZ S.A.",
                'es_persona_juridica': True,
                'dni': "",
                'cuit': "30123456789",
                'domicilio_real': "Av. Empresarial 456",
                'domicilio_legal': "Av. Empresarial 456",
                'email': "empresa.xyz@email.com",
                'telefono': "987654321",
                'notas_generales': "Demandado de prueba"
            })

            if defendant_contacto_id:
                defendant_rol_id = db.add_rol_a_caso({
                    'caso_id': case_id,
                    'contacto_id': defendant_contacto_id,
                    'rol_principal': 'Demandado'
                })

            print(f"Created test parties - Actor Contacto ID: {actor_contacto_id}, Defendant Contacto ID: {defendant_contacto_id}")
        else:
            print(f"Found {len(parties)} existing parties")

            # Check if we have actors and defendants
            has_actor = any(p.get('rol', '').lower() == 'actor' for p in parties)
            has_defendant = any(p.get('rol', '').lower() == 'demandado' for p in parties)

            if not has_actor:
                print("No actors found, creating test actor...")
                actor_contacto_id = db.add_contacto({
                    'nombre_completo': "Juan Pérez",
                    'es_persona_juridica': False,
                    'dni': "12345678",
                    'cuit': "20123456789",
                    'domicilio_real': "Calle Falsa 123",
                    'domicilio_legal': "Calle Falsa 123",
                    'email': "juan.perez@email.com",
                    'telefono': "123456789",
                    'notas_generales': "Actor de prueba"
                })
                if actor_contacto_id:
                    actor_rol_id = db.add_rol_a_caso({
                        'caso_id': case_id,
                        'contacto_id': actor_contacto_id,
                        'rol_principal': 'Actor',
                        'datos_bancarios': 'CBU: 1234567890123456789012, Alias: JUAN.PEREZ.CUENTA'
                    })
                print(f"Created test actor Contacto ID: {actor_contacto_id}")

            if not has_defendant:
                print("No defendants found, creating test defendant...")
                defendant_contacto_id = db.add_contacto({
                    'nombre_completo': "Empresa XYZ S.A.",
                    'es_persona_juridica': True,
                    'dni': "",
                    'cuit': "30123456789",
                    'domicilio_real': "Av. Empresarial 456",
                    'domicilio_legal': "Av. Empresarial 456",
                    'email': "empresa.xyz@email.com",
                    'telefono': "987654321",
                    'notas_generales': "Demandado de prueba"
                })
                if defendant_contacto_id:
                    defendant_rol_id = db.add_rol_a_caso({
                        'caso_id': case_id,
                        'contacto_id': defendant_contacto_id,
                        'rol_principal': 'Demandado'
                    })
                print(f"Created test defendant Contacto ID: {defendant_contacto_id}")

        return True

    except Exception as e:
        print(f"Error ensuring test parties: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_document_generation():
    """Test document generation with sample data"""

    print("=== Testing Document Generation ===")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")

    try:
        # Create CaseManager instance
        print("\n1. Creating CaseManager instance...")
        case_manager = CaseManager()
        print("CaseManager created successfully")

        # Create test data if needed
        case_id = create_test_data()
        if not case_id:
            print("Failed to create or find test case")
            return None

        # Ensure the case has required parties
        if not ensure_test_parties(case_id):
            print("Failed to ensure test parties")
            return None

        # Sample case data
        print("\n4. Preparing sample data...")

        # Sample agreement details with the corrected variable name
        agreement_details = {
            'monto_compensacion_numeros': '150000',  # Fixed variable name
            'plazo_pago_dias': '30',
            'banco_actor': 'Banco Nación',
            'cbu_actor': '1234567890123456789012',
            'alias_actor': 'MI.CUENTA.BANCARIA',
            'cuit_actor': '20123456789'
        }

        print(f"Sample agreement details: {agreement_details}")

        print(f"\n5. Testing document generation for case ID: {case_id}")

        # Call the pure document generation method
        result = case_manager._generar_documento_con_datos(case_id, agreement_details)

        print("\n=== Document Generation Result ===")
        print(f"Success: {result['success']}")
        print(f"Error message: {result.get('error_message', 'None')}")
        print(f"Error type: {result.get('error_type', 'None')}")

        if result['success']:
            print("[SUCCESS] Document generation completed successfully!")
            print(f"Filename suggestion: {result.get('filename_suggestion', 'None')}")

            # Show some context data
            context = result.get('document_context', {})
            if context:
                print("\n[CONTEXT] Context data sample:")
                print(f"  NUMERO_EXPEDIENTE: '{context.get('NUMERO_EXPEDIENTE', 'NOT_SET')}'")
                print(f"  CARATULA: '{context.get('CARATULA', 'NOT_SET')}'")
                print(f"  MONTO_COMPENSACION_NUMEROS: '{context.get('MONTO_COMPENSACION_NUMEROS', 'NOT_SET')}'")
                print(f"  MONTO_COMPENSACION_LETRAS: '{context.get('MONTO_COMPENSACION_LETRAS', 'NOT_SET')}'")
                print(f"  PLAZO_PAGO_DIAS: '{context.get('PLAZO_PAGO_DIAS', 'NOT_SET')}'")
                print(f"  PLAZO_PAGO_LETRAS: '{context.get('PLAZO_PAGO_LETRAS', 'NOT_SET')}'")
                print(f"  ACTORES count: {len(context.get('ACTORES', [])) if isinstance(context.get('ACTORES'), list) else 'invalid'}")
                print(f"  DEMANDADOS count: {len(context.get('DEMANDADOS', [])) if isinstance(context.get('DEMANDADOS'), list) else 'invalid'}")
        else:
            print("[ERROR] Document generation failed!")
            print(f"Error details: {result.get('error_message', 'Unknown error')}")

        return result

    except Exception as e:
        print(f"\n[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        print("\nTest completed")

if __name__ == "__main__":
    print("Starting document generation test...")
    result = test_document_generation()

    if result and result['success']:
        print("\n[SUCCESS] Test completed successfully!")
        sys.exit(0)
    else:
        print("\n[FAILED] Test failed!")
        sys.exit(1)