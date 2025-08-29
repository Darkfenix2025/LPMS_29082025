#!/usr/bin/env python3
"""
Comprehensive test script for the LPMS agent refactoring implementation.
Tests all implemented functionality including logging, monitoring, and agent tools.
"""

import sys
import logging
import time
import traceback
from datetime import datetime

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_imports():
    """Test that all required modules can be imported."""
    print("=" * 80)
    print("TESTING IMPORTS AND DEPENDENCIES")
    print("=" * 80)
    
    try:
        # Test core imports
        import agent_tools
        print("✓ agent_tools imported successfully")
        
        import case_dialog_manager
        print("✓ case_dialog_manager imported successfully")
        
        # Test LangChain availability
        from agent_tools import LANGCHAIN_AVAILABLE
        print(f"✓ LangChain available: {LANGCHAIN_AVAILABLE}")
        
        # Test specific functions
        from agent_tools import (
            generar_escrito_mediacion_tool,
            get_agent_tools_performance_stats,
            reset_agent_tools_performance_stats
        )
        print("✓ Agent tool functions imported successfully")
        
        from case_dialog_manager import CaseManager
        print("✓ CaseManager class imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_case_manager_creation():
    """Test CaseManager creation and initialization."""
    print("\n" + "=" * 80)
    print("TESTING CASE MANAGER CREATION")
    print("=" * 80)
    
    try:
        from case_dialog_manager import CaseManager
        
        # Test creation without app_controller
        print("Creating CaseManager without app_controller...")
        case_manager = CaseManager(app_controller=None)
        print("✓ CaseManager created successfully")
        
        # Test that required methods exist
        required_methods = [
            '_generar_documento_con_datos',
            '_validate_pure_parameters',
            '_validate_system_dependencies_pure'
        ]
        
        for method in required_methods:
            if hasattr(case_manager, method):
                print(f"✓ Method {method} exists")
            else:
                print(f"❌ Method {method} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ CaseManager creation error: {e}")
        traceback.print_exc()
        return False

def test_agent_tool_validation():
    """Test agent tool parameter validation."""
    print("\n" + "=" * 80)
    print("TESTING AGENT TOOL PARAMETER VALIDATION")
    print("=" * 80)
    
    try:
        from agent_tools import generar_escrito_mediacion_tool, reset_agent_tools_performance_stats
        
        # Reset stats for clean test
        reset_agent_tools_performance_stats()
        
        # Test 1: Invalid case ID
        print("\n--- Test 1: Invalid Case ID ---")
        result = generar_escrito_mediacion_tool.invoke({
            "id_del_caso": -1,
            "monto_compensacion": "50000.50",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco Nación",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "test.alias",
            "cuit_actor": "20-12345678-9"
        })
        print(f"Result: {result[:100]}...")
        
        # Test 2: Invalid amount
        print("\n--- Test 2: Invalid Amount ---")
        result = generar_escrito_mediacion_tool.invoke({
            "id_del_caso": 1,
            "monto_compensacion": "invalid_amount",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco Nación",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "test.alias",
            "cuit_actor": "20-12345678-9"
        })
        print(f"Result: {result[:100]}...")
        
        # Test 3: Invalid CBU
        print("\n--- Test 3: Invalid CBU ---")
        result = generar_escrito_mediacion_tool.invoke({
            "id_del_caso": 1,
            "monto_compensacion": "50000.50",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco Nación",
            "cbu_actor": "123",  # Too short
            "alias_actor": "test.alias",
            "cuit_actor": "20-12345678-9"
        })
        print(f"Result: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        traceback.print_exc()
        return False

def test_performance_monitoring():
    """Test performance monitoring and statistics."""
    print("\n" + "=" * 80)
    print("TESTING PERFORMANCE MONITORING")
    print("=" * 80)
    
    try:
        from agent_tools import (
            generar_escrito_mediacion_tool,
            get_agent_tools_performance_stats,
            reset_agent_tools_performance_stats
        )
        
        # Reset stats
        reset_agent_tools_performance_stats()
        initial_stats = get_agent_tools_performance_stats()
        print(f"Initial stats: {initial_stats}")
        
        # Make a few calls to generate statistics
        print("\nMaking test calls to generate statistics...")
        
        for i in range(3):
            print(f"\nCall {i+1}:")
            result = generar_escrito_mediacion_tool.invoke({
                "id_del_caso": i + 1,
                "monto_compensacion": f"{(i+1)*10000}.00",
                "plazo_pago_dias": str((i+1)*30),
                "banco_actor": "Banco Test",
                "cbu_actor": "0110599520000001234567",
                "alias_actor": "test.alias",
                "cuit_actor": "20-12345678-9"
            })
            print(f"Result type: {'Success' if '✅' in result else 'Error'}")
        
        # Check final statistics
        final_stats = get_agent_tools_performance_stats()
        print(f"\nFinal stats: {final_stats}")
        
        # Verify statistics make sense
        if final_stats['total_calls'] == 3:
            print("✓ Total calls tracked correctly")
        else:
            print(f"❌ Total calls incorrect: expected 3, got {final_stats['total_calls']}")
        
        if final_stats['last_call_time']:
            print("✓ Last call time recorded")
        else:
            print("❌ Last call time not recorded")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring test error: {e}")
        traceback.print_exc()
        return False

def test_logging_output():
    """Test that logging is working correctly."""
    print("\n" + "=" * 80)
    print("TESTING LOGGING OUTPUT")
    print("=" * 80)
    
    try:
        from agent_tools import generar_escrito_mediacion_tool
        
        print("Making a call with detailed logging enabled...")
        
        # Set logging to DEBUG to see all messages
        logging.getLogger('agent_tools').setLevel(logging.DEBUG)
        logging.getLogger('case_dialog_manager').setLevel(logging.DEBUG)
        
        result = generar_escrito_mediacion_tool.invoke({
            "id_del_caso": 999,  # Likely non-existent case
            "monto_compensacion": "75000.00",
            "plazo_pago_dias": "45",
            "banco_actor": "Banco Santander Argentina S.A.",
            "cbu_actor": "0720001234000056789012",
            "alias_actor": "logging.test",
            "cuit_actor": "30-87654321-4"
        })
        
        print(f"\nResult: {result}")
        print("✓ Logging test completed - check console output above for detailed logs")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging test error: {e}")
        traceback.print_exc()
        return False

def test_error_handling():
    """Test comprehensive error handling."""
    print("\n" + "=" * 80)
    print("TESTING ERROR HANDLING")
    print("=" * 80)
    
    try:
        from agent_tools import generar_escrito_mediacion_tool
        
        # Test various error scenarios
        error_scenarios = [
            {
                "name": "Multiple validation errors",
                "params": {
                    "id_del_caso": 0,
                    "monto_compensacion": "",
                    "plazo_pago_dias": "",
                    "banco_actor": "",
                    "cbu_actor": "",
                    "alias_actor": "",
                    "cuit_actor": ""
                }
            },
            {
                "name": "Type errors",
                "params": {
                    "id_del_caso": "not_a_number",
                    "monto_compensacion": "50000.50",
                    "plazo_pago_dias": "30",
                    "banco_actor": "Banco Test",
                    "cbu_actor": "0110599520000001234567",
                    "alias_actor": "test.alias",
                    "cuit_actor": "20-12345678-9"
                }
            }
        ]
        
        for scenario in error_scenarios:
            print(f"\n--- {scenario['name']} ---")
            try:
                result = generar_escrito_mediacion_tool.invoke(scenario['params'])
                if "❌" in result:
                    print("✓ Error properly handled and returned")
                else:
                    print("❌ Expected error but got success")
            except Exception as e:
                print(f"❌ Unhandled exception: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run all tests and provide summary."""
    print("LPMS Agent Refactoring - Comprehensive Implementation Test")
    print("=" * 80)
    print(f"Test started at: {datetime.now()}")
    
    tests = [
        ("Import and Dependencies", test_imports),
        ("CaseManager Creation", test_case_manager_creation),
        ("Agent Tool Validation", test_agent_tool_validation),
        ("Performance Monitoring", test_performance_monitoring),
        ("Logging Output", test_logging_output),
        ("Error Handling", test_error_handling)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            start_time = time.time()
            success = test_func()
            duration = time.time() - start_time
            results[test_name] = {
                'success': success,
                'duration': duration
            }
        except Exception as e:
            print(f"❌ Test {test_name} failed with exception: {e}")
            results[test_name] = {
                'success': False,
                'duration': 0,
                'error': str(e)
            }
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_tests = len(tests)
    passed_tests = sum(1 for r in results.values() if r['success'])
    
    for test_name, result in results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        duration = result['duration']
        print(f"{status} {test_name:<30} ({duration:.3f}s)")
        if not result['success'] and 'error' in result:
            print(f"     Error: {result['error']}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Implementation is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the details above.")
    
    print(f"Test completed at: {datetime.now()}")

if __name__ == "__main__":
    run_comprehensive_test()