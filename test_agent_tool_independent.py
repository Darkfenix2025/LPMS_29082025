#!/usr/bin/env python3
"""
Test Suite para la Herramienta del Agente - Pruebas Independientes

Este archivo contiene pruebas comprehensivas para la herramienta generar_escrito_mediacion_tool
del módulo agent_tools.py. Las pruebas cubren:

1. Casos de prueba con datos válidos
2. Casos con parámetros inválidos o faltantes  
3. Verificación de mensajes de retorno claros y útiles
4. Confirmación de generación correcta de documentos

Requirements cubiertos: 2.2, 2.3, 6.1, 6.2, 6.4
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from typing import Dict, Any, List, Tuple

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_tools import generar_escrito_mediacion_tool, _validate_comprehensive_parameters
    AGENT_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: No se pudo importar agent_tools: {e}")
    AGENT_TOOLS_AVAILABLE = False


class TestAgentToolIndependent(unittest.TestCase):
    """
    Suite de pruebas para la herramienta del agente generar_escrito_mediacion_tool.
    
    Estas pruebas validan que la herramienta funcione correctamente de manera independiente,
    sin depender de la interfaz de usuario o componentes externos.
    """
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.valid_test_data = {
            "id_del_caso": 1234,
            "monto_compensacion": "150000.50",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco de la Nación Argentina",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "mi.alias.mp",
            "cuit_actor": "20-12345678-9"
        }
        
        # Crear directorio temporal para pruebas de archivos
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpieza después de cada prueba."""
        # Limpiar directorio temporal
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_valid_parameters_basic_case(self):
        """
        Test 1: Caso básico con parámetros válidos
        
        Verifica que la herramienta funcione correctamente con un conjunto
        básico de parámetros válidos.
        
        Requirements: 2.2, 6.1
        """
        print("\n=== Test 1: Caso básico con parámetros válidos ===")
        
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            # Configurar mock del case manager
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = True
            mock_case_manager.return_value = mock_manager
            
            # Ejecutar la herramienta
            result = generar_escrito_mediacion_tool(**self.valid_test_data)
            
            # Verificaciones
            self.assertIsInstance(result, str, "El resultado debe ser un string")
            self.assertIn("✅", result, "El resultado debe indicar éxito")
            self.assertIn("exitosamente", result.lower(), "Debe contener mensaje de éxito")
            self.assertIn(str(self.valid_test_data["id_del_caso"]), result, "Debe mencionar el ID del caso")
            
            # Verificar que se llamó al método correcto
            mock_manager._generar_documento_con_datos.assert_called_once()
            
            print(f"✓ Resultado: {result}")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_valid_parameters_edge_cases(self):
        """
        Test 2: Casos válidos con valores límite
        
        Prueba la herramienta con valores en los límites de validación
        pero que siguen siendo válidos.
        
        Requirements: 2.2, 6.1
        """
        print("\n=== Test 2: Casos válidos con valores límite ===")
        
        edge_cases = [
            {
                "name": "Monto mínimo",
                "data": {**self.valid_test_data, "monto_compensacion": "0.01"}
            },
            {
                "name": "Monto alto",
                "data": {**self.valid_test_data, "monto_compensacion": "999999.99"}
            },
            {
                "name": "Plazo mínimo",
                "data": {**self.valid_test_data, "plazo_pago_dias": "1"}
            },
            {
                "name": "Plazo largo",
                "data": {**self.valid_test_data, "plazo_pago_dias": "365"}
            },
            {
                "name": "Alias mínimo",
                "data": {**self.valid_test_data, "alias_actor": "abc.de"}
            },
            {
                "name": "Alias máximo",
                "data": {**self.valid_test_data, "alias_actor": "a.b.c.d.e.f.g.h.i.j"}
            }
        ]
        
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = True
            mock_case_manager.return_value = mock_manager
            
            for case in edge_cases:
                with self.subTest(case=case["name"]):
                    print(f"  Probando: {case['name']}")
                    
                    result = generar_escrito_mediacion_tool(**case["data"])
                    
                    self.assertIsInstance(result, str)
                    self.assertIn("✅", result, f"Caso '{case['name']}' debe ser exitoso")
                    
                    print(f"  ✓ {case['name']}: OK")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_invalid_case_id_parameters(self):
        """
        Test 3: Parámetros inválidos para ID del caso
        
        Verifica el manejo de errores cuando el ID del caso es inválido.
        
        Requirements: 2.3, 6.2
        """
        print("\n=== Test 3: Parámetros inválidos para ID del caso ===")
        
        invalid_case_ids = [
            {"value": None, "name": "ID None"},
            {"value": 0, "name": "ID cero"},
            {"value": -1, "name": "ID negativo"},
            {"value": "abc", "name": "ID string"},
            {"value": 1.5, "name": "ID float"},
            {"value": [], "name": "ID lista"},
        ]
        
        for case in invalid_case_ids:
            with self.subTest(case_id=case["name"]):
                print(f"  Probando: {case['name']} = {case['value']}")
                
                test_data = {**self.valid_test_data, "id_del_caso": case["value"]}
                
                result = generar_escrito_mediacion_tool(**test_data)
                
                self.assertIsInstance(result, str)
                self.assertIn("❌", result, f"Debe indicar error para {case['name']}")
                self.assertIn("error", result.lower(), "Debe contener la palabra 'error'")
                self.assertIn("id_del_caso", result.lower(), "Debe mencionar el parámetro problemático")
                
                print(f"  ✓ {case['name']}: {result[:100]}...")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_invalid_string_parameters(self):
        """
        Test 4: Parámetros string inválidos
        
        Verifica el manejo de errores para parámetros string inválidos.
        
        Requirements: 2.3, 6.2, 6.4
        """
        print("\n=== Test 4: Parámetros string inválidos ===")
        
        string_params = ["monto_compensacion", "plazo_pago_dias", "banco_actor", 
                        "cbu_actor", "alias_actor", "cuit_actor"]
        
        invalid_values = [
            {"value": None, "name": "None"},
            {"value": "", "name": "String vacío"},
            {"value": "   ", "name": "Solo espacios"},
            {"value": 123, "name": "Número"},
            {"value": [], "name": "Lista"},
            {"value": {}, "name": "Diccionario"},
        ]
        
        for param in string_params:
            for invalid_case in invalid_values:
                with self.subTest(param=param, case=invalid_case["name"]):
                    print(f"  Probando {param} = {invalid_case['name']}")
                    
                    test_data = {**self.valid_test_data, param: invalid_case["value"]}
                    
                    result = generar_escrito_mediacion_tool(**test_data)
                    
                    self.assertIsInstance(result, str)
                    self.assertIn("❌", result, f"Debe indicar error para {param}")
                    self.assertIn("error", result.lower(), "Debe contener 'error'")
                    self.assertIn(param, result.lower(), f"Debe mencionar {param}")
                    
                    print(f"    ✓ Error detectado correctamente")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_invalid_format_parameters(self):
        """
        Test 5: Parámetros con formato inválido
        
        Verifica la validación de formato para parámetros específicos.
        
        Requirements: 2.3, 6.2, 6.4
        """
        print("\n=== Test 5: Parámetros con formato inválido ===")
        
        format_test_cases = [
            {
                "param": "monto_compensacion",
                "invalid_values": ["abc", "-100", "100,000.50", "1e6", ""],
                "description": "Monto inválido"
            },
            {
                "param": "plazo_pago_dias", 
                "invalid_values": ["abc", "-30", "30.5", "0", ""],
                "description": "Plazo inválido"
            },
            {
                "param": "cbu_actor",
                "invalid_values": ["123", "abcd1234567890123456789012", "0110599520000001234", ""],
                "description": "CBU inválido"
            },
            {
                "param": "cuit_actor",
                "invalid_values": ["123", "99-12345678-9", "20-123456789", "abc-def-ghi", ""],
                "description": "CUIT inválido"
            },
            {
                "param": "alias_actor",
                "invalid_values": ["ab", "alias_con_guiones_bajos", "alias con espacios", "a" * 25, ""],
                "description": "Alias inválido"
            }
        ]
        
        for test_case in format_test_cases:
            param = test_case["param"]
            for invalid_value in test_case["invalid_values"]:
                with self.subTest(param=param, value=invalid_value):
                    print(f"  Probando {param} = '{invalid_value}'")
                    
                    test_data = {**self.valid_test_data, param: invalid_value}
                    
                    result = generar_escrito_mediacion_tool(**test_data)
                    
                    self.assertIsInstance(result, str)
                    self.assertIn("❌", result, f"Debe rechazar {param} inválido")
                    self.assertIn("error", result.lower(), "Debe indicar error")
                    
                    print(f"    ✓ Formato inválido detectado")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_nonexistent_case_id(self):
        """
        Test 6: Caso inexistente en la base de datos
        
        Verifica el manejo cuando el caso no existe.
        
        Requirements: 6.1, 6.2
        """
        print("\n=== Test 6: Caso inexistente en la base de datos ===")
        
        with patch('agent_tools._validate_case_id', return_value=False):
            
            result = generar_escrito_mediacion_tool(**self.valid_test_data)
            
            self.assertIsInstance(result, str)
            self.assertIn("❌", result, "Debe indicar error")
            self.assertIn("caso", result.lower(), "Debe mencionar el caso")
            self.assertIn("no existe", result.lower(), "Debe indicar que no existe")
            self.assertIn(str(self.valid_test_data["id_del_caso"]), result, "Debe mencionar el ID")
            
            print(f"✓ Resultado: {result}")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_case_manager_creation_failure(self):
        """
        Test 7: Fallo en la creación del CaseManager
        
        Verifica el manejo de errores cuando no se puede crear el CaseManager.
        
        Requirements: 6.1, 6.2
        """
        print("\n=== Test 7: Fallo en la creación del CaseManager ===")
        
        with patch('agent_tools._validate_case_id', return_value=True), \
             patch('agent_tools._create_case_manager', side_effect=Exception("Error de inicialización")):
            
            result = generar_escrito_mediacion_tool(**self.valid_test_data)
            
            self.assertIsInstance(result, str)
            self.assertIn("❌", result, "Debe indicar error")
            self.assertIn("error", result.lower(), "Debe contener 'error'")
            
            print(f"✓ Resultado: {result}")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_document_generation_failure(self):
        """
        Test 8: Fallo en la generación del documento
        
        Verifica el manejo cuando la generación del documento falla.
        
        Requirements: 6.1, 6.2
        """
        print("\n=== Test 8: Fallo en la generación del documento ===")
        
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            # Configurar mock para que falle la generación
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = False
            mock_case_manager.return_value = mock_manager
            
            result = generar_escrito_mediacion_tool(**self.valid_test_data)
            
            self.assertIsInstance(result, str)
            self.assertIn("❌", result, "Debe indicar error")
            self.assertIn("error", result.lower(), "Debe contener 'error'")
            
            print(f"✓ Resultado: {result}")
    
    @unittest.skipUnless(AGENT_TOOLS_AVAILABLE, "agent_tools no está disponible")
    def test_document_generation_exception(self):
        """
        Test 9: Excepción durante la generación del documento
        
        Verifica el manejo de excepciones inesperadas.
        
        Requirements: 6.1, 6.2
        """
        print("\n=== Test 9: Excepción durante la generación ===")
        
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            # Configurar mock para que lance excepción
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.side_effect = Exception("Error inesperado")
            mock_case_manager.return_value = mock_manager
            
            result = generar_escrito_mediacion_tool(**self.valid_test_data)
            
            self.assertIsInstance(result, str)
            self.assertIn("❌", result, "Debe indicar error")
            self.assertIn("error", result.lower(), "Debe contener 'error'")
            
            print(f"✓ Resultado: {result}")
    
    def test_message_clarity_and_usefulness(self):
        """
        Test 10: Claridad y utilidad de los mensajes
        
        Verifica que todos los mensajes de retorno sean claros y útiles.
        
        Requirements: 6.1, 6.2, 6.4
        """
        print("\n=== Test 10: Claridad y utilidad de los mensajes ===")
        
        if not AGENT_TOOLS_AVAILABLE:
            print("⚠️  agent_tools no disponible, saltando test de mensajes")
            return
        
        # Casos de prueba para diferentes tipos de mensajes
        message_test_cases = [
            {
                "name": "Éxito",
                "setup": lambda: (
                    patch('agent_tools._create_case_manager'),
                    patch('agent_tools._validate_case_id', return_value=True)
                ),
                "expected_elements": ["✅", "exitosamente", "caso", str(self.valid_test_data["id_del_caso"])]
            },
            {
                "name": "Error de validación",
                "data": {**self.valid_test_data, "id_del_caso": -1},
                "expected_elements": ["❌", "error", "validación", "id_del_caso"]
            },
            {
                "name": "Caso inexistente", 
                "setup": lambda: patch('agent_tools._validate_case_id', return_value=False),
                "expected_elements": ["❌", "error", "caso", "no existe"]
            }
        ]
        
        for test_case in message_test_cases:
            with self.subTest(message_type=test_case["name"]):
                print(f"  Verificando mensajes de: {test_case['name']}")
                
                # Configurar mocks si es necesario
                patches = []
                if "setup" in test_case:
                    if test_case["name"] == "Éxito":
                        mock_case_manager, mock_validate = test_case["setup"]()
                        patches = [mock_case_manager, mock_validate]
                        
                        mock_manager = MagicMock()
                        mock_manager._generar_documento_con_datos.return_value = True
                        mock_case_manager.return_value = mock_manager
                    else:
                        patches = [test_case["setup"]()]
                
                # Usar datos específicos del test o datos válidos por defecto
                test_data = test_case.get("data", self.valid_test_data)
                
                # Ejecutar con patches activos
                if patches:
                    with patches[0] if len(patches) == 1 else patches[0].__enter__(), \
                         (patches[1].__enter__() if len(patches) > 1 else patches[0]):
                        result = generar_escrito_mediacion_tool(**test_data)
                else:
                    result = generar_escrito_mediacion_tool(**test_data)
                
                # Verificar elementos esperados en el mensaje
                for element in test_case["expected_elements"]:
                    self.assertIn(element, result, 
                                f"Mensaje debe contener '{element}' para caso {test_case['name']}")
                
                # Verificar que el mensaje no esté vacío y sea informativo
                self.assertTrue(len(result) > 10, "El mensaje debe ser informativo")
                self.assertFalse(result.isspace(), "El mensaje no debe ser solo espacios")
                
                print(f"    ✓ Mensaje claro y útil: {result[:80]}...")
    
    def test_parameter_validation_function(self):
        """
        Test 11: Función de validación de parámetros
        
        Prueba la función auxiliar de validación de parámetros si está disponible.
        
        Requirements: 2.3, 6.2
        """
        print("\n=== Test 11: Función de validación de parámetros ===")
        
        if not AGENT_TOOLS_AVAILABLE:
            print("⚠️  agent_tools no disponible, saltando test de validación")
            return
        
        try:
            # Probar validación con parámetros válidos
            is_valid, errors = _validate_comprehensive_parameters(**self.valid_test_data)
            
            self.assertTrue(is_valid, "Parámetros válidos deben pasar la validación")
            self.assertEqual(len(errors), 0, "No debe haber errores con parámetros válidos")
            
            print("  ✓ Validación de parámetros válidos: OK")
            
            # Probar validación con parámetros inválidos
            invalid_data = {**self.valid_test_data, "id_del_caso": -1, "monto_compensacion": "abc"}
            is_valid, errors = _validate_comprehensive_parameters(**invalid_data)
            
            self.assertFalse(is_valid, "Parámetros inválidos deben fallar la validación")
            self.assertGreater(len(errors), 0, "Debe haber errores con parámetros inválidos")
            
            print(f"  ✓ Validación de parámetros inválidos: {len(errors)} errores detectados")
            
        except NameError:
            print("  ⚠️  Función _validate_comprehensive_parameters no disponible")
    
    def test_comprehensive_integration(self):
        """
        Test 12: Prueba de integración comprehensiva
        
        Ejecuta un flujo completo simulando condiciones reales.
        
        Requirements: 2.2, 2.3, 6.1, 6.4
        """
        print("\n=== Test 12: Prueba de integración comprehensiva ===")
        
        if not AGENT_TOOLS_AVAILABLE:
            print("⚠️  agent_tools no disponible, saltando test de integración")
            return
        
        # Simular múltiples casos de uso realistas
        realistic_cases = [
            {
                "name": "Mediación laboral típica",
                "data": {
                    "id_del_caso": 1001,
                    "monto_compensacion": "75000.00",
                    "plazo_pago_dias": "45",
                    "banco_actor": "Banco de la Nación Argentina",
                    "cbu_actor": "0110599520000001234567",
                    "alias_actor": "empleado.indemnizacion",
                    "cuit_actor": "20-12345678-9"
                }
            },
            {
                "name": "Mediación comercial",
                "data": {
                    "id_del_caso": 2002,
                    "monto_compensacion": "250000.50",
                    "plazo_pago_dias": "30",
                    "banco_actor": "Banco Santander Argentina S.A.",
                    "cbu_actor": "0720001234000056789012",
                    "alias_actor": "empresa.comercial.2024",
                    "cuit_actor": "30-87654321-4"
                }
            },
            {
                "name": "Acuerdo civil alto monto",
                "data": {
                    "id_del_caso": 3003,
                    "monto_compensacion": "500000",
                    "plazo_pago_dias": "90",
                    "banco_actor": "Banco Macro S.A.",
                    "cbu_actor": "2850590940090418135201",
                    "alias_actor": "acuerdo.civil.mp",
                    "cuit_actor": "27-11223344-5"
                }
            }
        ]
        
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = True
            mock_case_manager.return_value = mock_manager
            
            for case in realistic_cases:
                with self.subTest(case=case["name"]):
                    print(f"  Ejecutando: {case['name']}")
                    
                    result = generar_escrito_mediacion_tool(**case["data"])
                    
                    # Verificaciones comprehensivas
                    self.assertIsInstance(result, str, "Resultado debe ser string")
                    self.assertIn("✅", result, "Debe indicar éxito")
                    self.assertGreater(len(result), 20, "Mensaje debe ser informativo")
                    self.assertIn(str(case["data"]["id_del_caso"]), result, "Debe mencionar ID del caso")
                    
                    print(f"    ✓ {case['name']}: Exitoso")


