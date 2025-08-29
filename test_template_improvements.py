#!/usr/bin/env python3
"""
Test script for the improved mediation agreement template.
This script tests the new template that supports multiple parties with representatives.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

# Add the current directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the CaseManager class
from case_dialog_manager import CaseManager

class TestTemplateImprovements(unittest.TestCase):
    """Test cases for the improved mediation agreement template."""

    def setUp(self):
        """Set up test fixtures."""
        self.app_controller = Mock()
        self.case_manager = CaseManager(self.app_controller)

        # Sample case data for testing
        self.sample_case_data = {
            'id': 1,
            'caratula': 'Demanda por Cobro de Pesos',
            'numero_expediente': '12345/2024',
            'juzgado': 'Juzgado Civil 1',
            'notas': 'El actor reclama el pago de la suma de $50.000 por servicios prestados.'
        }

        # Sample parties data
        self.sample_actores = [
            {
                'id': 1,
                'nombre_completo': 'Juan Pérez',
                'dni': '12345678',
                'cuit': '20123456789',
                'domicilio_real': 'Calle Falsa 123, Buenos Aires',
                'domicilio_legal': 'Calle Real 456, Buenos Aires'
            }
        ]

        self.sample_demandados = [
            {
                'id': 2,
                'nombre_completo': 'Empresa XYZ S.A.',
                'dni': '',
                'cuit': '30765432198',
                'domicilio_real': 'Av. Empresarial 789, Buenos Aires',
                'domicilio_legal': 'Av. Legal 101, Buenos Aires'
            }
        ]

    def test_prepare_parties_with_representatives(self):
        """Test _prepare_parties_with_representatives method."""
        # Test with actors
        actores_data = self.case_manager._prepare_parties_with_representatives(
            self.sample_actores, 'ACTOR', self.sample_case_data['id']
        )

        self.assertEqual(len(actores_data), 1)
        actor = actores_data[0]
        self.assertEqual(actor['nombre_completo'], 'Juan Pérez')
        self.assertEqual(actor['dni'], '12345678')
        self.assertEqual(actor['cuit'], '20123456789')
        self.assertIsInstance(actor['representantes'], list)

        # Test with defendants
        demandados_data = self.case_manager._prepare_parties_with_representatives(
            self.sample_demandados, 'DEMANDADO', self.sample_case_data['id']
        )

        self.assertEqual(len(demandados_data), 1)
        demandado = demandados_data[0]
        self.assertEqual(demandado['nombre_completo'], 'Empresa XYZ S.A.')
        self.assertEqual(demandado['cuit'], '30765432198')
        self.assertIsInstance(demandado['representantes'], list)

    def test_get_representatives_for_party(self):
        """Test _get_representatives_for_party method."""
        # Mock the database call
        with patch('case_dialog_manager.db.get_roles_by_case_id', return_value=[]):
            representantes = self.case_manager._get_representatives_for_party(1, 1, 1)

            # Should return empty list when no representatives found
            self.assertIsInstance(representantes, list)
            self.assertEqual(len(representantes), 0)

    def test_template_context_structure(self):
        """Test that the context includes the new structured data."""
        # Mock the database and other dependencies
        with patch('case_dialog_manager.db.get_roles_by_case_id', return_value=[]), \
             patch.object(self.case_manager, '_format_parties_text', return_value='Test Party'):

            # Simulate the context creation process
            case_id = self.sample_case_data['id']
            lista_actores = self.sample_actores
            lista_demandados = self.sample_demandados
            caso_data = self.sample_case_data

            # This simulates the code that would be in the actual method
            actores_texto = self.case_manager._format_parties_text(lista_actores, 'ACTOR')
            demandados_texto = self.case_manager._format_parties_text(lista_demandados, 'DEMANDADO')

            ACTORES = self.case_manager._prepare_parties_with_representatives(lista_actores, 'ACTOR', case_id)
            DEMANDADOS = self.case_manager._prepare_parties_with_representatives(lista_demandados, 'DEMANDADO', case_id)

            detalles_caso = caso_data.get('notas', 'Sin detalles adicionales del caso.')

            # Verify the structure
            self.assertIsInstance(ACTORES, list)
            self.assertIsInstance(DEMANDADOS, list)
            self.assertIsInstance(detalles_caso, str)
            self.assertEqual(len(ACTORES), 1)
            self.assertEqual(len(DEMANDADOS), 1)

            # Verify actor data structure
            actor = ACTORES[0]
            self.assertIn('nombre_completo', actor)
            self.assertIn('dni', actor)
            self.assertIn('cuit', actor)
            self.assertIn('domicilio_real', actor)
            self.assertIn('domicilio_legal', actor)
            self.assertIn('representantes', actor)

            # Verify defendant data structure
            demandado = DEMANDADOS[0]
            self.assertIn('nombre_completo', demandado)
            self.assertIn('dni', demandado)
            self.assertIn('cuit', demandado)
            self.assertIn('domicilio_real', demandado)
            self.assertIn('domicilio_legal', demandado)
            self.assertIn('representantes', demandado)

    def test_new_template_exists(self):
        """Test that the new template file exists."""
        template_path = 'plantillas/mediacion/acuerdo_base_nuevo.docx'
        self.assertTrue(os.path.exists(template_path), f"New template should exist at {template_path}")

if __name__ == '__main__':
    print("Running tests for improved mediation agreement template...")
    unittest.main(verbosity=2)