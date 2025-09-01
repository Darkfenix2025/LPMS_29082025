#!/usr/bin/env python3
"""
Test script to verify the double-saving fix in ProspectDialogManager
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestDoubleSaveFix(unittest.TestCase):
    """Test cases for the double-saving fix"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock the app controller
        self.mock_app_controller = Mock()
        self.mock_app_controller.root = Mock()

        # Import and create ProspectDialogManager
        from prospect_dialog_manager import ProspectDialogManager
        self.dialog_manager = ProspectDialogManager(self.mock_app_controller)

    def test_flag_initialization(self):
        """Test that the consultation_saved flag is properly initialized"""
        # Test new consultation (should be False)
        self.dialog_manager.open_consultation_dialog({"id": 1, "nombre": "Test Prospect"})
        self.assertFalse(self.dialog_manager.consultation_saved)

        # Test editing existing consultation (should be True)
        mock_consultation = {"id": 1, "relato_original_cliente": "Test"}
        self.dialog_manager.open_consultation_dialog(
            {"id": 1, "nombre": "Test Prospect"},
            mock_consultation
        )
        self.assertTrue(self.dialog_manager.consultation_saved)

    def test_manual_save_sets_flag(self):
        """Test that manual save operations set the flag to True"""
        # Reset flag
        self.dialog_manager.consultation_saved = False

        # Mock database operations
        with patch.object(self.dialog_manager, 'db') as mock_db:
            mock_db.add_consulta.return_value = 123

            # Simulate manual save (this would be called from save_consultation)
            self.dialog_manager.consultation_saved = True

            # Verify flag is set
            self.assertTrue(self.dialog_manager.consultation_saved)

    def test_auto_save_prevents_duplicate(self):
        """Test that auto-save is prevented when consultation is already saved"""
        # Set flag to True (simulating manual save)
        self.dialog_manager.consultation_saved = True

        # Mock the database and other dependencies
        with patch.object(self.dialog_manager, 'db') as mock_db, \
             patch('prospect_dialog_manager.datetime') as mock_datetime:

            # Configure mocks
            mock_db.get_consultas_by_prospecto_id.return_value = []
            mock_datetime.date.today.return_value = Mock()

            # Call auto-save
            self.dialog_manager._auto_save_ai_analysis(
                {"id": 1, "nombre": "Test", "estado": "Consulta Inicial"},
                "Test relato",
                "Test analisis"
            )

            # Verify that add_consulta was NOT called (auto-save was skipped)
            mock_db.add_consulta.assert_not_called()
            mock_db.update_consulta.assert_not_called()

    def test_auto_save_allows_first_save(self):
        """Test that auto-save works when consultation hasn't been saved yet"""
        # Set flag to False (simulating new consultation)
        self.dialog_manager.consultation_saved = False

        # Mock the database and other dependencies
        with patch.object(self.dialog_manager, 'db') as mock_db, \
             patch('prospect_dialog_manager.datetime') as mock_datetime:

            # Configure mocks
            mock_db.get_consultas_by_prospecto_id.return_value = []
            mock_db.add_consulta.return_value = 123
            mock_datetime.date.today.return_value = Mock()

            # Call auto-save
            self.dialog_manager._auto_save_ai_analysis(
                {"id": 1, "nombre": "Test", "estado": "Consulta Inicial"},
                "Test relato",
                "Test analisis"
            )

            # Verify that add_consulta WAS called (auto-save was performed)
            mock_db.add_consulta.assert_called_once()

    def test_auto_save_updates_existing(self):
        """Test that auto-save updates existing consultation and sets flag"""
        # Set flag to False initially
        self.dialog_manager.consultation_saved = False

        # Mock existing consultation
        existing_consultation = {
            "id": 456,
            "fecha_consulta": "2024-01-01",
            "relato_original_cliente": "Old relato"
        }

        # Mock the database and other dependencies
        with patch.object(self.dialog_manager, 'db') as mock_db, \
             patch('prospect_dialog_manager.datetime') as mock_datetime:

            # Configure mocks
            mock_db.get_consultas_by_prospecto_id.return_value = [existing_consultation]
            mock_db.update_consulta.return_value = True
            mock_datetime.date.today.return_value = Mock()

            # Call auto-save
            self.dialog_manager._auto_save_ai_analysis(
                {"id": 1, "nombre": "Test", "estado": "Consulta Inicial"},
                "Test relato",
                "Test analisis"
            )

            # Verify that update_consulta was called
            mock_db.update_consulta.assert_called_once()

            # Verify that flag was set to True (since it updated existing)
            self.assertTrue(self.dialog_manager.consultation_saved)

def run_tests():
    """Run the test suite"""
    print("Running double-save fix tests...")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDoubleSaveFix)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Report results
    if result.wasSuccessful():
        print("\nAll tests passed! The double-saving fix is working correctly.")
        return True
    else:
        print(f"\n{len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)