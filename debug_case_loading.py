#!/usr/bin/env python3
"""
Debug script to trace case list loading issues in the actual application
"""

import sys
import os
import traceback

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_case_loading():
    """Debug the case loading functionality step by step"""
    print("=" * 80)
    print("DEBUGGING CASE LIST LOADING IN ACTUAL APPLICATION")
    print("=" * 80)

    try:
        # Import required modules
        print("\n[1] Importing modules...")
        import crm_database as db
        from case_dialog_manager import CaseManager
        from client_dialog_manager import ClientManager

        print("[OK] All modules imported successfully")

        # Test database connection
        print("\n[2] Testing database connection...")
        conn = db.connect_db()
        if not conn:
            print("[ERROR] Database connection failed")
            return False
        conn.close()
        print("[OK] Database connection successful")

        # Get clients
        print("\n[3] Getting clients from database...")
        clients = db.get_clients()
        if not clients:
            print("[ERROR] No clients found in database")
            return False
        print(f"[OK] Found {len(clients)} clients")

        # Test with first client
        if clients:
            first_client = clients[0]
            client_id = first_client['id']
            client_name = first_client['nombre']
            print(f"\n[4] Testing with client: {client_name} (ID: {client_id})")

            # Test get_cases_by_client directly
            print("\n[5] Testing get_cases_by_client function...")
            cases = db.get_cases_by_client(client_id)
            if cases is None:
                print("[ERROR] get_cases_by_client returned None")
                return False
            print(f"[OK] get_cases_by_client returned {len(cases)} cases")

            # Test CaseManager initialization
            print("\n[6] Testing CaseManager initialization...")

            # Mock classes
            class MockButton:
                def __init__(self, name):
                    self.name = name

                def config(self, state):
                    print(f"    [MOCK] Button {self.name} state set to: {state}")

            class MockCaseTree:
                def __init__(self):
                    self.items = []
                    self.children = []

                def insert(self, parent, index, values, iid=None):
                    item = {"values": values, "iid": iid}
                    self.items.append(item)
                    self.children.append(str(values[0]))  # Add to children list
                    print(f"    [MOCK] Inserted case: ID={values[0]}, Expediente={values[1]}, Caratula={values[2][:50]}...")

                def get_children(self, item=""):
                    """Mock get_children method"""
                    return self.children

                def delete(self, item):
                    """Mock delete method"""
                    if item in self.children:
                        self.children.remove(item)
                    # Also remove from items
                    self.items = [i for i in self.items if str(i.get("values", [None])[0]) != item]
                    print(f"    [MOCK] Deleted case item: {item}")

            # Create a mock app controller
            class MockAppController:
                def __init__(self):
                    self.selected_case = None
                    self.case_tree_items = []

                    # Mock buttons
                    self.edit_case_btn = MockButton("edit_case_btn")
                    self.delete_case_btn = MockButton("delete_case_btn")
                    self.add_case_btn = MockButton("add_case_btn")

                    # Mock case tree
                    self.case_tree = MockCaseTree()

                def clear_case_list(self):
                    self.case_tree_items = []
                    print("    [MOCK] Case list cleared")

                def disable_case_buttons(self):
                    print("    [MOCK] Case buttons disabled")

                def update_add_audiencia_button_state(self):
                    print("    [MOCK] Add audiencia button state updated")

            mock_app = MockAppController()

            # Create CaseManager
            case_manager = CaseManager(mock_app)
            print("[OK] CaseManager created successfully")

            # Test load_cases_by_client
            print("\n[7] Testing load_cases_by_client method...")
            result = case_manager.load_cases_by_client(client_id)

            if result:
                print(f"[OK] load_cases_by_client completed successfully")
                print(f"    - Cases loaded: {len(mock_app.case_tree.items)}")
                for i, item in enumerate(mock_app.case_tree.items, 1):
                    values = item['values']
                    print(f"    - Case {i}: ID={values[0]}, Expediente={values[1]}, Caratula={values[2][:50]}...")
            else:
                print("[ERROR] load_cases_by_client failed")
                return False

        print("\n" + "=" * 80)
        print("[SUCCESS] All tests passed! Case loading should work in the application.")
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n[ERROR] Exception during debugging: {e}")
        print("Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_case_loading()
    sys.exit(0 if success else 1)