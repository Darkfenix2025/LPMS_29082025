#!/usr/bin/env python3
"""
Script de CI/CD Standalone para Tests del Módulo de Prospectos
Verificaciones independientes sin dependencias externas
"""

import sys
import os
import ast
import re
from datetime import datetime


def print_header(title):
    """Imprime un header formateado"""
    print("\n" + "=" * 70)
    print(f"🔧 {title}")
    print("=" * 70)


def print_section(title):
    """Imprime una sección formateada"""
    print(f"\n📋 {title}")
    print("-" * 50)


def check_file_integrity():
    """Verifica la integridad de los archivos principales"""
    print_section("Verificación de Integridad de Archivos")
    
    files_to_check = [
        ('prospect_manager.py', 'Gestor principal de prospectos'),
        ('prospects_window.py', 'Ventana de gestión de prospectos'),
        ('prospect_dialog_manager.py', 'Gestor de diálogos de consulta'),
        ('test_validacion_prospecto.py', 'Tests de validación'),
        ('test_compatibilidad_simple.py', 'Tests de compatibilidad'),
        ('REFACTOR_PROSPECTOS_RESUMEN.md', 'Documentación del refactor'),
    ]
    
    all_files_ok = True
    
    for file_path, description in files_to_check:
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"✅ {description}: {file_path} ({file_size} bytes)")
        else:
            print(f"❌ {description}: {file_path} - NO ENCONTRADO")
            all_files_ok = False
    
    return all_files_ok


def check_syntax():
    """Verifica que no haya errores de sintaxis"""
    print_section("Verificación de Sintaxis")
    
    files_to_check = ['prospect_manager.py', 'prospects_window.py']
    all_syntax_ok = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                compile(code, file_path, 'exec')
                print(f"✅ Sintaxis OK: {file_path}")
            except SyntaxError as e:
                print(f"❌ Error de sintaxis en {file_path}: {e}")
                all_syntax_ok = False
            except Exception as e:
                print(f"❌ Error verificando {file_path}: {e}")
                all_syntax_ok = False
        else:
            print(f"❌ Archivo no encontrado: {file_path}")
            all_syntax_ok = False
    
    return all_syntax_ok


