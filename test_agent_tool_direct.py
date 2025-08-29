#!/usr/bin/env python3
"""
Test Suite Directo para la Herramienta del Agente

Este archivo prueba la función generar_escrito_mediacion_tool directamente,
sin pasar por el wrapper de LangChain, para validar la lógica interna.

Requirements cubiertos: 2.2, 2.3, 6.1, 6.2, 6.4
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Importar la función directamente
    from agent_tools import generar_escrito_mediacion_tool
    AGENT_TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"Error: No se pudo importar agent_tools: {e}")
    AGENT_TOOLS_AVAILABLE = False


def test_valid_parameters():
    """
    Test 1: Caso básico con parámetros válidos
    """
    print("\n=== Test 1: Caso básico con parámetros válidos ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    valid_data = {
        "id_del_caso": 1234,
        "monto_compensacion": "150000.50",
        "plazo_pago_dias": "30",
        "banco_actor": "Banco de la Nación Argentina",
        "cbu_actor": "0110599520000001234567",
        "alias_actor": "mi.alias.mp",
        "cuit_actor": "20-12345678-9"
    }
    
    try:
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            # Configurar mock del case manager
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = {
                'success': True,
                'error_message': None,
                'error_type': None,
                'filename_suggestion': 'acuerdo_mediacion_caso_1234.docx'
            }
            mock_case_manager.return_value = mock_manager
            
            # Llamar a la función directamente
            result = generar_escrito_mediacion_tool.func(**valid_data)
            
            print(f"✓ Resultado: {result}")
            
            # Verificaciones básicas
            if not isinstance(result, str):
                print(f"❌ Error: Resultado no es string: {type(result)}")
                return False
                
            if "✅" not in result:
                print(f"❌ Error: Resultado no indica éxito: {result}")
                return False
                
            if "exitosamente" not in result.lower():
                print(f"❌ Error: Resultado no contiene mensaje de éxito: {result}")
                return False
                
            print("✅ Test 1 PASÓ")
            return True
            
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def test_invalid_case_id():
    """
    Test 2: ID de caso inválido
    """
    print("\n=== Test 2: ID de caso inválido ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    invalid_data = {
        "id_del_caso": -1,  # ID inválido
        "monto_compensacion": "150000.50",
        "plazo_pago_dias": "30",
        "banco_actor": "Banco de la Nación Argentina",
        "cbu_actor": "0110599520000001234567",
        "alias_actor": "mi.alias.mp",
        "cuit_actor": "20-12345678-9"
    }
    
    try:
        result = generar_escrito_mediacion_tool.func(**invalid_data)
        
        print(f"✓ Resultado: {result}")
        
        # Verificaciones
        if not isinstance(result, str):
            print(f"❌ Error: Resultado no es string: {type(result)}")
            return False
            
        if "❌" not in result:
            print(f"❌ Error: Resultado no indica error: {result}")
            return False
            
        if "error" not in result.lower():
            print(f"❌ Error: Resultado no contiene 'error': {result}")
            return False
            
        print("✅ Test 2 PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def test_invalid_string_parameters():
    """
    Test 3: Parámetros string inválidos
    """
    print("\n=== Test 3: Parámetros string inválidos ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    # Test con monto inválido
    invalid_data = {
        "id_del_caso": 1234,
        "monto_compensacion": "abc",  # Monto inválido
        "plazo_pago_dias": "30",
        "banco_actor": "Banco de la Nación Argentina",
        "cbu_actor": "0110599520000001234567",
        "alias_actor": "mi.alias.mp",
        "cuit_actor": "20-12345678-9"
    }
    
    try:
        result = generar_escrito_mediacion_tool.func(**invalid_data)
        
        print(f"✓ Resultado: {result}")
        
        # Verificaciones
        if not isinstance(result, str):
            print(f"❌ Error: Resultado no es string: {type(result)}")
            return False
            
        if "❌" not in result:
            print(f"❌ Error: Resultado no indica error: {result}")
            return False
            
        if "monto_compensacion" not in result.lower():
            print(f"❌ Error: Resultado no menciona el parámetro problemático: {result}")
            return False
            
        print("✅ Test 3 PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def test_nonexistent_case():
    """
    Test 4: Caso inexistente en la base de datos
    """
    print("\n=== Test 4: Caso inexistente ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    valid_data = {
        "id_del_caso": 9999,
        "monto_compensacion": "150000.50",
        "plazo_pago_dias": "30",
        "banco_actor": "Banco de la Nación Argentina",
        "cbu_actor": "0110599520000001234567",
        "alias_actor": "mi.alias.mp",
        "cuit_actor": "20-12345678-9"
    }
    
    try:
        with patch('agent_tools._validate_case_id', return_value=False):
            result = generar_escrito_mediacion_tool.func(**valid_data)
            
            print(f"✓ Resultado: {result}")
            
            # Verificaciones
            if not isinstance(result, str):
                print(f"❌ Error: Resultado no es string: {type(result)}")
                return False
                
            if "❌" not in result:
                print(f"❌ Error: Resultado no indica error: {result}")
                return False
                
            if "no existe" not in result.lower():
                print(f"❌ Error: Resultado no indica que el caso no existe: {result}")
                return False
                
            print("✅ Test 4 PASÓ")
            return True
            
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def test_case_manager_failure():
    """
    Test 5: Fallo en la creación del CaseManager
    """
    print("\n=== Test 5: Fallo en CaseManager ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    valid_data = {
        "id_del_caso": 1234,
        "monto_compensacion": "150000.50",
        "plazo_pago_dias": "30",
        "banco_actor": "Banco de la Nación Argentina",
        "cbu_actor": "0110599520000001234567",
        "alias_actor": "mi.alias.mp",
        "cuit_actor": "20-12345678-9"
    }
    
    try:
        with patch('agent_tools._validate_case_id', return_value=True), \
             patch('agent_tools._create_case_manager', side_effect=Exception("Error de inicialización")):
            
            result = generar_escrito_mediacion_tool.func(**valid_data)
            
            print(f"✓ Resultado: {result}")
            
            # Verificaciones
            if not isinstance(result, str):
                print(f"❌ Error: Resultado no es string: {type(result)}")
                return False
                
            if "❌" not in result:
                print(f"❌ Error: Resultado no indica error: {result}")
                return False
                
            if "error" not in result.lower():
                print(f"❌ Error: Resultado no contiene 'error': {result}")
                return False
                
            print("✅ Test 5 PASÓ")
            return True
            
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def test_document_generation_failure():
    """
    Test 6: Fallo en la generación del documento
    """
    print("\n=== Test 6: Fallo en generación de documento ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    valid_data = {
        "id_del_caso": 1234,
        "monto_compensacion": "150000.50",
        "plazo_pago_dias": "30",
        "banco_actor": "Banco de la Nación Argentina",
        "cbu_actor": "0110599520000001234567",
        "alias_actor": "mi.alias.mp",
        "cuit_actor": "20-12345678-9"
    }
    
    try:
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            # Configurar mock para que falle la generación
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = {
                'success': False,
                'error_message': 'Error simulado en la generación del documento',
                'error_type': 'template_error',
                'filename_suggestion': None
            }
            mock_case_manager.return_value = mock_manager
            
            result = generar_escrito_mediacion_tool.func(**valid_data)
            
            print(f"✓ Resultado: {result}")
            
            # Verificaciones
            if not isinstance(result, str):
                print(f"❌ Error: Resultado no es string: {type(result)}")
                return False
                
            if "❌" not in result:
                print(f"❌ Error: Resultado no indica error: {result}")
                return False
                
            print("✅ Test 6 PASÓ")
            return True
            
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def test_format_validation():
    """
    Test 7: Validación de formatos específicos
    """
    print("\n=== Test 7: Validación de formatos ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    # Test CBU inválido
    invalid_cbu_data = {
        "id_del_caso": 1234,
        "monto_compensacion": "150000.50",
        "plazo_pago_dias": "30",
        "banco_actor": "Banco de la Nación Argentina",
        "cbu_actor": "123",  # CBU muy corto
        "alias_actor": "mi.alias.mp",
        "cuit_actor": "20-12345678-9"
    }
    
    try:
        result = generar_escrito_mediacion_tool.func(**invalid_cbu_data)
        
        print(f"✓ Resultado CBU inválido: {result}")
        
        # Verificaciones
        if "❌" not in result or "cbu_actor" not in result.lower():
            print(f"❌ Error: No detectó CBU inválido correctamente")
            return False
        
        # Test CUIT inválido
        invalid_cuit_data = {
            "id_del_caso": 1234,
            "monto_compensacion": "150000.50",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco de la Nación Argentina",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "mi.alias.mp",
            "cuit_actor": "99-12345678-9"  # Prefijo inválido
        }
        
        result = generar_escrito_mediacion_tool.func(**invalid_cuit_data)
        
        print(f"✓ Resultado CUIT inválido: {result}")
        
        # Verificaciones
        if "❌" not in result or "cuit_actor" not in result.lower():
            print(f"❌ Error: No detectó CUIT inválido correctamente")
            return False
            
        print("✅ Test 7 PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def test_edge_cases():
    """
    Test 8: Casos límite válidos
    """
    print("\n=== Test 8: Casos límite válidos ===")
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ agent_tools no disponible")
        return False
    
    edge_cases = [
        {
            "name": "Monto mínimo",
            "data": {
                "id_del_caso": 1234,
                "monto_compensacion": "0.01",
                "plazo_pago_dias": "1",
                "banco_actor": "Banco de la Nación Argentina",
                "cbu_actor": "0110599520000001234567",
                "alias_actor": "abc.de",
                "cuit_actor": "20-12345678-9"
            }
        },
        {
            "name": "Valores altos",
            "data": {
                "id_del_caso": 1234,
                "monto_compensacion": "999999.99",
                "plazo_pago_dias": "365",
                "banco_actor": "Banco Santander Argentina S.A.",
                "cbu_actor": "0720001234000056789012",
                "alias_actor": "a.b.c.d.e.f.g.h.i.j",
                "cuit_actor": "30-87654321-4"
            }
        }
    ]
    
    try:
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = {
                'success': True,
                'error_message': None,
                'error_type': None,
                'filename_suggestion': 'acuerdo_mediacion_caso_1234.docx'
            }
            mock_case_manager.return_value = mock_manager
            
            for case in edge_cases:
                print(f"  Probando: {case['name']}")
                
                result = generar_escrito_mediacion_tool.func(**case["data"])
                
                if "✅" not in result:
                    print(f"❌ Error en {case['name']}: {result}")
                    return False
                    
                print(f"  ✓ {case['name']}: OK")
            
            print("✅ Test 8 PASÓ")
            return True
            
    except Exception as e:
        print(f"❌ Error ejecutando test: {e}")
        return False


def run_all_tests():
    """
    Ejecuta todos los tests y genera un reporte
    """
    print("=" * 80)
    print("SUITE DE PRUEBAS DIRECTAS PARA HERRAMIENTA DEL AGENTE")
    print("=" * 80)
    
    if not AGENT_TOOLS_AVAILABLE:
        print("❌ CRÍTICO: agent_tools no está disponible")
        return False
    
    tests = [
        ("Parámetros válidos", test_valid_parameters),
        ("ID de caso inválido", test_invalid_case_id),
        ("Parámetros string inválidos", test_invalid_string_parameters),
        ("Caso inexistente", test_nonexistent_case),
        ("Fallo en CaseManager", test_case_manager_failure),
        ("Fallo en generación", test_document_generation_failure),
        ("Validación de formatos", test_format_validation),
        ("Casos límite", test_edge_cases)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error en test '{test_name}': {e}")
            failed += 1
    
    print("\n" + "=" * 80)
    print("RESUMEN DE PRUEBAS")
    print("=" * 80)
    print(f"Total de pruebas: {len(tests)}")
    print(f"Exitosas: {passed}")
    print(f"Fallidas: {failed}")
    
    if failed == 0:
        print("\n🎉 TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("   La herramienta del agente está funcionando correctamente")
        return True
    else:
        print(f"\n⚠️  {failed} PRUEBAS FALLARON")
        print("   Revise los errores antes de usar la herramienta en producción")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)