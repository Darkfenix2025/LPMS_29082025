#!/usr/bin/env python3
"""
Script de prueba para la integración del agente refactorizado con LPMS.
Permite probar la funcionalidad sin ejecutar toda la aplicación.
"""

import sys
import os
import json
from datetime import datetime

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_agent_integration():
    """Prueba completa de la integración del agente con LPMS"""
    print("🧪 INICIANDO PRUEBA DE INTEGRACIÓN AGENTE-LPMS")
    print("=" * 60)

    try:
        # Importar módulos necesarios
        print("📦 Importando módulos...")
        from agent_integration import LPMSAgentIntegration
        import crm_database as db
        print("✅ Módulos importados correctamente")

        # Verificar conexión a base de datos
        print("\n🔌 Verificando conexión a base de datos...")
        conn = db.connect_db()
        if conn:
            print("✅ Conexión a PostgreSQL exitosa")
            conn.close()
        else:
            print("❌ Error de conexión a PostgreSQL")
            return False

        # Inicializar integración
        print("\n🤖 Inicializando integración del agente...")
        integration = LPMSAgentIntegration()
        print("✅ Integración inicializada correctamente")

        # Obtener lista de casos disponibles para prueba
        print("\n📋 Obteniendo casos disponibles...")
        try:
            cases = db.get_all_cases()
            if cases:
                print(f"✅ Encontrados {len(cases)} casos en la base de datos")

                # Mostrar primeros 3 casos como ejemplo
                print("\n📄 Primeros casos disponibles:")
                for i, case in enumerate(cases[:3]):
                    print(f"  {i+1}. ID: {case.get('id')} - {case.get('caratula', 'Sin carátula')[:50]}...")

                # Solicitar ID de caso para prueba
                while True:
                    try:
                        case_id_input = input("\n🔍 Ingrese el ID del caso para probar (o '0' para cancelar): ").strip()
                        if case_id_input == '0':
                            print("❌ Prueba cancelada por el usuario")
                            return False

                        case_id = int(case_id_input)

                        # Verificar que el caso existe
                        case_data = integration.get_case_data_for_agent(case_id)
                        print(f"\n✅ Caso encontrado: {case_data['caratula']}")
                        break

                    except ValueError:
                        print("❌ Por favor ingrese un número válido")
                    except Exception as e:
                        print(f"❌ Error obteniendo caso: {e}")
                        continue

            else:
                print("⚠️ No se encontraron casos en la base de datos")
                print("Creando datos de prueba...")

                # Crear un caso de prueba
                test_case_id = create_test_case()
                if test_case_id:
                    case_id = test_case_id
                    print(f"✅ Caso de prueba creado con ID: {case_id}")
                else:
                    print("❌ Error creando caso de prueba")
                    return False

        except Exception as e:
            print(f"❌ Error obteniendo casos: {e}")
            return False

        # Probar obtención de datos del caso
        print(f"\n📊 Probando obtención de datos del caso {case_id}...")
        try:
            case_data = integration.get_case_data_for_agent(case_id)
            print("✅ Datos del caso obtenidos correctamente")
            print(f"   📋 Carátula: {case_data['caratula']}")
            print(f"   👤 Cliente: {case_data['cliente']['nombre'] if case_data['cliente'] else 'No especificado'}")
            print(f"   📄 Partes: {len(case_data['partes'])} partes involucradas")
            print(f"   📝 Actividades: {len(case_data['actividades'])} actividades registradas")
        except Exception as e:
            print(f"❌ Error obteniendo datos del caso: {e}")
            return False

        # Probar generación de acuerdo
        print(f"\n📄 Probando generación de acuerdo de mediación...")
        agreement_data = {
            "monto_compensacion": "75000.00",
            "plazo_pago_dias": "30",
            "banco_actor": "Banco de la Nación Argentina",
            "cbu_actor": "0110599520000001234567",
            "alias_actor": "empleado.indemnizacion",
            "cuit_actor": "20-12345678-9"
        }

        try:
            result = integration.generate_mediation_agreement(case_id, agreement_data)

            if result["success"]:
                print("✅ Acuerdo generado exitosamente")
                print(f"   📄 Respuesta: {result['response'][:100]}...")

                # Guardar como actividad
                saved = integration.save_agreement_to_case(case_id, result)
                if saved:
                    print("✅ Acuerdo guardado como actividad en el caso")
                else:
                    print("⚠️ Acuerdo generado pero no se pudo guardar como actividad")

            else:
                print(f"❌ Error generando acuerdo: {result.get('error', 'Error desconocido')}")

        except Exception as e:
            print(f"❌ Error en generación de acuerdo: {e}")
            return False

        # Cerrar integración
        print("\n🔚 Cerrando integración...")
        integration.close()
        print("✅ Integración cerrada correctamente")

        print("\n" + "=" * 60)
        print("🎉 PRUEBA DE INTEGRACIÓN COMPLETADA EXITOSAMENTE")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO EN PRUEBA: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_test_case():
    """Crea un caso de prueba para testing"""
    try:
        import crm_database as db

        # Crear cliente de prueba
        client_id = db.add_client(
            nombre="Cliente de Prueba IA",
            direccion="Dirección de Prueba 123",
            email="prueba@cliente.com",
            whatsapp="1234567890",
            telefono="1234567890"
        )

        if not client_id:
            print("❌ Error creando cliente de prueba")
            return None

        # Crear caso de prueba
        case_id = db.add_case(
            cliente_id=client_id,
            caratula="Caso de Prueba - Integración Agente IA",
            descripcion="Caso creado para probar la integración del agente refactorizado con LPMS",
            estado="Activo"
        )

        if case_id:
            print(f"✅ Caso de prueba creado: ID {case_id}")
            return case_id
        else:
            print("❌ Error creando caso de prueba")
            return None

    except Exception as e:
        print(f"❌ Error creando caso de prueba: {e}")
        return None