def run_comprehensive_tests():
    """
    Ejecuta todas las pruebas de manera organizada y genera un reporte.
    """
    print("=" * 80)
    print("SUITE DE PRUEBAS INDEPENDIENTES PARA HERRAMIENTA DEL AGENTE")
    print("=" * 80)
    print(f"Fecha: {os.popen('date').read().strip() if os.name != 'nt' else 'N/A'}")
    print(f"Sistema: {sys.platform}")
    print(f"Python: {sys.version}")
    print("=" * 80)
    
    # Verificar disponibilidad de dependencias
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ CRÍTICO: agent_tools no está disponible")
        print("   Verifique que el archivo agent_tools.py existe y es importable")
        return False
    
    print("✅ agent_tools disponible")
    
    # Crear suite de pruebas
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestAgentToolIndependent)
    
    # Ejecutar pruebas con reporte detallado
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generar resumen final
    print("\n" + "=" * 80)
    print("RESUMEN DE PRUEBAS")
    print("=" * 80)
    print(f"Pruebas ejecutadas: {result.testsRun}")
    print(f"Exitosas: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallidas: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.failures:
        print("\nFALLOS:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORES:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("   La herramienta del agente está funcionando correctamente")
    else:
        print("\n⚠️  ALGUNAS PRUEBAS FALLARON")
        print("   Revise los errores antes de usar la herramienta en producción")
    
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)