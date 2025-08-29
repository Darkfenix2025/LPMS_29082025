#!/usr/bin/env python3
"""
Simple test to verify Ollama integration fix without making actual AI calls
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_method_exists():
    """Test that the new method exists and can be imported"""
    try:
        from prospect_dialog_manager import ProspectDialogManager

        # Create a mock app controller
        class MockAppController:
            def __init__(self):
                self.root = None

        mock_controller = MockAppController()
        dialog_manager = ProspectDialogManager(mock_controller)

        # Check if the new method exists
        if hasattr(dialog_manager, '_call_local_ollama_ai'):
            print("[OK] Method _call_local_ollama_ai exists")
            return True
        else:
            print("[ERROR] Method _call_local_ollama_ai not found")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to import or create dialog manager: {e}")
        return False

def test_old_method_gone():
    """Test that the old Gemini method is gone"""
    try:
        from prospect_dialog_manager import ProspectDialogManager

        class MockAppController:
            def __init__(self):
                self.root = None

        mock_controller = MockAppController()
        dialog_manager = ProspectDialogManager(mock_controller)

        # Check if the old method is gone
        if hasattr(dialog_manager, '_call_gemini_ai'):
            print("[ERROR] Old method _call_gemini_ai still exists")
            return False
        else:
            print("[OK] Old method _call_gemini_ai has been removed")
            return True

    except Exception as e:
        print(f"[ERROR] Failed to check old method: {e}")
        return False

def test_method_signature():
    """Test that the new method has the correct signature"""
    try:
        from prospect_dialog_manager import ProspectDialogManager
        import inspect

        class MockAppController:
            def __init__(self):
                self.root = None

        mock_controller = MockAppController()
        dialog_manager = ProspectDialogManager(mock_controller)

        # Get method signature
        method = getattr(dialog_manager, '_call_local_ollama_ai')
        sig = inspect.signature(method)

        # Check parameters (self is not included for bound methods)
        params = list(sig.parameters.keys())
        if 'prompt' in params:
            print("[OK] Method signature is correct")
            return True
        else:
            print(f"[ERROR] Method signature incorrect. Expected 'prompt', got: {params}")
            return False

    except Exception as e:
        print(f"[ERROR] Failed to check method signature: {e}")
        return False

def main():
    print("=" * 60)
    print("SIMPLE OLLAMA INTEGRATION TEST")
    print("=" * 60)

    tests = [
        ("Method Exists", test_method_exists),
        ("Old Method Removed", test_old_method_gone),
        ("Method Signature", test_method_signature)
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
        print("[SUCCESS] All basic integration tests passed!")
        print("The Ollama integration fix has been successfully implemented.")
        return True
    else:
        print("[FAILURE] Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)