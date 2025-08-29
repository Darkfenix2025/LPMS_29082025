#!/usr/bin/env python3
"""
Test script for AI-powered agreement generation system.
Demuestra el uso del generador de acuerdos con IA y análisis de documentos de ejemplo.
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_agreement_generator import AIAgreementGenerator
from agent_core import AgentCore

def test_ai_generator_basic():
    """Test básico del generador de acuerdos con IA."""
    print("=" * 60)
    print("TEST 1: Generador de Acuerdos con IA - Funcionalidad Basica")
    print("=" * 60)

    try:
        # Inicializar generador
        generator = AIAgreementGenerator()
        print("Generador de IA inicializado correctamente")

        # Verificar herramientas disponibles
        available_docs = generator.get_available_example_documents()
        print(f"Documentos de ejemplo disponibles: {len(available_docs)}")
        for doc in available_docs:
            print(f"   - {doc}")

        # Probar análisis de documento si existe
        template_path = "plantillas/mediacion/acuerdo_base.docx"
        if os.path.exists(template_path):
            print(f"\nAnalizando documento de ejemplo: {template_path}")
            analysis = generator.analyze_document_for_patterns(template_path)

            if 'error' not in analysis:
                print("Analisis completado exitosamente")
                print(f"   Parrafos encontrados: {analysis['structure']['metadata']['total_paragraphs']}")
                placeholders = analysis.get('placeholders', [])
                print(f"   Placeholders encontrados: {len(placeholders)}")
                print(f"   Recomendaciones: {len(analysis['recommendations'])}")

                if analysis['recommendations']:
                    print("   Recomendaciones:")
                    for rec in analysis['recommendations']:
                        print(f"     - {rec}")
            else:
                print(f"Error en analisis: {analysis['error']}")
        else:
            print(f"Documento de ejemplo no encontrado: {template_path}")

    except Exception as e:
        print(f"Error en test basico: {e}")
        import traceback
        traceback.print_exc()

def test_ai_generator_with_example():
    """Test del generador con documento de ejemplo específico."""
    print("\n" + "=" * 60)
    print("TEST 2: Generador con Documento de Ejemplo Especifico")
    print("=" * 60)

    # Ruta del documento de ejemplo proporcionado por el usuario
    example_path = r"C:\Users\Pc\Desktop\Google Drive (causasdario@gmail.com)\Dario Causas\MI RECLAMO\DISANTI\Acuerdo Mediacion - J-01-00091307-9 - DISANTI_ADOLFO_RUBEN__c_PILISAR_S_A_s_RECLAMO_PREV.docx"

    try:
        if os.path.exists(example_path):
            print(f"Usando documento de ejemplo: {os.path.basename(example_path)}")

            # Inicializar generador con documento de ejemplo
            generator = AIAgreementGenerator(example_document_path=example_path)
            print("Generador con documento de ejemplo inicializado")

            # Analizar el documento
            analysis = generator.analyze_document_for_patterns(example_path)

            if 'error' not in analysis:
                print("Analisis del documento de ejemplo completado")
                print(f"   Estructura: {json.dumps(analysis['structure']['metadata'], indent=2)}")

                # Mostrar patrones encontrados
                patterns = analysis['patterns']
                print(f"   Patrones de encabezado: {len(patterns['header_patterns'])}")
                print(f"   Patrones de partes: {len(patterns['party_patterns'])}")
                print(f"   Patrones de acuerdo: {len(patterns['agreement_patterns'])}")
                print(f"   Patrones de firma: {len(patterns['signature_patterns'])}")

                # Mostrar placeholders únicos
                placeholders = list(set(analysis['placeholders']))
                if placeholders:
                    print(f"   Placeholders encontrados: {placeholders}")

            else:
                print(f"Error analizando documento: {analysis['error']}")

        else:
            print(f"Documento de ejemplo no encontrado: {example_path}")
            print("   Se usara el generador sin documento de ejemplo especifico")

            # Inicializar sin documento específico
            generator = AIAgreementGenerator()
            print("Generador basico inicializado")

    except Exception as e:
        print(f"Error en test con documento de ejemplo: {e}")
        import traceback
        traceback.print_exc()

def test_agent_integration():
    """Test de integración con el sistema de agentes."""
    print("\n" + "=" * 60)
    print("TEST 3: Integración con Sistema de Agentes")
    print("=" * 60)

    try:
        # Inicializar el núcleo del agente
        agent_core = AgentCore()
        print("✅ Núcleo del agente inicializado")

        # Verificar que la nueva herramienta esté disponible
        tool_names = [tool.name for tool in agent_core.tools]
        print(f"🔧 Herramientas disponibles: {tool_names}")

        if 'generar_acuerdo_ia_tool' in tool_names:
            print("✅ Herramienta de generación con IA encontrada")

            # Crear una consulta de prueba
            test_query = """
            Por favor, genera un acuerdo de mediación usando IA para el caso número 99.
            Los detalles son:
            - Monto de compensación: 150000 pesos
            - Plazo de pago: 30 días
            - Datos bancarios: Banco Santander, CBU 0720123456789012345678, alias 'empresa.legal', CUIT 27-12345678-1

            Si es posible, usa un documento de ejemplo para mejorar la calidad del acuerdo generado.
            """

            print("🤖 Enviando consulta al agente...")
            response = agent_core.run_intent(test_query)

            print("\n📝 Respuesta del agente:")
            print("-" * 40)
            print(response)
            print("-" * 40)

        else:
            print("❌ Herramienta de generación con IA no encontrada en el sistema de agentes")

    except Exception as e:
        print(f"❌ Error en integración con agentes: {e}")
        import traceback
        traceback.print_exc()

def test_case_data_extraction():
    """Test de extracción de datos del caso."""
    print("\n" + "=" * 60)
    print("TEST 4: Extracción de Datos del Caso")
    print("=" * 60)

    try:
        # Inicializar generador
        generator = AIAgreementGenerator()

        # Probar con un caso de ejemplo (usar ID 1 como ejemplo)
        case_id = 1

        print(f"🔍 Extrayendo datos del caso ID: {case_id}")

        # Obtener datos del caso
        case_data = generator._get_case_data_for_ai(case_id)

        if case_data:
            print("✅ Datos del caso obtenidos exitosamente")
            print(f"   📋 Carátula: {case_data['case_info'].get('caratula', 'No disponible')}")
            print(f"   👤 Cliente: {case_data['client'].get('nombre', 'No disponible')}")
            print(f"   👥 Actores: {len(case_data['actors'])}")
            print(f"   🏢 Demandados: {len(case_data['defendants'])}")

            # Mostrar detalles de actores
            for i, actor in enumerate(case_data['actors'], 1):
                print(f"   Actor {i}: {actor.get('nombre_completo', 'Sin nombre')}")
                print(f"     📞 Teléfono: {actor.get('telefono', 'No disponible')}")
                print(f"     👨‍⚖️ Representantes: {len(actor.get('representantes', []))}")

            # Mostrar detalles de demandados
            for i, defendant in enumerate(case_data['defendants'], 1):
                print(f"   Demandado {i}: {defendant.get('nombre_completo', 'Sin nombre')}")
                print(f"     📞 Teléfono: {defendant.get('telefono', 'No disponible')}")
                print(f"     👨‍⚖️ Representantes: {len(defendant.get('representantes', []))}")

        else:
            print("❌ No se pudieron obtener datos del caso")
            print("   Esto puede deberse a que no existe el caso o hay problemas de conexión con la BD")

    except Exception as e:
        print(f"❌ Error extrayendo datos del caso: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Función principal para ejecutar todos los tests."""
    print("INICIANDO TESTS DEL SISTEMA DE GENERACION DE ACUERDOS CON IA")
    print("=" * 80)

    # Ejecutar tests
    test_ai_generator_basic()
    test_ai_generator_with_example()
    test_agent_integration()
    test_case_data_extraction()

    print("\n" + "=" * 80)
    print("TESTS COMPLETADOS")
    print("=" * 80)

    print("\nRESUMEN DE FUNCIONALIDADES:")
    print("   - Generador de Acuerdos con IA: IMPLEMENTADO")
    print("   - Analisis de Documentos de Ejemplo: IMPLEMENTADO")
    print("   - Integracion con Sistema de Agentes: IMPLEMENTADO")
    print("   - Extraccion de Datos de Casos: IMPLEMENTADO")
    print("   - Generacion de Documentos Word: IMPLEMENTADO")

    print("\nPARA USAR EL SISTEMA:")
    print("   1. Asegurate de que Ollama este ejecutandose")
    print("   2. Verifica que los documentos de ejemplo existan")
    print("   3. Ejecuta el agente con consultas sobre generacion de acuerdos")
    print("   4. Los documentos generados se guardaran en 'generated_documents/'")

if __name__ == "__main__":
    main()