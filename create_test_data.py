#!/usr/bin/env python3
"""
Script to create test data in the database for testing the agent tools.
"""

import crm_database as db
import datetime

def create_test_case():
    """Create a test case with parties for testing."""
    
    try:
        print("Creating test case data...")
        
        # Test case data
        case_data = {
            'caratula': 'PÉREZ, JUAN C/ EMPRESA XYZ S.A. S/ DESPIDO',
            'numero_expediente': 'EXP-2024-001',
            'juzgado': 'Juzgado Nacional del Trabajo Nº 1',
            'fecha_inicio': datetime.date.today().strftime('%Y-%m-%d'),
            'estado': 'En mediación'
        }
        
        # Create the case
        case_id = db.create_case(case_data)
        print(f"✓ Test case created with ID: {case_id}")
        
        # Create test parties
        parties = [
            {
                'case_id': case_id,
                'nombre': 'Juan Carlos',
                'apellido': 'Pérez',
                'dni': '12345678',
                'rol': 'Actor',
                'telefono': '11-1234-5678',
                'email': 'juan.perez@email.com'
            },
            {
                'case_id': case_id,
                'nombre': 'Empresa XYZ',
                'apellido': 'S.A.',
                'dni': '30123456789',
                'rol': 'Demandado',
                'telefono': '11-9876-5432',
                'email': 'legal@empresaxyz.com'
            }
        ]
        
        for party in parties:
            party_id = db.create_party(party)
            print(f"✓ Party created: {party['nombre']} {party['apellido']} ({party['rol']}) - ID: {party_id}")
        
        return case_id
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        return None

def verify_test_data(case_id):
    """Verify that the test data was created correctly."""
    
    try:
        print(f"\nVerifying test data for case ID: {case_id}")
        
        # Get case data
        case = db.get_case_by_id(case_id)
        if case:
            print(f"✓ Case found: {case.get('caratula', 'No caratula')}")
        else:
            print("❌ Case not found")
            return False
        
        # Get parties
        parties = db.get_parties_by_case_id(case_id)
        if parties:
            print(f"✓ Found {len(parties)} parties:")
            for party in parties:
                print(f"  - {party.get('nombre', '')} {party.get('apellido', '')} ({party.get('rol', '')})")
        else:
            print("❌ No parties found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying test data: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CREATING TEST DATA FOR AGENT TOOLS")
    print("=" * 60)
    
    case_id = create_test_case()
    
    if case_id:
        if verify_test_data(case_id):
            print(f"\n✅ Test data created successfully!")
            print(f"Use case ID {case_id} for testing the agent tools.")
        else:
            print("\n❌ Test data verification failed.")
    else:
        print("\n❌ Failed to create test data.")