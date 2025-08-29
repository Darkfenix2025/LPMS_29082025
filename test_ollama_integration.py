#!/usr/bin/env python3
"""
Test script to verify Ollama integration in prospect_dialog_manager.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ollama_connection():
    """Test basic Ollama connection"""
    try:
        from langchain_community.llms import Ollama

        print("Testing Ollama connection...")
        llm = Ollama(
            model="gpt-oss:20b",
            temperature=0.3,
            base_url="http://localhost:11434"
        )

        # Test simple query
        response = llm.invoke("Responde solo 'OK' si puedes procesar este mensaje.")
        print(f"[OK] Ollama connection successful: {response.strip()}")
        return True

    except Exception as e:
        print(f"[ERROR] Ollama connection failed: {e}")
        return False

def test_prospect_ai_method():
    """Test the modified _call_local_ollama_ai method"""
    try:
        from prospect_dialog_manager import ProspectDialogManager

        print("Testing ProspectDialogManager AI method...")

        # Create instance (we'll need to mock the app_controller)
        class MockAppController:
            def __init__(self):
                self.root = None

        mock_controller = MockAppController()
        dialog_manager = ProspectDialogManager(mock_controller)

        # Test the AI method
        test_prompt = "Analiza este caso legal simple: Un cliente sufrió un accidente de tránsito."
        result = dialog_manager._call_local_ollama_ai(test_prompt)

        if "error" in result:
            print(f"[ERROR] AI method failed: {result['error']}")
            return False
        else:
            print(f"[OK] AI method successful: {result['result'][:100]}...")
            return True

    except Exception as e:
        print(f"[ERROR] AI method test failed: {e}")
        return False

def main():
    print("=" * 60)
    print("TESTING OLLAMA INTEGRATION FIX")
    print("=" * 60)

    tests = [
        ("Ollama Connection", test_ollama_connection),
        ("Prospect AI Method", test_prospect_ai_method)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        if test_func():
            passed += 1
        print("-" * 40)

    print(f"\nRESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("[SUCCESS] ALL TESTS PASSED! The Ollama integration fix is working correctly.")
        return True
    else:
        print("[FAILURE] Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)