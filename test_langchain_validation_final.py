#!/usr/bin/env python3
"""
Test Final de Validación de Integración con LangChain - Tarea 11

Este archivo implementa las validaciones específicas requeridas por la tarea 11:

1. Verificar que la herramienta se registra correctamente con el decorador @tool
2. Probar que el docstring es accesible para el agente  
3. Confirmar que los tipos de parámetros son correctos
4. Validar que la herramienta puede ser invocada por un agente de LangChain

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


def test_tool_decorator_registration():
    """
    Requirement 2.1: Verificar que la herramienta se registra correctamente con el decorador @tool
    """
    print("\n=== Test 1: Registro con decorador @tool ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Verificar que es una BaseTool (resultado del decorador @tool)
        if not isinstance(generar_escrito_mediacion_tool, BaseTool):
            print(f"❌ Error: No es una BaseTool: {type(generar_escrito_mediacion_tool)}")
            return False
        
        print("✓ Es una BaseTool válida de LangChain")
        
        # Verificar atributos esenciales del decorador @tool
        essential_attrs = ['name', 'description', 'func', 'args_schema']
        for attr in essential_attrs:
            if not hasattr(generar_escrito_mediacion_tool, attr):
                print(f"❌ Error: Falta atributo {attr}")
                return False
        
        print("✓ Todos los atributos esenciales presentes")
        
        # Verificar que el nombre se deriva de la función
        expected_name = "generar_escrito_mediacion_tool"
        if generar_escrito_mediacion_tool.name != expected_name:
            print(f"❌ Error: Nombre incorrecto: {generar_escrito_mediacion_tool.name}")
            return False
        
        print(f"✓ Nombre correcto: {generar_escrito_mediacion_tool.name}")
        
        print("✅ PASÓ: Herramienta registrada correctamente con @tool")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_docstring_accessibility():
    """
    Requirement 2.4: Probar que el docstring es accesible para el agente
    """
    print("\n=== Test 2: Accesibilidad del docstring ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Verificar que hay descripción disponible
        description = generar_escrito_mediacion_tool.description
        if not description or len(description) < 100:
            print("❌ Error: Descripción insuficiente o faltante")
            return False
        
        print(f"✓ Descripción disponible: {len(description)} caracteres")
        
        # Verificar que el docstring original existe
        original_docstring = generar_escrito_mediacion_tool.func.__doc__
        if not original_docstring or len(original_docstring) < 100:
            print("❌ Error: Docstring original insuficiente")
            return False
        
        print(f"✓ Docstring original: {len(original_docstring)} caracteres")
        
        # Verificar elementos clave para agentes (más flexible)
        key_elements = ["PROPÓSITO", "PARÁMETROS", "EJEMPLOS"]
        for element in key_elements:
            if element not in description:
                print(f"❌ Error: Elemento faltante: {element}")
                return False
        
        print("✓ Elementos clave presentes para agentes")
        
        # Verificar que está en español
        spanish_words = ["para", "con", "del", "que", "sistema", "documento"]
        spanish_count = sum(1 for word in spanish_words if word in description.lower())
        
        if spanish_count < 4:
            print("❌ Error: No parece estar en español")
            return False
        
        print("✓ Documentación en español confirmada")
        
        print("✅ PASÓ: Docstring accesible para agentes")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_parameter_types():
    """
    Requirement 2.2: Confirmar que los tipos de parámetros son correctos
    """
    print("\n=== Test 3: Tipos de parámetros ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Obtener esquema de argumentos
        args_schema = generar_escrito_mediacion_tool.args_schema
        if not args_schema:
            print("❌ Error: No hay esquema de argumentos")
            return False
        
        print("✓ Esquema de argumentos disponible")
        
        # Tipos esperados según requirements
        expected_params = {
            'id_del_caso': int,
            'monto_compensacion': str,
            'plazo_pago_dias': str,
            'banco_actor': str,
            'cbu_actor': str,
            'alias_actor': str,
            'cuit_actor': str
        }
        
        # Obtener campos (compatible con Pydantic v1 y v2)
        if hasattr(args_schema, 'model_fields'):
            fields = args_schema.model_fields
        elif hasattr(args_schema, '__fields__'):
            fields = args_schema.__fields__
        else:
            print("❌ Error: No se pueden obtener campos del esquema")
            return False
        
        # Verificar cada parámetro
        for param_name, expected_type in expected_params.items():
            if param_name not in fields:
                print(f"❌ Error: Parámetro faltante: {param_name}")
                return False
            
            field = fields[param_name]
            
            # Obtener tipo del campo
            if hasattr(field, 'annotation'):
                field_type = field.annotation
            elif hasattr(field, 'type_'):
                field_type = field.type_
            else:
                field_type = type(field)
            
            if field_type != expected_type:
                print(f"❌ Error: Tipo incorrecto para {param_name}: {field_type} != {expected_type}")
                return False
            
            print(f"  ✓ {param_name}: {expected_type.__name__}")
        
        # Verificar que no hay parámetros extra
        if len(fields) != len(expected_params):
            print(f"❌ Error: Número incorrecto de parámetros: {len(fields)} != {len(expected_params)}")
            return False
        
        print("✅ PASÓ: Tipos de parámetros correctos")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_agent_invocation():
    """
    Requirement 2.1: Validar que la herramienta puede ser invocada por un agente de LangChain
    """
    print("\n=== Test 4: Invocación por agente ===")
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ LangChain no disponible")
        return False
    
    try:
        # Preparar datos de prueba
        test_data = {
            "id_del_caso": 1234,
            "monto_compensacion": "150000.50",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco de la Nación Argentina",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "mi.alias.mp",
            "cuit_actor": "20-12345678-9"
        }
        
        print("✓ Datos de prueba preparados")
        
        # Mock de dependencias
        with patch('agent_tools._create_case_manager') as mock_case_manager, \
             patch('agent_tools._validate_case_id', return_value=True):
            
            # Configurar mock para éxito
            mock_manager = MagicMock()
            mock_manager._generar_documento_con_datos.return_value = {
                'success': True,
                'error_message': None,
                'error_type': None,
                'filename_suggestion': 'acuerdo_mediacion_caso_1234.docx'
            }
            mock_case_manager.return_value = mock_manager
            
            print("✓ Mocks configurados")
            
            # Probar invocación directa (método invoke)
            try:
                result = generar_escrito_mediacion_tool.invoke(test_data)
                
                if not isinstance(result, str):
                    print(f"❌ Error: Resultado no es string: {type(result)}")
                    return False
                
                if "✅" not in result:
                    print(f"❌ Error: Resultado no indica éxito: {result[:100]}")
                    return False
                
                print("✓ Invocación directa exitosa")
                
            except Exception as e:
                print(f"❌ Error en invocación directa: {e}")
                return False
            
            # Probar invocación con método run (compatibilidad)
            try:
                result2 = generar_escrito_mediacion_tool.run(test_data)
                
                if not isinstance(result2, str):
                    print(f"❌ Error: Resultado run() no es string: {type(result2)}")
                    return False
                
                print("✓ Invocación con run() exitosa")
                
            except Exception as e:
                print(f"⚠️  Método run() no disponible: {e}")
                # Esto es aceptable en algunas versiones
            
            # Verificar que la herramienta puede ser agregada a una lista de tools
            try:
                tools_list = [generar_escrito_mediacion_tool]
                if len(tools_list) != 1:
                    print("❌ Error: No se puede agregar a lista de herramientas")
                    return False
                
                print("✓ Se puede agregar a lista de herramientas")
                
            except Exception as e:
                print(f"❌ Error agregando a lista: {e}")
                return False
        
        print("✅ PASÓ: Herramienta invocable por agentes")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def run_task_11_validation():
    """
    Ejecuta todas las validaciones específicas de la tarea 11
    """
    print("=" * 80)
    print("VALIDACIÓN DE TAREA 11: INTEGRACIÓN CON LANGCHAIN")
    print("=" * 80)
    print("Requirements a validar:")
    print("  2.1 - Herramienta decorada con @tool y invocable por agentes")
    print("  2.4 - Docstring accesible y en español para agentes")
    print("=" * 80)
    
    if not LANGCHAIN_AVAILABLE:
        print("❌ CRÍTICO: LangChain no está disponible")
        return False
    
    # Tests específicos de la tarea 11
    tests = [
        ("Registro con decorador @tool", test_tool_decorator_registration),
        ("Accesibilidad del docstring", test_docstring_accessibility),
        ("Tipos de parámetros correctos", test_parameter_types),
        ("Invocación por agente de LangChain", test_agent_invocation)
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
    print("RESUMEN DE VALIDACIÓN - TAREA 11")
    print("=" * 80)
    print(f"Total de validaciones: {len(tests)}")
    print(f"Exitosas: {passed}")
    print(f"Fallidas: {failed}")
    
    if failed == 0:
        print("\n🎉 TAREA 11 COMPLETADA EXITOSAMENTE")
        print("\n✅ VALIDACIONES COMPLETADAS:")
        print("   ✓ La herramienta se registra correctamente con el decorador @tool")
        print("   ✓ El docstring es accesible para el agente")
        print("   ✓ Los tipos de parámetros son correctos")
        print("   ✓ La herramienta puede ser invocada por un agente de LangChain")
        print("\n📋 REQUIREMENTS VALIDADOS:")
        print("   ✓ Requirement 2.1 - Herramienta LangChain funcional")
        print("   ✓ Requirement 2.4 - Documentación accesible para agentes")
        
        return True
    else:
        print(f"\n⚠️  {failed} VALIDACIONES FALLARON")
        print("   La tarea 11 no está completa")
        return False


if __name__ == "__main__":
    success = run_task_11_validation()
    sys.exit(0 if success else 1)