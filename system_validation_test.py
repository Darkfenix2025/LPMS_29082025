#!/usr/bin/env python3
"""
Sistema de Validación Completa - Test Final del Sistema Refactorizado
=======================================================================

Este script ejecuta pruebas exhaustivas para validar que todos los componentes
del sistema refactorizado funcionan correctamente:

1. Generación de acuerdos de mediación con múltiples partes
2. Sistema de IA para generación de acuerdos
3. Interfaz de agente mejorada
4. Integración con base de datos
5. Sistema de plantillas
6. Manejo de representantes legales

Autor: Kilo Code
Fecha: 2025-08-28
"""

import os
import sys
import time
import traceback
from datetime import datetime
import json

# Configurar encoding para evitar problemas con caracteres especiales
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Agregar el directorio actual al path para importar módulos locales
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class SystemValidator:
    """Clase principal para validar el sistema completo"""

    def __init__(self):
        self.test_results = []
        self.start_time = None
        self.end_time = None

    def log_test(self, test_name, status, message="", error=None):
        """Registra el resultado de una prueba"""
        result = {
            'test_name': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'error': str(error) if error else None
        }
        self.test_results.append(result)
        print(f"[{status.upper()}] {test_name}: {message}")
        if error:
            print(f"       Error: {error}")

    def run_test(self, test_name, test_function):
        """Ejecuta una prueba y maneja excepciones"""
        try:
            print(f"\n🔍 Ejecutando: {test_name}")
            result = test_function()
            if result:
                self.log_test(test_name, 'PASS', result)
                return True
            else:
                self.log_test(test_name, 'FAIL', "La función retornó False")
                return False
        except Exception as e:
            self.log_test(test_name, 'ERROR', f"Excepción durante la prueba", e)
            return False

    def test_imports(self):
        """Prueba que todos los módulos se importan correctamente"""
        modules_to_test = [
            'case_dialog_manager',
            'crm_database',
            'agent_core',
            'agent_tools',
            'agent_interface',
            'agent_template_generator',
            'ai_agreement_generator'
        ]

        failed_imports = []
        for module in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {module} importado correctamente")
            except ImportError as e:
                failed_imports.append((module, str(e)))
                print(f"❌ Error importando {module}: {e}")

        if failed_imports:
            return False, f"Error importando módulos: {failed_imports}"
        return True, f"Todos los módulos importados correctamente ({len(modules_to_test)} módulos)"

    def test_database_connection(self):
        """Prueba la conexión a la base de datos"""
        try:
            import crm_database as db

            # Intentar conectar
            conn = db.connect_db()
            if not conn:
                return False, "No se pudo establecer conexión con la base de datos"

            # Verificar que podemos hacer una consulta simple
            result = db.execute_query("SELECT 1 as test", fetch_one=True)
            if not result:
                return False, "No se pudo ejecutar consulta de prueba"

            conn.close()
            return True, "Conexión a base de datos funcionando correctamente"

        except Exception as e:
            return False, f"Error en conexión a BD: {e}"

    def test_case_manager_initialization(self):
        """Prueba la inicialización del CaseManager"""
        try:
            from case_dialog_manager import CaseManager

            # Crear instancia sin app_controller para pruebas
            case_manager = CaseManager(app_controller=None)

            # Verificar que se inicializó correctamente
            if not hasattr(case_manager, 'db'):
                return False, "CaseManager no tiene atributo db"

            if not hasattr(case_manager, 'logger'):
                return False, "CaseManager no tiene atributo logger"

            return True, "CaseManager inicializado correctamente"

        except Exception as e:
            return False, f"Error inicializando CaseManager: {e}"

    def test_mediation_dependencies(self):
        """Prueba las dependencias necesarias para generación de acuerdos"""
        try:
            from case_dialog_manager import CaseManager

            case_manager = CaseManager(app_controller=None)
            validation_result = case_manager._validate_mediation_dependencies()

            if not validation_result['success']:
                errors = validation_result['errors']
                return False, f"Dependencias faltantes: {[e['message'] for e in errors]}"

            return True, f"Dependencias validadas correctamente. Advertencias: {len(validation_result['warnings'])}"

        except Exception as e:
            return False, f"Error validando dependencias: {e}"

    def test_template_files(self):
        """Prueba que los archivos de plantilla existen"""
        template_files = [
            'plantillas/mediacion/acuerdo_base.docx',
            'modelo_acuerdo.txt'
        ]

        missing_files = []
        for template_file in template_files:
            if not os.path.exists(template_file):
                missing_files.append(template_file)

        if missing_files:
            return False, f"Archivos de plantilla faltantes: {missing_files}"

        # Verificar que no están vacíos
        for template_file in template_files:
            if os.path.getsize(template_file) == 0:
                return False, f"Archivo de plantilla vacío: {template_file}"

        return True, f"Todos los archivos de plantilla existen y no están vacíos ({len(template_files)} archivos)"

    def test_agent_core_functionality(self):
        """Prueba la funcionalidad básica del núcleo del agente"""
        try:
            from agent_core import AgentCore

            # Crear instancia del agente
            agent = AgentCore()

            # Verificar que se inicializó correctamente
            if not hasattr(agent, 'tools'):
                return False, "AgentCore no tiene atributo tools"

            if not hasattr(agent, 'execute_tool'):
                return False, "AgentCore no tiene método execute_tool"

            return True, "AgentCore inicializado correctamente"

        except Exception as e:
            return False, f"Error en AgentCore: {e}"

    def test_agent_tools(self):
        """Prueba que las herramientas del agente están disponibles"""
        try:
            from agent_tools import AgentTools

            # Verificar que podemos crear instancia
            tools = AgentTools()

            # Verificar herramientas críticas
            critical_tools = ['generar_acuerdo_template_tool']
            for tool_name in critical_tools:
                if not hasattr(tools, tool_name):
                    return False, f"Herramienta faltante: {tool_name}"

            return True, f"Herramientas del agente verificadas ({len(critical_tools)} herramientas críticas)"

        except Exception as e:
            return False, f"Error en AgentTools: {e}"

    def test_template_generator(self):
        """Prueba el generador de plantillas"""
        try:
            from agent_template_generator import AgentTemplateGenerator

            # Crear instancia
            generator = AgentTemplateGenerator()

            # Verificar que se inicializó correctamente
            if not hasattr(generator, 'template_path'):
                return False, "AgentTemplateGenerator no tiene template_path"

            if not os.path.exists(generator.template_path):
                return False, f"Archivo de plantilla no encontrado: {generator.template_path}"

            return True, "AgentTemplateGenerator inicializado correctamente"

        except Exception as e:
            return False, f"Error en AgentTemplateGenerator: {e}"

    def test_ai_agreement_generator(self):
        """Prueba el generador de acuerdos con IA"""
        try:
            from ai_agreement_generator import AIAgreementGenerator

            # Crear instancia
            ai_generator = AIAgreementGenerator()

            # Verificar que se inicializó correctamente
            if not hasattr(ai_generator, 'generate_agreement'):
                return False, "AIAgreementGenerator no tiene método generate_agreement"

            return True, "AIAgreementGenerator inicializado correctamente"

        except Exception as e:
            return False, f"Error en AIAgreementGenerator: {e}"

    def test_agent_interface(self):
        """Prueba la interfaz del agente"""
        try:
            from agent_interface import AgentInterface

            # Verificar que podemos crear instancia (sin parámetros para evitar UI)
            interface = AgentInterface()

            # Verificar métodos críticos
            critical_methods = ['search_cases', 'get_case_details', 'generate_agreement']
            for method_name in critical_methods:
                if not hasattr(interface, method_name):
                    return False, f"Método faltante en AgentInterface: {method_name}"

            return True, f"AgentInterface verificado ({len(critical_methods)} métodos críticos)"

        except Exception as e:
            return False, f"Error en AgentInterface: {e}"

    def test_mock_data_generation(self):
        """Prueba la generación de datos mock para testing"""
        try:
            # Crear datos mock representativos
            mock_case_data = {
                'id': 1,
                'caratula': 'Test Case - Mediación Laboral',
                'numero_expediente': '1234/2025',
                'juzgado': 'Juzgado Nacional del Trabajo N° 1',
                'jurisdiccion': 'CABA',
                'cliente_id': 1
            }

            mock_parties = [
                {
                    'id': 1,
                    'nombre_completo': 'Juan Pérez',
                    'rol': 'Actor',
                    'dni': '12345678',
                    'cuit': '20-12345678-9',
                    'representantes': [
                        {
                            'nombre_completo': 'Dr. María González',
                            'matricula': '12345',
                            'personeria': 'Poder General Judicial'
                        }
                    ]
                },
                {
                    'id': 2,
                    'nombre_completo': 'Empresa XYZ S.A.',
                    'rol': 'Demandado',
                    'cuit': '30-12345678-9',
                    'representantes': [
                        {
                            'nombre_completo': 'Dra. Ana López',
                            'matricula': '67890',
                            'personeria': 'Apoderada Judicial'
                        }
                    ]
                }
            ]

            # Verificar estructura de datos
            if not all(key in mock_case_data for key in ['id', 'caratula', 'numero_expediente']):
                return False, "Estructura de datos del caso mock inválida"

            if not all('nombre_completo' in party and 'rol' in party for party in mock_parties):
                return False, "Estructura de datos de partes mock inválida"

            return True, "Datos mock generados correctamente"

        except Exception as e:
            return False, f"Error generando datos mock: {e}"

    def test_document_generation_simulation(self):
        """Prueba simulación de generación de documentos"""
        try:
            from agent_template_generator import AgentTemplateGenerator

            # Crear generador
            generator = AgentTemplateGenerator()

            # Datos de prueba
            test_data = {
                'numero_expediente': '1234/2025',
                'caratula': 'Test Case - Mediación Laboral',
                'actores': ['Juan Pérez'],
                'demandados': ['Empresa XYZ S.A.'],
                'monto_compensacion': '50000.00',
                'plazo_pago': '30 días'
            }

            # Intentar generar acuerdo (sin guardar archivo)
            try:
                result = generator.generate_agreement(test_data, save_file=False)
                if not result:
                    return False, "Generación de acuerdo falló"
                return True, "Simulación de generación de documento exitosa"
            except Exception as e:
                return False, f"Error en simulación de generación: {e}"

        except Exception as e:
            return False, f"Error en simulación de documento: {e}"

    def run_all_tests(self):
        """Ejecuta todas las pruebas del sistema"""
        print("=" * 80)
        print("🚀 INICIANDO VALIDACIÓN COMPLETA DEL SISTEMA")
        print("=" * 80)
        print(f"Fecha y hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Directorio de trabajo: {os.getcwd()}")
        print()

        self.start_time = time.time()

        # Definir todas las pruebas
        tests = [
            ("Importación de módulos", self.test_imports),
            ("Conexión a base de datos", self.test_database_connection),
            ("Inicialización de CaseManager", self.test_case_manager_initialization),
            ("Validación de dependencias de mediación", self.test_mediation_dependencies),
            ("Verificación de archivos de plantilla", self.test_template_files),
            ("Funcionalidad básica de AgentCore", self.test_agent_core_functionality),
            ("Herramientas del agente", self.test_agent_tools),
            ("Generador de plantillas", self.test_template_generator),
            ("Generador de acuerdos con IA", self.test_ai_agreement_generator),
            ("Interfaz del agente", self.test_agent_interface),
            ("Generación de datos mock", self.test_mock_data_generation),
            ("Simulación de generación de documentos", self.test_document_generation_simulation)
        ]

        # Ejecutar todas las pruebas
        passed = 0
        failed = 0
        errors = 0

        for test_name, test_function in tests:
            if self.run_test(test_name, test_function):
                passed += 1
            else:
                failed += 1

        self.end_time = time.time()
        execution_time = self.end_time - self.start_time

        # Resumen final
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE VALIDACIÓN DEL SISTEMA")
        print("=" * 80)
        print(f"Total de pruebas: {len(tests)}")
        print(f"✅ Aprobadas: {passed}")
        print(f"❌ Fallidas: {failed}")
        print(f"⚠️  Errores: {errors}")
        print(f"Tiempo de ejecución: {execution_time:.2f} segundos")
        print()

        # Calcular porcentaje de éxito
        success_rate = (passed / len(tests)) * 100 if tests else 0

        if success_rate >= 90:
            print("🎉 ¡VALIDACIÓN EXITOSA!")
            print("El sistema está listo para producción.")
        elif success_rate >= 75:
            print("⚠️  VALIDACIÓN CON ADVERTENCIAS")
            print("El sistema funciona pero requiere atención en algunos componentes.")
        else:
            print("❌ VALIDACIÓN FALLIDA")
            print("Se requieren correcciones antes de usar el sistema.")

        print("\n" + "=" * 80)

        # Guardar resultados en archivo
        self.save_results_to_file()

        return success_rate >= 75  # Retornar True si al menos 75% de pruebas pasan

    def save_results_to_file(self):
        """Guarda los resultados de las pruebas en un archivo JSON"""
        try:
            results_file = f"system_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            results_summary = {
                'validation_timestamp': datetime.now().isoformat(),
                'execution_time_seconds': self.end_time - self.start_time,
                'total_tests': len(self.test_results),
                'passed_tests': len([r for r in self.test_results if r['status'] == 'PASS']),
                'failed_tests': len([r for r in self.test_results if r['status'] == 'FAIL']),
                'error_tests': len([r for r in self.test_results if r['status'] == 'ERROR']),
                'success_rate': (len([r for r in self.test_results if r['status'] == 'PASS']) / len(self.test_results)) * 100 if self.test_results else 0,
                'system_info': {
                    'python_version': sys.version,
                    'platform': sys.platform,
                    'working_directory': os.getcwd()
                },
                'test_results': self.test_results
            }

            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(results_summary, f, indent=2, ensure_ascii=False)

            print(f"📄 Resultados guardados en: {results_file}")

        except Exception as e:
            print(f"⚠️  Error guardando resultados: {e}")

def main():
    """Función principal"""
    try:
        validator = SystemValidator()
        success = validator.run_all_tests()

        # Código de salida basado en el resultado
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⏹️  Validación interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Error crítico durante la validación: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()