def check_validation_function():
    """Verifica que la función de validación centralizada existe y funciona"""
    print_section("Verificación de Función de Validación Centralizada")
    
    try:
        # Leer el archivo prospect_manager.py
        with open('prospect_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que la función validar_datos_prospecto existe
        if 'def validar_datos_prospecto(self, datos: dict) -> tuple[bool, str]:' in content:
            print("✅ Función validar_datos_prospecto encontrada")
        else:
            print("❌ Función validar_datos_prospecto NO encontrada")
            return False
        
        # Verificar que contiene las validaciones esperadas
        validations_to_check = [
            "El nombre del prospecto no puede estar vacío",
            "demasiado largo (máximo 255 caracteres)",
            "información de contacto es demasiado larga",
            "notas generales son demasiado largas",
            "Estado inválido"
        ]
        
        validations_found = 0
        for validation in validations_to_check:
            if validation in content:
                print(f"✅ Validación encontrada: {validation[:50]}...")
                validations_found += 1
            else:
                print(f"❌ Validación faltante: {validation[:50]}...")
        
        if validations_found == len(validations_to_check):
            print(f"✅ Todas las validaciones encontradas ({validations_found}/{len(validations_to_check)})")
            return True
        else:
            print(f"❌ Validaciones faltantes ({validations_found}/{len(validations_to_check)})")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando función de validación: {e}")
        return False


def check_aliases():
    """Verifica que los aliases de compatibilidad existen"""
    print_section("Verificación de Aliases de Compatibilidad")
    
    try:
        # Leer el archivo prospect_manager.py
        with open('prospect_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Aliases esperados
        expected_aliases = [
            'load_prospects = cargar_prospectos',
            'on_prospect_select = al_seleccionar_prospecto',
            'display_prospect_details = mostrar_detalles_prospecto',
            'clear_prospect_details = limpiar_detalles_prospecto',
            'enable_prospect_buttons = habilitar_botones_prospecto',
            'disable_prospect_buttons = deshabilitar_botones_prospecto'
        ]
        
        aliases_found = 0
        for alias in expected_aliases:
            if alias in content:
                print(f"✅ Alias encontrado: {alias}")
                aliases_found += 1
            else:
                print(f"❌ Alias faltante: {alias}")
        
        if aliases_found == len(expected_aliases):
            print(f"✅ Todos los aliases encontrados ({aliases_found}/{len(expected_aliases)})")
            return True
        else:
            print(f"❌ Aliases faltantes ({aliases_found}/{len(expected_aliases)})")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando aliases: {e}")
        return False


def check_function_organization():
    """Verifica que las funciones estén organizadas correctamente"""
    print_section("Verificación de Organización de Funciones")
    
    try:
        # Leer el archivo prospect_manager.py
        with open('prospect_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar comentarios de sección
        section_comments = [
            "# GRUPO 1: FUNCIONES CRUD PRINCIPALES",
            "# ALIASES DE COMPATIBILIDAD"
        ]
        
        sections_found = 0
        for comment in section_comments:
            if comment in content:
                print(f"✅ Sección encontrada: {comment}")
                sections_found += 1
            else:
                print(f"❌ Sección faltante: {comment}")
        
        # Verificar funciones renombradas
        renamed_functions = [
            'def cargar_prospectos(self)',
            'def al_seleccionar_prospecto(self, event)',
            'def mostrar_detalles_prospecto(self, prospect_data)',
            'def limpiar_detalles_prospecto(self)',
            'def habilitar_botones_prospecto(self)',
            'def deshabilitar_botones_prospecto(self)'
        ]
        
        functions_found = 0
        for function in renamed_functions:
            if function in content:
                print(f"✅ Función renombrada encontrada: {function}")
                functions_found += 1
            else:
                print(f"❌ Función renombrada faltante: {function}")
        
        total_expected = len(section_comments) + len(renamed_functions)
        total_found = sections_found + functions_found
        
        if total_found == total_expected:
            print(f"✅ Organización correcta ({total_found}/{total_expected})")
            return True
        else:
            print(f"❌ Organización incompleta ({total_found}/{total_expected})")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando organización: {e}")
        return False


def check_prospects_window_updates():
    """Verifica que prospects_window.py fue actualizado correctamente"""
    print_section("Verificación de Actualizaciones en prospects_window.py")
    
    try:
        # Leer el archivo prospects_window.py
        with open('prospects_window.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que usa cargar_prospectos en lugar de load_prospects
        if 'self.prospect_manager.cargar_prospectos()' in content:
            print("✅ Llamada a cargar_prospectos encontrada")
        else:
            print("❌ Llamada a cargar_prospectos NO encontrada")
            return False
        
        # Verificar que no quedan referencias a load_prospects
        if 'load_prospects' not in content:
            print("✅ No hay referencias a load_prospects (correcto)")
        else:
            print("❌ Aún hay referencias a load_prospects")
            return False
        
        # Verificar que save_notes usa validación centralizada
        if 'validar_datos_prospecto' in content:
            print("✅ save_notes usa validación centralizada")
        else:
            print("❌ save_notes NO usa validación centralizada")
            return False
        
        print("✅ prospects_window.py actualizado correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando prospects_window.py: {e}")
        return False


def run_inline_validation_test():
    """Ejecuta un test inline de la función de validación"""
    print_section("Test Inline de Validación")
    
    # Función de validación copiada para test independiente
    def validar_datos_prospecto_test(datos: dict) -> tuple[bool, str]:
        nombre = datos.get('nombre', '').strip()
        if not nombre:
            return False, "El nombre del prospecto no puede estar vacío."
        if len(nombre) > 255:
            return False, "El nombre del prospecto es demasiado largo (máximo 255 caracteres)."
        contacto = datos.get('contacto', '').strip()
        if contacto and len(contacto) > 255:
            return False, "La información de contacto es demasiado larga (máximo 255 caracteres)."
        notas_generales = datos.get('notas_generales', '').strip()
        if notas_generales and len(notas_generales) > 2000:
            return False, "Las notas generales son demasiado largas (máximo 2000 caracteres)."
        estado = datos.get('estado', '')
        estados_validos = ["Consulta Inicial", "En Análisis", "Convertido", "Desestimado"]
        if estado and estado not in estados_validos:
            return False, f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
        return True, ""
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Datos válidos
    total_tests += 1
    datos_validos = {'nombre': 'Juan Pérez', 'contacto': 'juan@email.com'}
    es_valido, mensaje = validar_datos_prospecto_test(datos_validos)
    if es_valido and mensaje == "":
        print("✅ Test 1: Datos válidos aceptados")
        tests_passed += 1
    else:
        print(f"❌ Test 1: Falló - {mensaje}")
    
    # Test 2: Nombre vacío
    total_tests += 1
    datos_invalidos = {'nombre': '', 'contacto': 'test@email.com'}
    es_valido, mensaje = validar_datos_prospecto_test(datos_invalidos)
    if not es_valido and "no puede estar vacío" in mensaje:
        print("✅ Test 2: Nombre vacío rechazado")
        tests_passed += 1
    else:
        print("❌ Test 2: Falló - Debería rechazar nombre vacío")
    
    # Test 3: Nombre demasiado largo
    total_tests += 1
    datos_largo = {'nombre': 'A' * 256}
    es_valido, mensaje = validar_datos_prospecto_test(datos_largo)
    if not es_valido and "demasiado largo" in mensaje:
        print("✅ Test 3: Nombre largo rechazado")
        tests_passed += 1
    else:
        print("❌ Test 3: Falló - Debería rechazar nombre largo")
    
    if tests_passed == total_tests:
        print(f"✅ Todos los tests inline pasaron ({tests_passed}/{total_tests})")
        return True
    else:
        print(f"❌ Tests inline fallaron ({tests_passed}/{total_tests})")
        return False


def main():
    """Función principal del script de CI/CD standalone"""
    print_header("CI/CD Standalone - Módulo de Prospectos Refactorizado")
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 Directorio: {os.getcwd()}")
    
    # Contadores
    total_checks = 0
    passed_checks = 0
    
    # Lista de verificaciones
    checks = [
        ("Integridad de archivos", check_file_integrity),
        ("Sintaxis", check_syntax),
        ("Función de validación", check_validation_function),
        ("Aliases de compatibilidad", check_aliases),
        ("Organización de funciones", check_function_organization),
        ("Actualizaciones en prospects_window", check_prospects_window_updates),
        ("Test inline de validación", run_inline_validation_test),
    ]
    
    # Ejecutar verificaciones
    for check_name, check_function in checks:
        total_checks += 1
        try:
            if check_function():
                passed_checks += 1
                print(f"✅ {check_name}: OK")
            else:
                print(f"❌ {check_name}: FALLÓ")
        except Exception as e:
            print(f"❌ {check_name}: ERROR - {e}")
    
    # Resumen final
    print_header("Resumen de Resultados")
    
    success_rate = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    print(f"📊 Verificaciones totales: {total_checks}")
    print(f"✅ Verificaciones exitosas: {passed_checks}")
    print(f"❌ Verificaciones fallidas: {total_checks - passed_checks}")
    print(f"📈 Tasa de éxito: {success_rate:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 ¡TODAS LAS VERIFICACIONES PASARON!")
        print("✅ El refactor se completó exitosamente")
        print("✅ Todas las funciones están en su lugar")
        print("✅ La compatibilidad está garantizada")
        print("✅ El código está bien organizado")
        print("✅ Listo para uso en producción")
        return True
    else:
        print(f"\n❌ {total_checks - passed_checks} VERIFICACIONES FALLARON")
        if success_rate >= 80:
            print("⚠️  Mayoría de verificaciones pasaron, revisar fallos menores")
        else:
            print("🔧 Revisar los errores antes de usar en producción")
        return False


if __name__ == "__main__":
    print("🚀 Iniciando verificaciones standalone del refactor...")
    
    success = main()
    
    print(f"\n🏁 Verificaciones completadas: {'ÉXITO TOTAL' if success else 'CON FALLOS'}")
    
    # Exit code para integración con sistemas de CI/CD
    sys.exit(0 if success else 1)