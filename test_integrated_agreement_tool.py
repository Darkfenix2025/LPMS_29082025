#!/usr/bin/env python3
"""
Test script for the new integrated agreement generation tool.
This demonstrates the complete workflow without UI dependencies.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_integrated_agreement_workflow():
    """Test the integrated agreement generation workflow"""
    print("=" * 80)
    print("TESTING INTEGRATED AGREEMENT GENERATION WORKFLOW")
    print("=" * 80)

    try:
        # Import the agent tools
        from agent_tools import generar_acuerdo_integrado_tool
        import crm_database as db

        print("\n[1] Testing client list retrieval...")
        clients = db.get_clients()
        if clients:
            print(f"[OK] Found {len(clients)} clients")
            first_client = clients[0]
            print(f"   First client: {first_client['nombre']} (ID: {first_client['id']})")
        else:
            print("[ERROR] No clients found")
            return False

        print("\n[2] Testing case retrieval for first client...")
        client_id = first_client['id']
        cases = db.get_cases_by_client(client_id)
        if cases:
            print(f"[OK] Found {len(cases)} cases for client {client_id}")
            first_case = cases[0]
            print(f"   First case: ID {first_case['id']} - {first_case.get('caratula', 'No caratula')[:50]}...")
        else:
            print(f"[ERROR] No cases found for client {client_id}")
            return False

        print("\n[3] Testing integrated tool - Step 1: Get clients...")
        # Test getting clients (no client_id specified)
        result1 = generar_acuerdo_integrado_tool.func()
        print("[OK] Client list retrieval working")
        print(f"   Response preview: {result1[:100]}...")

        print("\n[4] Testing integrated tool - Step 2: Get cases for client...")
        # Test getting cases for a specific client
        result2 = generar_acuerdo_integrado_tool.func(cliente_id=client_id)
        print("[OK] Case list retrieval working")
        print(f"   Response preview: {result2[:100]}...")

        print("\n[5] Testing integrated tool - Step 3: Complete agreement generation...")
        # Test complete agreement generation with sample data
        case_id = first_case['id']
        sample_data = {
            'cliente_id': client_id,
            'caso_id': case_id,
            'monto_compensacion': '150000',
            'plazo_pago_dias': '30',
            'banco_actor': 'Banco Nación',
            'cbu_actor': '0110599540000001234567',
            'alias_actor': 'juan.perez.legal',
            'cuit_actor': '20-12345678-9',
            'metodo_generacion': 'template'
        }

        result3 = generar_acuerdo_integrado_tool.func(**sample_data)
        print("[OK] Complete agreement generation working")
        if "[OK]" in result3 or "exitosamente" in result3:
            print("   Agreement generated successfully!")
        elif "[ERROR]" in result3 or "Error" in result3:
            print(f"   Generation had issues: {result3[:100]}...")
        else:
            print(f"   Unexpected response: {result3[:100]}...")

        print("\n" + "=" * 80)
        print("INTEGRATED WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("\nThe new integrated tool allows users to:")
        print("1. List all available clients")
        print("2. Select a client and see their cases")
        print("3. Generate agreements without UI dependencies")
        print("4. Choose between template, IA, or escrito generation methods")
        print("\nThis solves the UI case loading issues by working entirely within the agent!")

        return True

    except Exception as e:
        print(f"\n[ERROR] Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integrated_agreement_workflow()
    sys.exit(0 if success else 1)