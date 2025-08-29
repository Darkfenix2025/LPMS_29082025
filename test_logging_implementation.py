#!/usr/bin/env python3
"""
Test script for the logging and monitoring implementation in agent tools.
"""

import sys
import logging
from agent_tools import generar_escrito_mediacion_tool, get_agent_tools_performance_stats, reset_agent_tools_performance_stats

# Configure logging to see all messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_logging_implementation():
    """Test the logging and monitoring implementation."""
    
    print("=" * 80)
    print("TESTING LOGGING AND MONITORING IMPLEMENTATION")
    print("=" * 80)
    
    # Reset statistics
    reset_agent_tools_performance_stats()
    print("✓ Performance statistics reset")
    
    # Test 1: Valid parameters (should succeed if case exists)
    print("\n--- Test 1: Valid Parameters ---")
    try:
        result = generar_escrito_mediacion_tool.invoke({
            "id_del_caso": 1,
            "monto_compensacion": "50000.50",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco de la Nación Argentina",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "test.mediacion",
            "cuit_actor": "20-12345678-9"
        })
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 2: Invalid parameters (should fail validation)
    print("\n--- Test 2: Invalid Parameters ---")
    try:
        result = generar_escrito_mediacion_tool.invoke({
            "id_del_caso": -1,  # Invalid case ID
            "monto_compensacion": "invalid_amount",  # Invalid amount
            "plazo_pago_dias": "invalid_days",  # Invalid days
            "banco_actor": "",  # Empty bank
            "cbu_actor": "123",  # Invalid CBU
            "alias_actor": "x",  # Too short alias
            "cuit_actor": "invalid"  # Invalid CUIT
        })
        print(f"Result: {result}")
    except Exception as e:
        print(f"Exception: {e}")
    
    # Test 3: Check performance statistics
    print("\n--- Performance Statistics ---")
    stats = get_agent_tools_performance_stats()
    print(f"Total calls: {stats['total_calls']}")
    print(f"Successful calls: {stats['successful_calls']}")
    print(f"Failed calls: {stats['failed_calls']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")
    print(f"Average duration: {stats['average_duration']:.3f}s")
    print(f"Last call time: {stats['last_call_time']}")
    
    print("\n✅ Logging and monitoring test completed!")
    print("Check the console output above for detailed logging information.")

if __name__ == "__main__":
    test_logging_implementation()