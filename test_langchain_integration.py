#!/usr/bin/env python3
"""
Test de Integración con LangChain

Este archivo prueba que la herramienta se integre correctamente con LangChain
y que pueda ser invocada por agentes de IA.

Requirements cubiertos: 2.1, 2.4
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Agregar el directorio raíz al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from agent_tools import generar_escrito_mediacion_tool
    from langchain.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    print(f"Error: No se pudo importar dependencias: {e}")
    LANGCHAIN_AVAILABLE = False


def test_langchain_tool_registration():
    """
    Test 1: Verificar que la herramienta se registra correctamente con LangChain
    """
    print("\n=== Test 1: Registro con LangChain ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Verificar que es una instancia de BaseTool
        if not isinstance(generar_escrito_mediacion_tool, BaseTool):
            print(f"❌ Error: No es una BaseTool de LangChain: {type(generar_escrito_mediacion_tool)}")
            return False
        
        print("✓ La herramienta es una BaseTool válida de LangChain")
        
        # Verificar que tiene nombre
        if not hasattr(generar_escrito_mediacion_tool, 'name') or not generar_escrito_mediacion_tool.name:
            print("❌ Error: La herramienta no tiene nombre")
            return False
            
        print(f"✓ Nombre de la herramienta: {generar_escrito_mediacion_tool.name}")
        
        # Verificar que tiene descripción
        if not hasattr(generar_escrito_mediacion_tool, 'description') or not generar_escrito_mediacion_tool.description:
            print("❌ Error: La herramienta no tiene descripción")
            return False
            
        print(f"✓ Descripción disponible: {len(generar_escrito_mediacion_tool.description)} caracteres")
        
        print("✅ Test 1 PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False


def test_tool_schema():
    """
    Test 2: Verificar el esquema de parámetros de la herramienta
    """
    print("\n=== Test 2: Esquema de parámetros ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Obtener el esquema de argumentos
        args_schema = generar_escrito_mediacion_tool.args_schema
        
        if not args_schema:
            print("❌ Error: No hay esquema de argumentos")
            return False
            
        print("✓ Esquema de argumentos disponible")
        
        # Verificar parámetros requeridos
        expected_params = [
            'id_del_caso', 'monto_compensacion', 'plazo_pago_dias',
            'banco_actor', 'cbu_actor', 'alias_actor', 'cuit_actor'
        ]
        
        # Obtener campos del esquema (compatible con Pydantic v2)
        if hasattr(args_schema, 'model_fields'):
            schema_fields = args_schema.model_fields
        elif hasattr(args_schema, '__fields__'):
            schema_fields = args_schema.__fields__
        else:
            schema_fields = {}
        
        for param in expected_params:
            if param not in schema_fields:
                print(f"❌ Error: Parámetro faltante en esquema: {param}")
                return False
            field_info = schema_fields[param]
            field_type = getattr(field_info, 'annotation', getattr(field_info, 'type_', 'unknown'))
            print(f"  ✓ {param}: {field_type}")
        
        print("✅ Test 2 PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False


def test_tool_invocation():
    """
    Test 3: Probar invocación de la herramienta a través de LangChain
    """
    print("\n=== Test 3: Invocación a través de LangChain ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Datos de prueba
        test_input = {
            "id_del_caso": 1234,
            "monto_compensacion": "150000.50",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco de la Nación Argentina",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "mi.alias.mp",
            "cuit_actor": "20-12345678-9"
        }
        
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            # Configurar mock
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = {
                'success': True,
                'error_message': None,
                'error_type': None,
                'filename_suggestion': 'acuerdo_mediacion_caso_1234.docx'
            }
            mock_case_manager.return_value = mock_manager
            
            # Invocar la herramienta usando el método run de LangChain
            result = generar_escrito_mediacion_tool.run(test_input)
            
            print(f"✓ Resultado de invocación: {result[:100]}...")
            
            # Verificaciones
            if not isinstance(result, str):
                print(f"❌ Error: Resultado no es string: {type(result)}")
                return False
                
            if "✅" not in result:
                print(f"❌ Error: Resultado no indica éxito: {result}")
                return False
                
            print("✅ Test 3 PASÓ")
            return True
            
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False


def test_tool_documentation():
    """
    Test 4: Verificar que la documentación es accesible para agentes
    """
    print("\n=== Test 4: Documentación para agentes ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Verificar docstring
        docstring = generar_escrito_mediacion_tool.func.__doc__
        
        if not docstring:
            print("❌ Error: No hay docstring")
            return False
            
        print(f"✓ Docstring disponible: {len(docstring)} caracteres")
        
        # Verificar elementos clave en la documentación
        required_elements = [
            "PROPÓSITO", "FUNCIONAMIENTO", "PARÁMETROS", 
            "VALORES DE RETORNO", "EJEMPLOS"
        ]
        
        for element in required_elements:
            if element not in docstring:
                print(f"❌ Error: Elemento faltante en documentación: {element}")
                return False
            print(f"  ✓ {element}: Presente")
        
        # Verificar que está en español
        spanish_indicators = ["para", "con", "del", "que", "una", "los"]
        spanish_count = sum(1 for word in spanish_indicators if word in docstring.lower())
        
        if spanish_count < 3:
            print("❌ Error: La documentación no parece estar en español")
            return False
            
        print("✓ Documentación en español confirmada")
        
        print("✅ Test 4 PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False


def test_error_handling_through_langchain():
    """
    Test 5: Verificar manejo de errores a través de LangChain
    """
    print("\n=== Test 5: Manejo de errores a través de LangChain ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Datos inválidos
        invalid_input = {
            "id_del_caso": -1,  # ID inválido
            "monto_compensacion": "abc",  # Monto inválido
            "plazo_pago_dias": "30",
            "banco_actor": "Banco de la Nación Argentina",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "mi.alias.mp",
            "cuit_actor": "20-12345678-9"
        }
        
        # Invocar con datos inválidos
        result = generar_escrito_mediacion_tool.run(invalid_input)
        
        print(f"✓ Resultado con datos inválidos: {result[:100]}...")
        
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
            
        print("✓ Errores manejados correctamente a través de LangChain")
        
        print("✅ Test 5 PASÓ")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {e}")
        return False


def run_langchain_integration_tests():
    """
    Ejecuta todos los tests de integración con LangChain
    """
    print("=" * 80)
    print("SUITE DE PRUEBAS DE INTEGRACIÓN CON LANGCHAIN")
    print("=" * 80)
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ CRÍTICO: LangChain no está disponible")
        return False
    
    tests = [
        ("Registro con LangChain", test_langchain_tool_registration),
        ("Esquema de parámetros", test_tool_schema),
        ("Invocación a través de LangChain", test_tool_invocation),
        ("Documentación para agentes", test_tool_documentation),
        ("Manejo de errores", test_error_handling_through_langchain)
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
    print("RESUMEN DE PRUEBAS DE INTEGRACIÓN")
    print("=" * 80)
    print(f"Total de pruebas: {len(tests)}")
    print(f"Exitosas: {passed}")
    print(f"Fallidas: {failed}")
    
    if failed == 0:
        print("\n🎉 TODAS LAS PRUEBAS DE INTEGRACIÓN PASARON")
        print("   La herramienta está correctamente integrada con LangChain")
        return True
    else:
        print(f"\n⚠️  {failed} PRUEBAS DE INTEGRACIÓN FALLARON")
        print("   Revise los errores antes de usar con agentes de IA")
        return False


if __name__ == "__main__":
    success = run_langchain_integration_tests()
    sys.exit(0 if success else 1)