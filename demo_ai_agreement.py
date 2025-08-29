#!/usr/bin/env python3
"""
Demo completa del sistema de generación de acuerdos con IA
Muestra cómo usar el sistema completo paso a paso
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_ai_agreement_system():
    """Demo completo del sistema de acuerdos con IA"""
    print("=" * 80)
    print("DEMO COMPLETA: SISTEMA DE GENERACIÓN DE ACUERDOS CON IA")
    print("=" * 80)

    try:
        # 1. Importar componentes del sistema
        print("\n1. IMPORTANDO COMPONENTES DEL SISTEMA...")
        from ai_agreement_generator import AIAgreementGenerator
        from agent_core import AgentCore
        from agent_tools import generar_acuerdo_ia_tool

        print("   ✅ Componentes importados correctamente")

        # 2. Inicializar generador básico
        print("\n2. INICIALIZANDO GENERADOR DE ACUERDOS...")
        generator = AIAgreementGenerator()
        print("   ✅ Generador de IA inicializado")

        # 3. Verificar herramientas disponibles
        print("\n3. VERIFICANDO HERRAMIENTAS DISPONIBLES...")
        agent = AgentCore()
        tool_names = [tool.name for tool in agent.tools]
        print(f"   Herramientas disponibles: {tool_names}")

        if 'generar_acuerdo_ia_tool' in tool_names:
            print("   ✅ Herramienta de IA encontrada en el sistema")
        else:
            print("   ❌ Herramienta de IA no encontrada")
            return False

        # 4. Mostrar capacidades del sistema
        print("\n4. CAPACIDADES DEL SISTEMA:")
        print("   📄 Análisis de documentos de ejemplo")
        print("   🤖 Generación de contenido con IA")
        print("   💾 Integración con base de datos de casos")
        print("   📝 Creación de documentos Word profesionales")
        print("   🔍 Validación automática de datos")

        # 5. Simular un caso real
        print("\n5. SIMULANDO UN CASO REAL...")

        # Datos de ejemplo de un caso típico
        case_data = {
            'id': 123,
            'caratula': 'MARIA GONZALEZ c/ EMPRESA CONSTRUCCIONES S.A. s/ DESPIDO',
            'numero_expediente': 'EXP-2024-001',
            'juzgado': 'Juzgado del Trabajo N° 1',
            'jurisdiccion': 'Ciudad Autónoma de Buenos Aires',
            'estado': 'En mediación'
        }

        agreement_details = {
            'monto_compensacion_numeros': '350000',
            'plazo_pago_dias': '60',
            'banco_actor': 'Banco de la Nación Argentina',
            'cbu_actor': '0720000788000001234567',
            'alias_actor': 'gonzalez.maria',
            'cuit_actor': '27-12345678-1'
        }

        print("   Caso simulado:")
        print(f"     📋 Carátula: {case_data['caratula']}")
        print(f"     🏛️  Juzgado: {case_data['juzgado']}")
        print(f"     💰 Monto: ${agreement_details['monto_compensacion_numeros']}")
        print(f"     📅 Plazo: {agreement_details['plazo_pago_dias']} días")
        print(f"     🏦 Banco: {agreement_details['banco_actor']}")

        # 6. Mostrar cómo se usaría en la práctica
        print("\n6. EJEMPLOS DE USO EN LA PRÁCTICA:")

        print("\n   📝 EJEMPLO 1: Uso directo desde código Python")
        print("   ```python")
        print("   from ai_agreement_generator import AIAgreementGenerator")
        print("   ")
        print("   generator = AIAgreementGenerator()")
        print("   result = generator.generate_agreement_with_ai(")
        print("       case_id=123,")
        print("       agreement_details={")
        print("           'monto_compensacion_numeros': '350000',")
        print("           'plazo_pago_dias': '60',")
        print("           'banco_actor': 'Banco Nación',")
        print("           'cbu_actor': '0720000788000001234567',")
        print("           'alias_actor': 'gonzalez.maria',")
        print("           'cuit_actor': '27-12345678-1'")
        print("       }")
        print("   )")
        print("   ```")

        print("\n   🤖 EJEMPLO 2: Uso a través del agente inteligente")
        print("   Usuario dice:")
        print("   \"Genera un acuerdo de mediación para el caso 123 con monto 350000 y plazo 60 días\"")
        print("   ")
        print("   El agente automáticamente:")
        print("   - Identifica que necesita generar_acuerdo_ia_tool")
        print("   - Extrae los parámetros de la consulta")
        print("   - Ejecuta la herramienta con los datos correctos")
        print("   - Devuelve el resultado al usuario")

        # 7. Mostrar análisis de documento de ejemplo
        print("\n7. ANÁLISIS DE DOCUMENTO DE EJEMPLO...")

        template_path = "plantillas/mediacion/acuerdo_base.docx"
        if os.path.exists(template_path):
            print(f"   Analizando plantilla: {template_path}")
            analysis = generator.analyze_document_for_patterns(template_path)

            if 'error' not in analysis:
                print("   ✅ Análisis completado:")
                print(f"      📊 Párrafos encontrados: {analysis['structure']['metadata']['total_paragraphs']}")
                print(f"      🏷️  Placeholders encontrados: {len(analysis.get('placeholders', []))}")
                print(f"      💡 Recomendaciones: {len(analysis.get('recommendations', []))}")

                if analysis.get('recommendations'):
                    print("      Sugerencias de mejora:")
                    for i, rec in enumerate(analysis['recommendations'][:3], 1):
                        print(f"         {i}. {rec}")
            else:
                print(f"   ❌ Error en análisis: {analysis['error']}")
        else:
            print(f"   ⚠️  Plantilla no encontrada: {template_path}")

        # 8. Mostrar flujo completo
        print("\n8. FLUJO COMPLETO DEL SISTEMA:")
        print("   ┌─────────────────┐")
        print("   │   USUARIO       │")
        print("   │   solicita      │")
        print("   │   acuerdo       │")
        print("   └─────────┬───────┘")
        print("             │")
        print("   ┌─────────▼────────┐")
        print("   │   AGENTE         │")
        print("   │   identifica     │")
        print("   │   herramienta    │")
        print("   └─────────┬────────┘")
        print("             │")
        print("   ┌─────────▼────────┐")
        print("   │ HERRAMIENTA IA   │")
        print("   │ valida datos     │")
        print("   └─────────┬────────┘")
        print("             │")
        print("   ┌─────────▼────────┐")
        print("   │ BASE DE DATOS    │")
        print("   │ extrae info      │")
        print("   │ del caso         │")
        print("   └─────────┬────────┘")
        print("             │")
        print("   ┌─────────▼────────┐")
        print("   │   IA OLLAMA      │")
        print("   │ genera contenido │")
        print("   └─────────┬────────┘")
        print("             │")
        print("   ┌─────────▼────────┐")
        print("   │ DOCUMENTO WORD   │")
        print("   │ se crea y guarda │")
        print("   └──────────────────┘")

        # 9. Mostrar beneficios
        print("\n9. BENEFICIOS DEL SISTEMA:")
        print("   ⚡ RAPIDEZ: Genera acuerdos en segundos")
        print("   🎯 PRECISIÓN: Datos extraídos automáticamente de la BD")
        print("   🧠 INTELIGENCIA: Aprende de documentos de ejemplo")
        print("   📋 PROFESIONAL: Formato legal argentino correcto")
        print("   🔄 ESCALABLE: Maneja múltiples partes y representantes")
        print("   🤝 INTEGRADO: Funciona con tu sistema LPMS existente")

        print("\n" + "=" * 80)
        print("✅ DEMO COMPLETADA EXITOSAMENTE")
        print("El sistema de generación de acuerdos con IA está listo para usar")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"❌ ERROR EN DEMO: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_examples():
    """Muestra ejemplos prácticos de uso"""
    print("\n" + "=" * 60)
    print("EJEMPLOS PRÁCTICOS DE USO")
    print("=" * 60)

    examples = [
        {
            'titulo': 'Caso Simple - Un actor, un demandado',
            'consulta': 'Genera un acuerdo de mediación para el caso 456 con monto 200000 y plazo 30 días',
            'resultado': 'Documento generado automáticamente con datos del caso'
        },
        {
            'titulo': 'Caso Complejo - Múltiples partes',
            'consulta': 'Necesito un acuerdo para el caso 789 donde hay 2 actores y 3 demandados, monto total 500000, plazo 90 días',
            'resultado': 'Sistema maneja automáticamente todas las partes y representantes'
        },
        {
            'titulo': 'Con documento de ejemplo',
            'consulta': 'Genera un acuerdo similar al documento ejemplo.docx para el caso 101',
            'resultado': 'IA analiza el documento de ejemplo y adapta el estilo'
        },
        {
            'titulo': 'Caso laboral específico',
            'consulta': 'Acuerdo de despido para el caso 202, indemnización 300000, Banco Provincia, CBU 1234567890123456789012',
            'resultado': 'Documento especializado en derecho laboral'
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['titulo']}")
        print(f"   👤 Usuario: \"{example['consulta']}\"")
        print(f"   🤖 Sistema: {example['resultado']}")

if __name__ == "__main__":
    success = demo_ai_agreement_system()
    if success:
        show_usage_examples()

    print("\n" + "=" * 80)
    print("¿Quieres probar el sistema con datos reales?")
    print("Ejecuta: python main_app.py y usa el agente con consultas de acuerdos")
    print("=" * 80)