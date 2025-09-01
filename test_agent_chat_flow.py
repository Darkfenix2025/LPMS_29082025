#!/usr/bin/env python3
"""
Test script for the Agent Chat Flow - Asistente de Acuerdos
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")

    try:
        from agent_chat_window import AgentChatWindow, open_agent_chat_window
        print("[OK] AgentChatWindow imported successfully")
    except ImportError as e:
        print(f"[ERROR] Error importing AgentChatWindow: {e}")
        return False

    try:
        from agent_core import AgentCore
        print("[OK] AgentCore imported successfully")
    except ImportError as e:
        print(f"[ERROR] Error importing AgentCore: {e}")
        return False

    try:
        from agent_tools import leer_plantilla_tool, generar_acuerdo_template_tool
        print("[OK] Agent tools imported successfully")
    except ImportError as e:
        print(f"[ERROR] Error importing agent tools: {e}")
        return False

    try:
        import crm_database as db
        print("[OK] CRM Database imported successfully")
    except ImportError as e:
        print(f"[ERROR] Error importing CRM Database: {e}")
        return False

    return True

def test_agent_initialization():
    """Test that the agent can be initialized with all tools"""
    print("\nTesting agent initialization...")

    try:
        from agent_core import AgentCore
        agent = AgentCore()

        print(f"[OK] Agent initialized with {len(agent.tools)} tools:")
        for tool in agent.tools:
            print(f"  - {tool.name}")

        # Verify that our new tool is included
        tool_names = [tool.name for tool in agent.tools]
        if 'leer_plantilla_de_acuerdo' in tool_names:
            print("[OK] Template reading tool is properly loaded")
        else:
            print("[ERROR] Template reading tool not found in agent tools")
            return False

        return True

    except Exception as e:
        print(f"[ERROR] Error initializing agent: {e}")
        return False

def test_template_reading():
    """Test the template reading functionality"""
    print("\nTesting template reading...")

    try:
        from agent_tools import _leer_plantilla

        # Test reading the template file
        result = _leer_plantilla('modelo_acuerdo.txt')

        if result.startswith("Plantilla cargada exitosamente"):
            print("[OK] Template reading successful")
            print(f"  Content preview: {result[:100]}...")
            return True
        else:
            print(f"[ERROR] Template reading failed: {result}")
            return False

    except Exception as e:
        print(f"[ERROR] Error testing template reading: {e}")
        return False

def test_database_connection():
    """Test database connection and basic queries"""
    print("\nTesting database connection...")

    try:
        import crm_database as db

        # Test getting clients
        clients = db.get_clients()
        print(f"[OK] Database connection successful, found {len(clients)} clients")

        # Test getting cases if there are clients
        if clients:
            first_client = clients[0]
            cases = db.get_cases_by_client(first_client['id'])
            print(f"[OK] Found {len(cases)} cases for client {first_client['nombre']}")
        else:
            print("[INFO] No clients found in database (this is normal for a test environment)")

        return True

    except Exception as e:
        print(f"[ERROR] Error testing database: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("TESTING ASISTENTE DE ACUERDOS - COMPLETE FLOW")
    print("=" * 60)

    tests = [
        ("Imports", test_imports),
        ("Agent Initialization", test_agent_initialization),
        ("Template Reading", test_template_reading),
        ("Database Connection", test_database_connection),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)

    all_passed = True
    for test_name, result in results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] ALL TESTS PASSED! The Asistente de Acuerdos is ready to use.")
        print("\nTo use the system:")
        print("1. Open the main application (main_app.py)")
        print("2. Go to the Seguimiento tab")
        print("3. Select a case")
        print("4. Click the 'Agente IA - Acuerdos' button")
        print("5. The Asistente de Acuerdos window will open with case context pre-loaded")
    else:
        print("[ERROR] Some tests failed. Please check the errors above.")
    print("=" * 60)

    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)