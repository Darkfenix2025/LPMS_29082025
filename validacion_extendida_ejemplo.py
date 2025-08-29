#!/usr/bin/env python3
"""
Ejemplo de Validación Centralizada Extendida
Demuestra cómo extender la validación para nuevos campos y casos de uso
"""

from typing import Dict, Tuple, List, Optional
import re
from datetime import datetime, date


class ValidadorProspectos:
    """
    Clase de validación extendida para prospectos
    Permite agregar nuevos campos y validaciones fácilmente
    """
    
    def __init__(self):
        # Configuración de límites (fácil de modificar)
        self.limites = {
            'nombre_max': 255,
            'contacto_max': 255,
            'notas_max': 2000,
            'empresa_max': 200,
            'cargo_max': 100,
            'telefono_max': 50,
            'email_max': 255
        }
        
        # Estados válidos (fácil de extender)
        self.estados_validos = [
            "Consulta Inicial",
            "En Análisis", 
            "Convertido",
            "Desestimado",
            "En Seguimiento",  # Nuevo estado
            "Requiere Documentación"  # Nuevo estado
        ]
        
        # Tipos de consulta válidos (nuevo campo)
        self.tipos_consulta = [
            "Derecho Laboral",
            "Derecho Civil",
            "Derecho Penal",
            "Derecho Comercial",
            "Derecho de Familia",
            "Otros"
        ]
        
        # Prioridades válidas (nuevo campo)
        self.prioridades = ["Baja", "Media", "Alta", "Urgente"]
    
    def validar_datos_prospecto_extendido(self, datos: Dict) -> Tuple[bool, str]:
        """
        Validación extendida que puede manejar campos adicionales
        
        Args:
            datos (Dict): Diccionario con los datos del prospecto
            
        Returns:
            Tuple[bool, str]: (es_valido, mensaje_error)
        """
        # Validaciones básicas (existentes)
        resultado_basico = self._validar_campos_basicos(datos)
        if not resultado_basico[0]:
            return resultado_basico
        
        # Validaciones extendidas (nuevas)
        resultado_extendido = self._validar_campos_extendidos(datos)
        if not resultado_extendido[0]:
            return resultado_extendido
        
        # Validaciones de negocio (nuevas)
        resultado_negocio = self._validar_reglas_negocio(datos)
        if not resultado_negocio[0]:
            return resultado_negocio
        
        return True, ""
    
    def _validar_campos_basicos(self, datos: Dict) -> Tuple[bool, str]:
        """Validaciones básicas existentes"""
        
        # Validar nombre obligatorio
        nombre = datos.get('nombre', '').strip()
        if not nombre:
            return False, "El nombre del prospecto no puede estar vacío."
        
        if len(nombre) > self.limites['nombre_max']:
            return False, f"El nombre es demasiado largo (máximo {self.limites['nombre_max']} caracteres)."
        
        # Validar contacto
        contacto = datos.get('contacto', '').strip()
        if contacto and len(contacto) > self.limites['contacto_max']:
            return False, f"El contacto es demasiado largo (máximo {self.limites['contacto_max']} caracteres)."
        
        # Validar notas
        notas = datos.get('notas_generales', '').strip()
        if notas and len(notas) > self.limites['notas_max']:
            return False, f"Las notas son demasiado largas (máximo {self.limites['notas_max']} caracteres)."
        
        # Validar estado
        estado = datos.get('estado', '')
        if estado and estado not in self.estados_validos:
            return False, f"Estado inválido. Debe ser uno de: {', '.join(self.estados_validos)}"
        
        return True, ""
    
    def _validar_campos_extendidos(self, datos: Dict) -> Tuple[bool, str]:
        """Validaciones para campos nuevos/extendidos"""
        
        # Validar empresa (nuevo campo)
        empresa = datos.get('empresa', '').strip()
        if empresa and len(empresa) > self.limites['empresa_max']:
            return False, f"El nombre de empresa es demasiado largo (máximo {self.limites['empresa_max']} caracteres)."
        
        # Validar cargo (nuevo campo)
        cargo = datos.get('cargo', '').strip()
        if cargo and len(cargo) > self.limites['cargo_max']:
            return False, f"El cargo es demasiado largo (máximo {self.limites['cargo_max']} caracteres)."
        
        # Validar teléfono (nuevo campo)
        telefono = datos.get('telefono', '').strip()
        if telefono:
            if len(telefono) > self.limites['telefono_max']:
                return False, f"El teléfono es demasiado largo (máximo {self.limites['telefono_max']} caracteres)."
            
            # Validación básica de formato de teléfono
            if not re.match(r'^[\d\s\-\+\(\)]+$', telefono):
                return False, "El formato del teléfono no es válido."
        
        # Validar email (mejorado)
        email = datos.get('email', '').strip()
        if email:
            if len(email) > self.limites['email_max']:
                return False, f"El email es demasiado largo (máximo {self.limites['email_max']} caracteres)."
            
            # Validación mejorada de email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                return False, "El formato del email no es válido."
        
        # Validar tipo de consulta (nuevo campo)
        tipo_consulta = datos.get('tipo_consulta', '')
        if tipo_consulta and tipo_consulta not in self.tipos_consulta:
            return False, f"Tipo de consulta inválido. Debe ser uno de: {', '.join(self.tipos_consulta)}"
        
        # Validar prioridad (nuevo campo)
        prioridad = datos.get('prioridad', '')
        if prioridad and prioridad not in self.prioridades:
            return False, f"Prioridad inválida. Debe ser una de: {', '.join(self.prioridades)}"
        
        return True, ""
    
    def _validar_reglas_negocio(self, datos: Dict) -> Tuple[bool, str]:
        """Validaciones de reglas de negocio específicas"""
        
        # Regla: Si el estado es "Convertido", debe tener fecha de conversión
        estado = datos.get('estado', '')
        fecha_conversion = datos.get('fecha_conversion')
        if estado == "Convertido" and not fecha_conversion:
            return False, "Los prospectos convertidos deben tener fecha de conversión."
        
        # Regla: Si tiene prioridad "Urgente", debe tener contacto
        prioridad = datos.get('prioridad', '')
        contacto = datos.get('contacto', '').strip()
        email = datos.get('email', '').strip()
        telefono = datos.get('telefono', '').strip()
        
        if prioridad == "Urgente" and not (contacto or email or telefono):
            return False, "Los prospectos urgentes deben tener al menos un método de contacto."
        
        # Regla: Si tiene empresa, debe tener cargo
        empresa = datos.get('empresa', '').strip()
        cargo = datos.get('cargo', '').strip()
        if empresa and not cargo:
            return False, "Si especifica empresa, debe indicar el cargo."
        
        # Regla: Validar fecha de primera consulta
        fecha_primera_consulta = datos.get('fecha_primera_consulta')
        if fecha_primera_consulta:
            try:
                if isinstance(fecha_primera_consulta, str):
                    fecha_obj = datetime.strptime(fecha_primera_consulta, '%Y-%m-%d').date()
                elif isinstance(fecha_primera_consulta, date):
                    fecha_obj = fecha_primera_consulta
                else:
                    return False, "Formato de fecha de primera consulta inválido."
                
                # No puede ser fecha futura
                if fecha_obj > date.today():
                    return False, "La fecha de primera consulta no puede ser futura."
                    
            except ValueError:
                return False, "Formato de fecha de primera consulta inválido. Use YYYY-MM-DD."
        
        return True, ""
    
    def validar_lista_prospectos(self, lista_prospectos: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Valida una lista completa de prospectos
        Útil para importaciones masivas
        """
        errores = []
        
        for i, prospecto in enumerate(lista_prospectos):
            es_valido, mensaje = self.validar_datos_prospecto_extendido(prospecto)
            if not es_valido:
                errores.append(f"Prospecto {i+1}: {mensaje}")
        
        return len(errores) == 0, errores
    
    def agregar_estado_valido(self, nuevo_estado: str):
        """Permite agregar nuevos estados válidos dinámicamente"""
        if nuevo_estado not in self.estados_validos:
            self.estados_validos.append(nuevo_estado)
    
    def agregar_tipo_consulta(self, nuevo_tipo: str):
        """Permite agregar nuevos tipos de consulta dinámicamente"""
        if nuevo_tipo not in self.tipos_consulta:
            self.tipos_consulta.append(nuevo_tipo)
    
    def configurar_limite(self, campo: str, nuevo_limite: int):
        """Permite modificar límites de caracteres dinámicamente"""
        if campo in self.limites:
            self.limites[campo] = nuevo_limite


def test_validacion_extendida():
    """Test de la validación extendida"""
    print("🧪 Ejecutando tests de validación extendida...")
    
    validador = ValidadorProspectos()
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Datos básicos válidos
    total_tests += 1
    datos_basicos = {
        'nombre': 'Juan Pérez',
        'contacto': 'juan@email.com',
        'estado': 'Consulta Inicial'
    }
    es_valido, mensaje = validador.validar_datos_prospecto_extendido(datos_basicos)
    if es_valido:
        print("✅ Test 1 pasó: Datos básicos válidos")
        tests_passed += 1
    else:
        print(f"❌ Test 1 falló: {mensaje}")
    
    # Test 2: Datos extendidos válidos
    total_tests += 1
    datos_extendidos = {
        'nombre': 'María García',
        'email': 'maria.garcia@empresa.com.ar',
        'telefono': '+54 9 11 1234-5678',
        'empresa': 'Empresa SA',
        'cargo': 'Gerente de RRHH',
        'tipo_consulta': 'Derecho Laboral',
        'prioridad': 'Alta',
        'estado': 'En Análisis'
    }
    es_valido, mensaje = validador.validar_datos_prospecto_extendido(datos_extendidos)
    if es_valido:
        print("✅ Test 2 pasó: Datos extendidos válidos")
        tests_passed += 1
    else:
        print(f"❌ Test 2 falló: {mensaje}")
    
    # Test 3: Regla de negocio - Urgente sin contacto (debe fallar)
    total_tests += 1
    datos_urgente_sin_contacto = {
        'nombre': 'Carlos López',
        'prioridad': 'Urgente'
    }
    es_valido, mensaje = validador.validar_datos_prospecto_extendido(datos_urgente_sin_contacto)
    if not es_valido and "método de contacto" in mensaje:
        print("✅ Test 3 pasó: Rechaza urgente sin contacto")
        tests_passed += 1
    else:
        print(f"❌ Test 3 falló: Debería rechazar urgente sin contacto")
    
    # Test 4: Regla de negocio - Empresa sin cargo (debe fallar)
    total_tests += 1
    datos_empresa_sin_cargo = {
        'nombre': 'Ana Rodríguez',
        'empresa': 'Empresa XYZ'
    }
    es_valido, mensaje = validador.validar_datos_prospecto_extendido(datos_empresa_sin_cargo)
    if not es_valido and "debe indicar el cargo" in mensaje:
        print("✅ Test 4 pasó: Rechaza empresa sin cargo")
        tests_passed += 1
    else:
        print(f"❌ Test 4 falló: Debería rechazar empresa sin cargo")
    
    # Test 5: Email inválido (debe fallar)
    total_tests += 1
    datos_email_invalido = {
        'nombre': 'Pedro Martínez',
        'email': 'email_invalido'
    }
    es_valido, mensaje = validador.validar_datos_prospecto_extendido(datos_email_invalido)
    if not es_valido and "formato del email" in mensaje:
        print("✅ Test 5 pasó: Rechaza email inválido")
        tests_passed += 1
    else:
        print(f"❌ Test 5 falló: Debería rechazar email inválido")
    
    # Test 6: Extensibilidad - Agregar nuevo estado
    total_tests += 1
    validador.agregar_estado_valido("En Revisión Legal")
    datos_nuevo_estado = {
        'nombre': 'Laura Fernández',
        'estado': 'En Revisión Legal'
    }
    es_valido, mensaje = validador.validar_datos_prospecto_extendido(datos_nuevo_estado)
    if es_valido:
        print("✅ Test 6 pasó: Acepta nuevo estado agregado dinámicamente")
        tests_passed += 1
    else:
        print(f"❌ Test 6 falló: {mensaje}")
    
    # Resumen
    print("\n" + "=" * 60)
    if tests_passed == total_tests:
        print("🎉 ¡Todos los tests de validación extendida pasaron!")
        print(f"✅ {tests_passed}/{total_tests} tests exitosos")
        print("\n🔍 Características verificadas:")
        print("   ✅ Validaciones básicas funcionan")
        print("   ✅ Campos extendidos son validados")
        print("   ✅ Reglas de negocio se aplican")
        print("   ✅ Validaciones de formato funcionan")
        print("   ✅ Extensibilidad dinámica funciona")
        print("\n🎯 La validación extendida está lista para producción.")
        return True
    else:
        print(f"❌ {total_tests - tests_passed} tests fallaron")
        print(f"✅ {tests_passed}/{total_tests} tests exitosos")
        return False


if __name__ == "__main__":
    success = test_validacion_extendida()
    print(f"\n🏁 Resultado final: {'ÉXITO' if success else 'FALLÓ'}")
    
    # Demostrar uso práctico
    print("\n" + "=" * 60)
    print("📋 Ejemplo de Uso Práctico:")
    
    validador = ValidadorProspectos()
    
    # Ejemplo de prospecto completo
    prospecto_ejemplo = {
        'nombre': 'Roberto Silva',
        'email': 'roberto.silva@consultora.com',
        'telefono': '+54 9 11 5555-1234',
        'empresa': 'Consultora Legal SA',
        'cargo': 'Director Legal',
        'tipo_consulta': 'Derecho Comercial',
        'prioridad': 'Media',
        'estado': 'En Análisis',
        'notas_generales': 'Cliente referido por otro abogado. Consulta sobre contratos comerciales.',
        'fecha_primera_consulta': '2024-01-15'
    }
    
    es_valido, mensaje = validador.validar_datos_prospecto_extendido(prospecto_ejemplo)
    if es_valido:
        print("✅ Prospecto de ejemplo válido")
        print("🎯 Listo para guardar en base de datos")
    else:
        print(f"❌ Prospecto de ejemplo inválido: {mensaje}")