def show_menu():
    """Muestra menú de opciones de prueba"""
    print("\n🔧 MENÚ DE PRUEBA - INTEGRACIÓN AGENTE LPMS")
    print("=" * 50)
    print("1. Ejecutar prueba completa de integración")
    print("2. Probar solo conexión a base de datos")
    print("3. Probar solo inicialización del agente")
    print("4. Crear caso de prueba")
    print("5. Salir")
    print("=" * 50)

    while True:
        try:
            option = input("Seleccione una opción (1-5): ").strip()

            if option == "1":
                success = test_agent_integration()
                print(f"\nResultado: {'✅ EXITOSO' if success else '❌ FALLIDO'}")
                break
            elif option == "2":
                test_database_connection()
                break
            elif option == "3":
                test_agent_initialization()
                break
            elif option == "4":
                case_id = create_test_case()
                if case_id:
                    print(f"✅ Caso de prueba creado con ID: {case_id}")
                else:
                    print("❌ Error creando caso de prueba")
                break
            elif option == "5":
                print("👋 Hasta luego!")
                return
            else:
                print("❌ Opción no válida. Intente nuevamente.")

        except KeyboardInterrupt:
            print("\n👋 Prueba interrumpida por el usuario")
            return
        except Exception as e:
            print(f"❌ Error en opción seleccionada: {e}")
            break


def test_database_connection():
    """Prueba solo la conexión a la base de datos"""
    print("\n🔌 Probando conexión a PostgreSQL...")
    try:
        import crm_database as db
        conn = db.connect_db()
        if conn:
            print("✅ Conexión exitosa a PostgreSQL")
            conn.close()
        else:
            print("❌ Error de conexión")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_agent_initialization():
    """Prueba solo la inicialización del agente"""
    print("\n🤖 Probando inicialización del agente...")
    try:
        from agent_core import AgentCore
        agent = AgentCore()
        print("✅ Agente inicializado correctamente")
        # No cerramos el agente aquí para evitar problemas
    except Exception as e:
        print(f"❌ Error inicializando agente: {e}")


if __name__ == "__main__":
    print("🚀 SCRIPT DE PRUEBA - INTEGRACIÓN AGENTE LPMS")
    print("Este script permite probar la integración sin ejecutar la aplicación completa.")

    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Modo automático para CI/CD o testing
        success = test_agent_integration()
        sys.exit(0 if success else 1)
    else:
        # Modo interactivo
        show_menu()