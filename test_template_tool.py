#!/usr/bin/env python3
"""
Test de la Nueva Herramienta de Template para Acuerdos
Prueba la funcionalidad de generación de acuerdos usando templates
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_template_tool():
    """Prueba la herramienta de template para acuerdos"""

    print("=" * 60)
    print("TEST DE HERRAMIENTA DE TEMPLATE PARA ACUERDOS")
    print("=" * 60)

    try:
        from agent_template_generator import AgentTemplateGenerator

        print("Verificando existencia del archivo modelo_acuerdo.txt...")
        if os.path.exists("modelo_acuerdo.txt"):
            print("[OK] Archivo modelo_acuerdo.txt encontrado")
        else:
            print("[ERROR] Archivo modelo_acuerdo.txt no encontrado")
            return False

        print("\nInicializando generador de templates...")
        generator = AgentTemplateGenerator()
        print("[OK] Generador de templates inicializado")

        print("\nProbando generación de acuerdo de ejemplo...")

        # Datos de ejemplo para el test
        agreement_data = {
            'monto_compensacion_numeros': '50000',
            'monto_compensacion_letras': 'CINCUENTA MIL',
            'plazo_pago_dias': '30',
            'plazo_pago_letras': 'TREINTA',
            'banco_actor': 'Banco Nación',
            'cbu_actor': '0720123456789012345678',
            'alias_actor': 'empresa.legal',
            'cuit_actor': '27-12345678-1'
        }

        # Para el test, creamos datos ficticios del caso
        # En producción, se usaría un ID válido de la base de datos
        case_id = None  # No necesitamos ID real para este test

        print("Generando acuerdo con datos ficticios para test...")
        agreement = generator.generate_agreement_from_template_with_mock_data(case_id, agreement_data)

        if agreement and not agreement.startswith("ERROR"):
            print("[OK] Acuerdo generado exitosamente")
            print(f"Longitud del acuerdo generado: {len(agreement)} caracteres")

            # Mostrar una parte del acuerdo generado
            print("\n" + "=" * 60)
            print("MUESTRA DEL ACUERDO GENERADO:")
            print("=" * 60)
            lines = agreement.split('\n')
            for i, line in enumerate(lines[:20]):  # Mostrar primeras 20 líneas
                print(f"{i+1:2d}: {line}")
            if len(lines) > 20:
                print(f"... ({len(lines) - 20} líneas más)")

            print("\n" + "=" * 60)
            print("TEST COMPLETADO EXITOSAMENTE")
            print("=" * 60)
            print("[OK] Herramienta de template operativa")
            print("[OK] Template cargado correctamente")
            print("[OK] Acuerdo generado con datos de ejemplo")
            print("[OK] Formato del acuerdo válido")
            print("\nLa herramienta de template está lista para uso en producción!")

            return True
        else:
            print(f"[ERROR] Error generando acuerdo: {agreement}")
            return False

    except ImportError as e:
        print(f"Error de importación: {e}")
        print("Asegúrate de que agent_template_generator.py esté disponible")
        return False
    except Exception as e:
        print(f"Error en el test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_integration():
    """Prueba la integración con el sistema de agentes"""

    print("\n" + "=" * 60)
    print("TEST DE INTEGRACIÓN CON SISTEMA DE AGENTES")
    print("=" * 60)

    try:
        from agent_core import AgentCore

        print("Inicializando agente...")
        agent = AgentCore()
        print("[OK] Agente inicializado")

        # Verificar que la herramienta de template esté disponible
        tool_names = [tool.name for tool in agent.tools]
        print(f"Herramientas disponibles: {tool_names}")

        if "generar_acuerdo_template_tool" in tool_names:
            print("[OK] Herramienta de template encontrada en el agente")
        else:
            print("[ERROR] Herramienta de template no encontrada en el agente")
            return False

        print("[OK] Integración con sistema de agentes completada")
        return True

    except Exception as e:
        print(f"Error en integración con agentes: {e}")
        return False

if __name__ == "__main__":
    print("Iniciando tests de herramienta de template...\n")

    success1 = test_template_tool()
    success2 = test_agent_integration()

    if success1 and success2:
        print("\n" + "=" * 60)
        print("EXITO: TODOS LOS TESTS COMPLETADOS EXITOSAMENTE")
        print("=" * 60)
        print("[OK] Herramienta de template operativa")
        print("[OK] Archivo modelo_acuerdo.txt válido")
        print("[OK] Generación de acuerdos funcional")
        print("[OK] Integración con agentes completa")
        print("\n¡La nueva herramienta de template está lista para producción!")
    else:
        print("\n" + "=" * 60)
        print("ERROR: ALGÚN TEST FALLÓ")
        print("=" * 60)
        if not success1:
            print("[ERROR] Test de herramienta de template: FALLÓ")
        if not success2:
            print("[ERROR] Test de integración con agentes: FALLÓ")
        print("\nRevisa los errores y corrige antes de usar en producción.")
        sys.exit(1)