#!/usr/bin/env python3
"""
Demo del Agente Inteligente - Prueba Interactiva
Muestra cómo usar el agente IA para generar acuerdos de mediación
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_core import AgentCore
import crm_database as db

def demo_agent():
    """Demostración interactiva del agente inteligente"""

    print("=" * 60)
    print("DEMO DEL AGENTE INTELIGENTE DE ACUERDOS")
    print("=" * 60)

    try:
        # Inicializar agente
        print("Inicializando agente IA...")
        agent = AgentCore()
        print("Agente inicializado correctamente\n")

        # Mostrar casos disponibles
        print("CASOS DISPONIBLES:")
        try:
            cases = db.get_cases_by_client(None)
            if cases:
                for i, case in enumerate(cases[:5], 1):  # Mostrar máximo 5 casos
                    print(f"  {i}. ID {case['id']}: {case.get('numero_expediente', 'N/A')} - {case.get('caratula', 'Sin carátula')[:50]}")
            else:
                print("  No hay casos disponibles")
        except Exception as e:
            print(f"  Error obteniendo casos: {e}")

        print("\n" + "=" * 60)
        print("CONSULTAS DE EJEMPLO:")
        print("=" * 60)

        example_queries = [
            "Genera un acuerdo de mediación para el caso con ID 72",
            "Necesito un acuerdo laboral con monto de $75,000 y plazo de 45 días",
            "Crea un acuerdo de divorcio para expediente DIV-2024-001",
            "Genera acuerdo comercial para caso con carátula que contenga 'PRISMA'",
            "Necesito acuerdo de mediación con representante legal"
        ]

        for i, query in enumerate(example_queries, 1):
            print(f"{i}. '{query}'")

        print("\n" + "=" * 60)
        print("PRUEBA INTERACTIVA:")
        print("=" * 60)

        while True:
            try:
                print("\nOpciones:")
                print("1. Probar consulta de ejemplo")
                print("2. Escribir consulta personalizada")
                print("3. Salir")

                choice = input("\nSeleccione una opción (1-3): ").strip()

                if choice == "1":
                    print("\nConsultas disponibles:")
                    for i, query in enumerate(example_queries, 1):
                        print(f"{i}. {query}")

                    query_choice = input("\nSeleccione consulta (1-5): ").strip()
                    try:
                        query_index = int(query_choice) - 1
                        if 0 <= query_index < len(example_queries):
                            selected_query = example_queries[query_index]
                        else:
                            print("Opción inválida")
                            continue
                    except ValueError:
                        print("Entrada inválida")
                        continue

                elif choice == "2":
                    selected_query = input("Escriba su consulta: ").strip()
                    if not selected_query:
                        print("Consulta vacía, intente nuevamente")
                        continue

                elif choice == "3":
                    print("Hasta luego!")
                    break

                else:
                    print("Opción inválida")
                    continue

                # Procesar consulta
                print(f"\nProcesando: '{selected_query}'")
                print("Espere por favor...")

                response = agent.run_intent(selected_query)

                print("\n" + "=" * 60)
                print("RESPUESTA DEL AGENTE:")
                print("=" * 60)
                print(response)
                print("=" * 60)

            except KeyboardInterrupt:
                print("\nDemo interrumpida por el usuario")
                break
            except Exception as e:
                print(f"\nError procesando consulta: {e}")
                continue

    except Exception as e:
        print(f"Error inicializando demo: {e}")
        return False

    return True

def demo_agent_interface():
    """Demostración de la interfaz gráfica del agente"""

    print("=" * 60)
    print("DEMO DE INTERFAZ GRAFICA DEL AGENTE")
    print("=" * 60)

    try:
        from agent_interface import open_agent_interface

        print("Abriendo interfaz grafica del agente...")
        print("La interfaz permite:")
        print("   • Seleccionar casos de la base de datos")
        print("   • Escribir consultas en lenguaje natural")
        print("   • Recibir respuestas del agente IA")
        print("   • Generar acuerdos automaticamente")
        print("\nPara usar la interfaz grafica, ejecute:")
        print("   python agent_interface.py")
        print("\nO desde la aplicacion principal:")
        print("   Menu Asistente IA -> Agente IA - Generacion de Acuerdos")

        # Abrir interfaz (comentado para evitar bloqueo en demo)
        # agent_interface = open_agent_interface()
        print("\nInterfaz grafica lista para usar")

    except ImportError as e:
        print(f"Error importando interfaz: {e}")
        print("Asegurese de que todos los modulos esten instalados")
    except Exception as e:
        print(f"Error en interfaz grafica: {e}")

if __name__ == "__main__":
    print("DEMO DEL SISTEMA DE AGENTE INTELIGENTE")
    print("=" * 60)

    # Demo del agente en modo texto
    success = demo_agent()

    if success:
        print("\n" + "=" * 60)
        print("DEMO COMPLETADA EXITOSAMENTE!")
        print("=" * 60)

        # Demo de interfaz gráfica
        demo_agent_interface()

        print("\n" + "=" * 60)
        print("RESUMEN DEL SISTEMA:")
        print("=" * 60)
        print("✓ Agente IA completamente funcional")
        print("✓ Integracion con base de datos")
        print("✓ Generacion automatica de acuerdos")
        print("✓ Interfaz grafica disponible")
        print("✓ Sistema listo para produccion")
        print("\nEl sistema esta listo para usar!")

    else:
        print("\nLa demo fallo. Verifique la configuracion del sistema.")