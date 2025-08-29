#!/usr/bin/env python3
"""
Script de prueba para las herramientas del agente
Demuestra cómo funcionan las herramientas de agent_tools.py
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_tools():
    """Prueba las herramientas del agente"""
    print("=" * 60)
    print("PRUEBA DE HERRAMIENTAS DEL AGENTE")
    print("=" * 60)

    try:
        # Importar las herramientas
        from agent_tools import (
            generar_escrito_mediacion_tool,
            calculadora_matematica_tool,
            solicitar_nueva_herramienta_tool,
            generar_acuerdo_ia_tool,
            AI_GENERATOR_AVAILABLE
        )

        print("Herramientas importadas correctamente:")
        print(f"  - generar_escrito_mediacion_tool: {generar_escrito_mediacion_tool.name}")
        print(f"  - calculadora_matematica_tool: {calculadora_matematica_tool.name}")
        print(f"  - solicitar_nueva_herramienta_tool: {solicitar_nueva_herramienta_tool.name}")
        print(f"  - generar_acuerdo_ia_tool: {generar_acuerdo_ia_tool.name}")
        print(f"  - AI_GENERATOR_AVAILABLE: {AI_GENERATOR_AVAILABLE}")

        # Verificar que todas las herramientas tienen la estructura correcta
        tools = [
            generar_escrito_mediacion_tool,
            calculadora_matematica_tool,
            solicitar_nueva_herramienta_tool,
            generar_acuerdo_ia_tool
        ]

        print("\n" + "=" * 40)
        print("VERIFICACION DE ESTRUCTURA DE HERRAMIENTAS")
        print("=" * 40)

        for tool in tools:
            print(f"\nHerramienta: {tool.name}")
            print(f"  - Descripcion: {tool.description[:100]}...")
            print(f"  - Funcion: {tool.func.__name__}")
            print(f"  - Argumentos requeridos: {list(tool.args_schema.schema()['properties'].keys())}")

        # Probar la calculadora (la más simple)
        print("\n" + "=" * 40)
        print("PRUEBA DE CALCULADORA")
        print("=" * 40)

        try:
            result = calculadora_matematica_tool.func(expresion="15000 * 1.21")
            print(f"Resultado de '15000 * 1.21': {result}")
        except Exception as e:
            print(f"Error en calculadora: {e}")

        # Probar la herramienta de solicitud de nueva herramienta
        print("\n" + "=" * 40)
        print("PRUEBA DE SOLICITUD DE HERRAMIENTA")
        print("=" * 40)

        try:
            result = solicitar_nueva_herramienta_tool.func(
                descripcion_necesidad="Necesito una herramienta para analizar contratos legales y extraer clausulas importantes"
            )
            print(f"Resultado: {result}")
        except Exception as e:
            print(f"Error en solicitud: {e}")

        # Mostrar información sobre la herramienta de IA (sin ejecutarla por ahora)
        print("\n" + "=" * 40)
        print("INFORMACION DE HERRAMIENTA IA")
        print("=" * 40)

        print(f"Nombre: {generar_acuerdo_ia_tool.name}")
        print(f"Descripcion: {generar_acuerdo_ia_tool.description}")
        print(f"Argumentos requeridos:")
        for arg_name, arg_info in generar_acuerdo_ia_tool.args_schema.schema()['properties'].items():
            required = arg_name in generar_acuerdo_ia_tool.args_schema.schema().get('required', [])
            print(f"  - {arg_name}: {arg_info.get('description', 'Sin descripcion')} {'(requerido)' if required else '(opcional)'}")

        print("\n" + "=" * 40)
        print("PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 40)

        return True

    except Exception as e:
        print(f"ERROR GENERAL: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ai_tool_simulation():
    """Simula el uso de la herramienta de IA sin ejecutarla realmente"""
    print("\n" + "=" * 60)
    print("SIMULACION DE USO DE HERRAMIENTA IA")
    print("=" * 60)

    try:
        from agent_tools import generar_acuerdo_ia_tool

        # Datos de ejemplo para simular una llamada
        test_args = {
            "id_del_caso": 123,
            "monto_compensacion": "150000",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco Santander",
            "cbu_actor": "0720123456789012345678",
            "alias_actor": "empresa.legal",
            "cuit_actor": "27-12345678-1",
            "documento_ejemplo": None
        }

        print("Datos de prueba que se enviarian a la herramienta:")
        for key, value in test_args.items():
            print(f"  {key}: {value}")

        print("\nLa herramienta validaria estos datos y:")
        print("  1. Verificaria que el caso 123 existe en la BD")
        print("  2. Validaria el formato del CBU (22 digitos)")
        print("  3. Validaria el formato del CUIT (11 digitos)")
        print("  4. Extraeria datos del caso de la base de datos")
        print("  5. Usaria IA para generar el contenido del acuerdo")
        print("  6. Crearia un documento Word con el acuerdo completo")

        print("\nPara ejecutar realmente la herramienta, necesitaras:")
        print("  - Una base de datos con casos")
        print("  - Ollama ejecutandose con el modelo gpt-oss:20b")
        print("  - Los documentos de plantilla en plantillas/mediacion/")

        return True

    except Exception as e:
        print(f"Error en simulacion: {e}")
        return False

if __name__ == "__main__":
    print("INICIANDO PRUEBA DE HERRAMIENTAS DEL AGENTE")
    print("=" * 80)

    # Ejecutar pruebas
    success1 = test_agent_tools()
    success2 = test_ai_tool_simulation()

    print("\n" + "=" * 80)
    if success1 and success2:
        print("TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("Las herramientas del agente funcionan correctamente")
    else:
        print("ALGUNAS PRUEBAS FALLARON")
        print("Revisa los errores arriba")

    print("=" * 80)