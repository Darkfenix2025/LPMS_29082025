#!/usr/bin/env python3
"""
Demo simplificada del sistema de generación de acuerdos con IA
Sin caracteres Unicode para compatibilidad con Windows
"""

import os
import sys

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_sistema_ia():
    """Demo simplificada del sistema de IA"""
    print("=" * 80)
    print("DEMO SIMPLIFICADA: SISTEMA DE GENERACION DE ACUERDOS CON IA")
    print("=" * 80)

    try:
        # 1. Importar componentes
        print("\n1. IMPORTANDO COMPONENTES...")
        from ai_agreement_generator import AIAgreementGenerator
        from agent_core import AgentCore
        print("   Componentes importados correctamente")

        # 2. Inicializar sistema
        print("\n2. INICIALIZANDO SISTEMA...")
        generator = AIAgreementGenerator()
        agent = AgentCore()
        print("   Sistema inicializado correctamente")

        # 3. Verificar herramientas
        print("\n3. VERIFICANDO HERRAMIENTAS...")
        tool_names = [tool.name for tool in agent.tools]
        print(f"   Herramientas disponibles: {len(tool_names)}")
        for tool in tool_names:
            print(f"     - {tool}")

        if 'generar_acuerdo_ia_tool' in tool_names:
            print("   Herramienta de IA encontrada!")
        else:
            print("   ERROR: Herramienta de IA no encontrada")
            return False

        # 4. Mostrar capacidades
        print("\n4. CAPACIDADES DEL SISTEMA:")
        print("   - Analisis inteligente de documentos")
        print("   - Generacion de contenido con IA")
        print("   - Integracion con base de datos")
        print("   - Creacion de documentos Word profesionales")
        print("   - Validacion automatica de datos")

        # 5. Simular caso real
        print("\n5. EJEMPLO DE CASO REAL:")
        print("   Caso: MARIA GONZALEZ c/ EMPRESA S.A. s/ DESPIDO")
        print("   Monto: $350,000")
        print("   Plazo: 60 dias")
        print("   Banco: Banco de la Nacion Argentina")

        # 6. Mostrar uso practico
        print("\n6. COMO USAR EL SISTEMA:")

        print("\n   FORMA 1: Desde codigo Python")
        print("   from ai_agreement_generator import AIAgreementGenerator")
        print("   generator = AIAgreementGenerator()")
        print("   result = generator.generate_agreement_with_ai(case_id=123, ...)")
        print("   # Resultado: Documento Word generado automaticamente")

        print("\n   FORMA 2: A traves del agente inteligente")
        print("   Usuario: 'Genera acuerdo para caso 123 con monto 350000'")
        print("   Agente: Identifica herramienta -> Extrae datos -> Genera documento")
        print("   Resultado: Acuerdo profesional listo para usar")

        # 7. Analizar plantilla
        print("\n7. ANALISIS DE PLANTILLA...")
        template_path = "plantillas/mediacion/acuerdo_base.docx"
        if os.path.exists(template_path):
            analysis = generator.analyze_document_for_patterns(template_path)
            if 'error' not in analysis:
                metadata = analysis['structure']['metadata']
                print(f"   Plantilla analizada: {metadata['total_paragraphs']} parrafos")
                print(f"   Placeholders encontrados: {metadata['placeholders_found']}")
                print("   Analisis completado exitosamente")
            else:
                print(f"   Error en analisis: {analysis['error']}")
        else:
            print(f"   Plantilla no encontrada: {template_path}")

        # 8. Mostrar flujo de trabajo
        print("\n8. FLUJO DE TRABAJO:")
        print("   1. Usuario solicita generacion de acuerdo")
        print("   2. Agente identifica herramienta apropiada")
        print("   3. Herramienta valida datos de entrada")
        print("   4. Sistema extrae datos del caso de BD")
        print("   5. IA genera contenido personalizado")
        print("   6. Se crea documento Word profesional")
        print("   7. Documento se guarda y queda listo para usar")

        # 9. Beneficios
        print("\n9. BENEFICIOS:")
        print("   - RAPIDEZ: Genera acuerdos en segundos")
        print("   - PRECISION: Datos automaticos de BD")
        print("   - INTELIGENCIA: Aprende de ejemplos")
        print("   - PROFESIONAL: Formato legal correcto")
        print("   - ESCALABLE: Maneja multiples partes")

        print("\n" + "=" * 80)
        print("DEMO COMPLETADA EXITOSAMENTE")
        print("El sistema esta listo para generar acuerdos con IA")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"ERROR EN DEMO: {e}")
        import traceback
        traceback.print_exc()
        return False

def ejemplos_uso():
    """Muestra ejemplos de uso"""
    print("\nEJEMPLOS DE USO PRACTICO:")
    print("=" * 50)

    ejemplos = [
        "Genera acuerdo para caso 456, monto 200000, plazo 30 dias",
        "Necesito acuerdo de mediacion para expediente EXP-2024-001",
        "Crea documento de acuerdo usando el ejemplo.docx como base",
        "Genera acuerdo laboral para caso 789 con indemnizacion de 500000"
    ]

    for i, ejemplo in enumerate(ejemplos, 1):
        print(f"\n{i}. Usuario dice: '{ejemplo}'")
        print("   Sistema responde: 'Procesando... Generando acuerdo...'")
        print("   Resultado: Documento Word creado en generated_documents/")

if __name__ == "__main__":
    success = demo_sistema_ia()
    if success:
        ejemplos_uso()

    print("\n" + "=" * 80)
    print("PROXIMOS PASOS:")
    print("1. Asegurate de que Ollama este ejecutandose")
    print("2. Verifica que tengas casos en la base de datos")
    print("3. Ejecuta main_app.py y prueba el agente")
    print("4. Usa consultas como las mostradas arriba")
    print("=" * 80)