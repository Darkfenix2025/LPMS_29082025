#!/usr/bin/env python3
"""
Test script for the intelligent document saving functionality.
This script tests the new helper methods added to CaseManager.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the CaseManager class
from case_dialog_manager import CaseManager

class TestIntelligentSaving(unittest.TestCase):
    """Test cases for the intelligent saving functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.app_controller = Mock()
        self.case_manager = CaseManager(self.app_controller)

        # Sample case data for testing
        self.sample_case_data = {
            'id': 1,
            'caratula': 'Demanda por Cobro de Pesos',
            'numero_expediente': '12345',
            'anio_caratula': '2024',
            'ruta_carpeta': ''  # Will be set in individual tests
        }

    def test_is_valid_folder_path_valid(self):
        """Test _is_valid_folder_path with a valid folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.case_manager._is_valid_folder_path(temp_dir)
            self.assertTrue(result)

    def test_is_valid_folder_path_invalid(self):
        """Test _is_valid_folder_path with invalid paths."""
        # Test with non-existent path
        result = self.case_manager._is_valid_folder_path('/non/existent/path')
        self.assertFalse(result)

        # Test with file instead of directory
        with tempfile.NamedTemporaryFile() as temp_file:
            result = self.case_manager._is_valid_folder_path(temp_file.name)
            self.assertFalse(result)

        # Test with empty string
        result = self.case_manager._is_valid_folder_path('')
        self.assertFalse(result)

        # Test with None
        result = self.case_manager._is_valid_folder_path(None)
        self.assertFalse(result)

    def test_save_document_with_none_ruta_carpeta(self):
        """Test _save_document method when ruta_carpeta is None."""
        # Set ruta_carpeta to None (simulating database returning None)
        case_data_with_none = self.sample_case_data.copy()
        case_data_with_none['ruta_carpeta'] = None

        # Mock document
        mock_doc = Mock()
        def mock_save(filepath):
            with open(filepath, 'w') as f:
                f.write('test content')
        mock_doc.save = mock_save

        # Mock database
        self.case_manager.db = Mock()
        self.case_manager.db.update_case_folder.return_value = True

        # Mock user selecting a directory
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('case_dialog_manager.filedialog.askdirectory', return_value=temp_dir), \
                 patch('case_dialog_manager.messagebox.showwarning'), \
                 patch('case_dialog_manager.messagebox.showinfo'), \
                 patch('case_dialog_manager.messagebox.askyesno', return_value=False):

                result = self.case_manager._save_document(mock_doc, case_data_with_none)

                # Should return True (successful save)
                self.assertTrue(result)

                # Should have updated the database
                self.case_manager.db.update_case_folder.assert_called_once_with(
                    case_data_with_none['id'], temp_dir
                )

    def test_generate_document_filename(self):
        """Test _generate_document_filename method."""
        filename = self.case_manager._generate_document_filename(
            self.sample_case_data,
            "Acuerdo Mediacion"
        )

        # Check that filename contains expected parts
        self.assertIn("Acuerdo Mediacion", filename)
        self.assertIn("12345", filename)
        self.assertIn("Demanda_por_Cobro_de_Pesos", filename)
        self.assertTrue(filename.endswith('.docx'))

    def test_generate_document_filename_no_expediente(self):
        """Test _generate_document_filename with no expediente number."""
        case_data_no_exp = self.sample_case_data.copy()
        case_data_no_exp['numero_expediente'] = ''

        filename = self.case_manager._generate_document_filename(
            case_data_no_exp,
            "Acuerdo Mediacion"
        )

        # Should use date as fallback
        self.assertIn("Acuerdo Mediacion", filename)
        self.assertIn("Demanda_por_Cobro_de_Pesos", filename)
        self.assertTrue(filename.endswith('.docx'))

    def test_generate_generic_document_filename(self):
        """Test _generate_generic_document_filename method."""
        titulo_escrito = "Demanda de Divorcio"

        filename = self.case_manager._generate_generic_document_filename(
            self.sample_case_data,
            titulo_escrito
        )

        # Check that filename contains expected parts
        self.assertIn("Borrador", filename)
        self.assertIn("Demanda_de_Divorcio", filename)
        self.assertIn("12345", filename)
        self.assertTrue(filename.endswith('.docx'))

    def test_verify_document_saved(self):
        """Test _verify_document_saved method."""
        # Test with valid file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(b'test content')
            temp_file_path = temp_file.name

        try:
            result = self.case_manager._verify_document_saved(temp_file_path)
            self.assertTrue(result)
        finally:
            os.unlink(temp_file_path)

        # Test with non-existent file
        result = self.case_manager._verify_document_saved('/non/existent/file.docx')
        self.assertFalse(result)

        # Test with empty file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file_path = temp_file.name

        try:
            result = self.case_manager._verify_document_saved(temp_file_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_file_path)

    @patch('case_dialog_manager.messagebox.showinfo')
    @patch('case_dialog_manager.filedialog.askdirectory')
    @patch('case_dialog_manager.messagebox.showerror')
    def test_save_document_intelligent_case_a(self, mock_showerror, mock_askdirectory, mock_showinfo):
        """Test _save_document_intelligent with case A (folder assigned)."""
        # Mock a valid folder path
        with tempfile.TemporaryDirectory() as temp_dir:
            self.sample_case_data['ruta_carpeta'] = temp_dir

            # Mock document that actually creates a file
            mock_doc = Mock()
            def mock_save(filepath):
                with open(filepath, 'w') as f:
                    f.write('test content')
            mock_doc.save = mock_save

            # Mock database
            self.case_manager.db = Mock()

            result = self.case_manager._save_document_intelligent(
                mock_doc,
                self.sample_case_data,
                "Test Document"
            )

            # Should return a path (successful save)
            self.assertIsNotNone(result)
            self.assertTrue(result.endswith('.docx'))
            self.assertTrue(os.path.exists(result))

            # Should not ask for directory
            mock_askdirectory.assert_not_called()

            # Should show success message
            mock_showinfo.assert_called_once()

            # Should not show error
            mock_showerror.assert_not_called()

    @patch('case_dialog_manager.messagebox.showwarning')
    @patch('case_dialog_manager.messagebox.showinfo')
    @patch('case_dialog_manager.filedialog.askdirectory')
    @patch('case_dialog_manager.messagebox.showerror')
    def test_save_document_intelligent_case_b(self, mock_showerror, mock_askdirectory, mock_showinfo, mock_showwarning):
        """Test _save_document_intelligent with case B (no folder assigned)."""
        # No folder assigned
        self.sample_case_data['ruta_carpeta'] = ''

        # Mock user selecting a directory
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_askdirectory.return_value = temp_dir

            # Mock document that actually creates a file
            mock_doc = Mock()
            def mock_save(filepath):
                with open(filepath, 'w') as f:
                    f.write('test content')
            mock_doc.save = mock_save

            # Mock database
            self.case_manager.db = Mock()
            self.case_manager.db.update_case_folder.return_value = True

            result = self.case_manager._save_document_intelligent(
                mock_doc,
                self.sample_case_data,
                "Test Document"
            )

            # Should return a path (successful save)
            self.assertIsNotNone(result)
            self.assertTrue(result.endswith('.docx'))
            self.assertTrue(os.path.exists(result))

            # Should ask for directory
            mock_askdirectory.assert_called_once()

            # Should show warning first, then success
            mock_showwarning.assert_called_once()
            mock_showinfo.assert_called_once()

            # Should not show error
            mock_showerror.assert_not_called()

            # Should update database
            self.case_manager.db.update_case_folder.assert_called_once_with(
                self.sample_case_data['id'], temp_dir
            )

    @patch('case_dialog_manager.filedialog.askdirectory')
    @patch('case_dialog_manager.messagebox.showerror')
    @patch('case_dialog_manager.messagebox.showwarning')
    @patch('case_dialog_manager.messagebox.askyesno')
    def test_save_document_intelligent_case_b_cancelled(self, mock_askyesno, mock_showwarning, mock_showerror, mock_askdirectory):
        """Test _save_document_intelligent when user cancels folder selection."""
        # No folder assigned
        self.sample_case_data['ruta_carpeta'] = ''

        # Mock user cancelling directory selection
        mock_askdirectory.return_value = None

        # Mock document
        mock_doc = Mock()

        # Mock messagebox to avoid tkinter issues
        mock_showwarning.return_value = None
        mock_askyesno.return_value = False  # Don't try to open folder

        result = self.case_manager._save_document_intelligent(
            mock_doc,
            self.sample_case_data,
            "Test Document"
        )

        # Should return None (cancelled)
        self.assertIsNone(result)

        # Should not save document
        mock_doc.save.assert_not_called()

        # Should show warning about no folder assigned
        mock_showwarning.assert_called_once()

        # Should not show error (this is expected cancellation)
        mock_showerror.assert_not_called()

if __name__ == '__main__':
    print("Running tests for intelligent saving functionality...")
    unittest.main(verbosity=2)