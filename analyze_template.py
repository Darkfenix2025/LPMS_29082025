#!/usr/bin/env python3
"""
Analizador de plantillas de acuerdos de mediación.
Analiza la plantilla existente y sugiere mejoras para integración con el sistema.
"""

import sys
import os
from datetime import datetime

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_existing_template():
    """Analiza la plantilla existente."""
    print("🔍 ANALIZANDO PLANTILLA EXISTENTE")
    print("=" * 50)
    
    template_path = 'plantillas/mediacion/acuerdo_base.docx'
    
    try:
        # Verificar si existe la plantilla
        if not os.path.exists(template_path):
            print(f"❌ No se encontró la plantilla en: {template_path}")
            return False
        
        print(f"✅ Plantilla encontrada: {template_path}")
        
        # Obtener información del archivo
        file_size = os.path.getsize(template_path)
        file_time = os.path.getmtime(template_path)
        file_date = datetime.fromtimestamp(file_time).strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"📊 Tamaño: {file_size:,} bytes")
        print(f"📅 Última modificación: {file_date}")
        
        # Intentar cargar con docxtpl
        try:
            from docxtpl import DocxTemplate
            
            print("\n🔧 Analizando estructura con docxtpl...")
            doc = DocxTemplate(template_path)
            
            # Obtener variables de la plantilla
            try:
                variables = doc.get_undeclared_template_variables()
                print(f"✅ Plantilla cargada exitosamente")
                print(f"📝 Variables encontradas: {len(variables)}")
                
                if variables:
                    print("\n🏷️ Variables en la plantilla:")
                    for i, var in enumerate(sorted(variables), 1):
                        print(f"   {i:2d}. {var}")
                else:
                    print("⚠️ No se encontraron variables de plantilla")
                
                return variables
                
            except Exception as e:
                print(f"⚠️ No se pudieron obtener las variables: {e}")
                return []
                
        except ImportError:
            print("❌ docxtpl no está disponible")
            return False
        except Exception as e:
            print(f"❌ Error cargando plantilla: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error analizando plantilla: {e}")
        return False

def get_system_variables():
    """Obtiene las variables que genera nuestro sistema."""
    print("\n🖥️ VARIABLES DEL SISTEMA")
    print("=" * 50)
    
    # Variables que nuestro sistema genera
    system_variables = {
        # Información del caso
        'NUMERO_EXPEDIENTE': 'Número del expediente judicial',
        'CARATULA': 'Carátula completa del caso',
        
        # Fecha del acuerdo
        'DIA_ACUERDO': 'Día del acuerdo (número)',
        'MES_ACUERDO': 'Mes del acuerdo (texto en español)',
        'AÑO_ACUERDO': 'Año del acuerdo (número)',
        'FECHA_COMPLETA': 'Fecha completa formateada',
        'FECHA_CORTA': 'Fecha en formato dd/mm/yyyy',
        
        # Partes del caso
        'ACTORES': 'Lista de actores con representantes',
        'DEMANDADOS': 'Lista de demandados con representantes',
        'NOMBRE_ACTOR': 'Nombre del actor principal',
        
        # Montos y compensaciones
        'MONTO_COMPENSACION_NUMEROS': 'Monto en números',
        'MONTO_COMPENSACION_LETRAS': 'Monto en letras',
        'PLAZO_PAGO_DIAS': 'Plazo en días (número)',
        'PLAZO_PAGO_LETRAS': 'Plazo en letras',
        
        # Datos bancarios del actor
        'BANCO_ACTOR': 'Nombre del banco',
        'CBU_ACTOR': 'CBU del actor',
        'ALIAS_ACTOR': 'Alias del CBU',
        'CUIT_ACTOR': 'CUIT/CUIL del actor',
        
        # Honorarios (si aplica)
        'MONTO_HONORARIOS_NUMEROS': 'Honorarios en números',
        'MONTO_HONORARIOS_LETRAS': 'Honorarios en letras',
        'HONORARIOS_LETRAS': 'Honorarios en letras (compatibilidad plantilla)',
        'PLAZO_PAGO_HONORARIOS_DIAS': 'Plazo para honorarios',
        
        # Variables auxiliares
        'rep': 'Variable auxiliar para representantes',
        
        # Variables adicionales disponibles
        'LUGAR_ACUERDO': 'Lugar donde se firma el acuerdo',
        'MEDIADOR': 'Nombre del mediador',
        'CENTRO_MEDIACION': 'Centro de mediación',
        'OBSERVACIONES': 'Observaciones adicionales',
        'CLAUSULAS_ADICIONALES': 'Cláusulas adicionales'
    }
    
    print(f"📝 Variables disponibles en el sistema: {len(system_variables)}")
    print("\n🏷️ Lista de variables:")
    
    for i, (var, desc) in enumerate(system_variables.items(), 1):
        print(f"   {i:2d}. {var:<30} - {desc}")
    
    return system_variables

def compare_variables(template_vars, system_vars):
    """Compara las variables de la plantilla con las del sistema."""
    print("\n🔄 COMPARACIÓN DE VARIABLES")
    print("=" * 50)
    
    if not template_vars:
        print("⚠️ No se pudieron obtener variables de la plantilla para comparar")
        return
    
    template_set = set(template_vars) if template_vars else set()
    system_set = set(system_vars.keys())
    
    # Variables que están en la plantilla pero no en el sistema
    missing_in_system = template_set - system_set
    
    # Variables que están en el sistema pero no en la plantilla
    missing_in_template = system_set - template_set
    
    # Variables que coinciden
    matching = template_set & system_set
    
    print(f"✅ Variables que coinciden: {len(matching)}")
    if matching:
        for var in sorted(matching):
            print(f"   ✓ {var}")
    
    print(f"\n⚠️ Variables en plantilla pero no en sistema: {len(missing_in_system)}")
    if missing_in_system:
        for var in sorted(missing_in_system):
            print(f"   ? {var}")
    
    print(f"\n💡 Variables disponibles en sistema pero no en plantilla: {len(missing_in_template)}")
    if missing_in_template:
        for var in sorted(missing_in_template):
            desc = system_vars.get(var, 'Sin descripción')
            print(f"   + {var:<30} - {desc}")
    
    return {
        'matching': matching,
        'missing_in_system': missing_in_system,
        'missing_in_template': missing_in_template
    }

def suggest_improvements(comparison):
    """Sugiere mejoras para la plantilla."""
    print("\n💡 SUGERENCIAS DE MEJORA")
    print("=" * 50)
    
    if not comparison:
        print("⚠️ No se pudo realizar comparación")
        return
    
    suggestions = []
    
    # Sugerencias basadas en variables faltantes
    if comparison['missing_in_template']:
        suggestions.append({
            'type': 'add_variables',
            'title': 'Agregar variables del sistema',
            'description': 'Estas variables están disponibles en el sistema y podrían mejorar la plantilla',
            'variables': comparison['missing_in_template']
        })
    
    # Sugerencias basadas en variables no reconocidas
    if comparison['missing_in_system']:
        suggestions.append({
            'type': 'review_variables',
            'title': 'Revisar variables no reconocidas',
            'description': 'Estas variables están en la plantilla pero el sistema no las genera',
            'variables': comparison['missing_in_system']
        })
    
    # Sugerencias generales
    general_suggestions = [
        {
            'type': 'structure',
            'title': 'Mejorar estructura del documento',
            'items': [
                'Usar encabezados consistentes',
                'Agregar numeración automática de cláusulas',
                'Incluir tabla de contenidos si es necesario',
                'Usar estilos de Word consistentes'
            ]
        },
        {
            'type': 'data_validation',
            'title': 'Validación de datos',
            'items': [
                'Agregar validaciones para campos obligatorios',
                'Usar formato condicional para resaltar datos importantes',
                'Incluir valores por defecto para campos opcionales'
            ]
        },
        {
            'type': 'legal_compliance',
            'title': 'Cumplimiento legal',
            'items': [
                'Verificar que incluya todas las cláusulas legales requeridas',
                'Asegurar formato correcto para fechas y montos',
                'Incluir espacios para firmas y aclaraciones',
                'Agregar pie de página con información del centro de mediación'
            ]
        }
    ]
    
    suggestions.extend(general_suggestions)
    
    # Mostrar sugerencias
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion['title']}")
        print(f"   Tipo: {suggestion['type']}")
        
        if 'description' in suggestion:
            print(f"   Descripción: {suggestion['description']}")
        
        if 'variables' in suggestion:
            print(f"   Variables ({len(suggestion['variables'])}):")
            for var in sorted(suggestion['variables']):
                print(f"      • {var}")
        
        if 'items' in suggestion:
            print(f"   Recomendaciones:")
            for item in suggestion['items']:
                print(f"      • {item}")
    
    return suggestions

def create_template_guide():
    """Crea una guía para mejorar la plantilla."""
    print("\n📖 CREANDO GUÍA DE MEJORA")
    print("=" * 50)
    
    guide_content = """# Guía para Mejorar la Plantilla de Acuerdo de Mediación

## Variables Disponibles en el Sistema

### Información del Caso
- `{{NUMERO_EXPEDIENTE}}` - Número del expediente judicial
- `{{CARATULA}}` - Carátula completa del caso

### Fecha del Acuerdo
- `{{DIA_ACUERDO}}` - Día (número): 15
- `{{MES_ACUERDO}}` - Mes (texto): marzo
- `{{AÑO_ACUERDO}}` - Año (número): 2024
- `{{FECHA_COMPLETA}}` - Fecha formateada: "15 de marzo de 2024"

### Partes del Caso
- `{{NOMBRE_ACTOR}}` - Nombre del actor principal
- `{{ACTORES}}` - Lista completa de actores (con representantes)
- `{{DEMANDADOS}}` - Lista completa de demandados (con representantes)

### Montos y Plazos
- `{{MONTO_COMPENSACION_NUMEROS}}` - Monto en números: "150000"
- `{{MONTO_COMPENSACION_LETRAS}}` - Monto en letras: "CIENTO CINCUENTA MIL"
- `{{PLAZO_PAGO_DIAS}}` - Plazo en días: "30"
- `{{PLAZO_PAGO_LETRAS}}` - Plazo en letras: "TREINTA"

### Datos Bancarios
- `{{BANCO_ACTOR}}` - Nombre del banco
- `{{CBU_ACTOR}}` - CBU del actor
- `{{ALIAS_ACTOR}}` - Alias del CBU
- `{{CUIT_ACTOR}}` - CUIT/CUIL del actor

## Ejemplo de Uso en la Plantilla

```
ACUERDO DE MEDIACIÓN

En la Ciudad de Buenos Aires, a los {{DIA_ACUERDO}} días del mes de {{MES_ACUERDO}} de {{AÑO_ACUERDO}}, en el marco del expediente N° {{NUMERO_EXPEDIENTE}}, caratulado "{{CARATULA}}", las partes acuerdan:

PRIMERA: El demandado se compromete a abonar al actor la suma de PESOS {{MONTO_COMPENSACION_LETRAS}} (${{MONTO_COMPENSACION_NUMEROS}}) en concepto de compensación.

SEGUNDA: El pago se realizará en un plazo de {{PLAZO_PAGO_LETRAS}} ({{PLAZO_PAGO_DIAS}}) días hábiles.

TERCERA: Los datos bancarios para la transferencia son:
- Banco: {{BANCO_ACTOR}}
- CBU: {{CBU_ACTOR}}
- Alias: {{ALIAS_ACTOR}}
- CUIT: {{CUIT_ACTOR}}
```

## Recomendaciones Técnicas

1. **Usar sintaxis de docxtpl**: `{{variable}}` para variables simples
2. **Para listas de partes**: Usar loops de Jinja2
3. **Formateo condicional**: Usar `{% if %}` para campos opcionales
4. **Estilos de Word**: Aplicar estilos consistentes para mejor presentación

## Ejemplo de Loop para Partes

```
ACTORES:
{% for actor in ACTORES %}
- {{actor.nombre_completo}} ({{actor.rol_principal}})
  {% if actor.representantes %}
  Representado por:
    {% for rep in actor.representantes %}
    • {{rep.nombre_completo}}
    {% endfor %}
  {% endif %}
{% endfor %}
```

## Validación de Campos

Para campos que pueden estar vacíos, usar:
```
{% if BANCO_ACTOR %}
Banco: {{BANCO_ACTOR}}
{% else %}
Banco: A definir
{% endif %}
```
"""
    
    try:
        with open('guia_plantilla_mediacion.md', 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print("✅ Guía creada: guia_plantilla_mediacion.md")
        return True
        
    except Exception as e:
        print(f"❌ Error creando guía: {e}")
        return False

def test_template_with_system():
    """Prueba la plantilla con datos del sistema."""
    print("\n🧪 PROBANDO PLANTILLA CON DATOS DEL SISTEMA")
    print("=" * 50)
    
    template_path = 'plantillas/mediacion/acuerdo_base.docx'
    
    try:
        from docxtpl import DocxTemplate
        from case_dialog_manager import convertir_numero_a_letras, convertir_plazo_a_letras
        
        # Crear datos de prueba
        test_data = {
            'NUMERO_EXPEDIENTE': '12345/2024',
            'CARATULA': 'Pérez Juan c/ García María s/ Mediación por Daños y Perjuicios',
            'DIA_ACUERDO': 15,
            'MES_ACUERDO': 'marzo',
            'AÑO_ACUERDO': 2024,
            'FECHA_COMPLETA': '15 de marzo de 2024',
            'ACTORES': [
                {
                    'nombre_completo': 'Juan Pérez',
                    'rol_principal': 'Actor',
                    'representantes': [
                        {'nombre_completo': 'Dr. Carlos López'}
                    ]
                }
            ],
            'DEMANDADOS': [
                {
                    'nombre_completo': 'María García',
                    'rol_principal': 'Demandado',
                    'representantes': [
                        {'nombre_completo': 'Dra. Ana Martínez'}
                    ]
                }
            ],
            'NOMBRE_ACTOR': 'Juan Pérez',
            'MONTO_COMPENSACION_NUMEROS': '150000',
            'MONTO_COMPENSACION_LETRAS': convertir_numero_a_letras('150000'),
            'PLAZO_PAGO_DIAS': '30',
            'PLAZO_PAGO_LETRAS': convertir_plazo_a_letras('30'),
            'BANCO_ACTOR': 'Banco Nación',
            'CBU_ACTOR': '0110599520000001234567',
            'ALIAS_ACTOR': 'JUAN.PEREZ.ACTOR',
            'CUIT_ACTOR': '20123456789',
            'MONTO_HONORARIOS_NUMEROS': '0',
            'MONTO_HONORARIOS_LETRAS': 'CERO',
            'HONORARIOS_LETRAS': 'CERO',  # Variable específica de la plantilla
            'PLAZO_PAGO_HONORARIOS_DIAS': '0',
            'FECHA_COMPLETA': '15 de marzo de 2024',
            'FECHA_CORTA': '15/03/2024',
            'LUGAR_ACUERDO': 'Ciudad Autónoma de Buenos Aires',
            'MEDIADOR': 'Mediador designado',
            'CENTRO_MEDIACION': 'Centro de Mediación',
            'OBSERVACIONES': '',
            'CLAUSULAS_ADICIONALES': '',
            'rep': {}
        }
        
        print("📊 Datos de prueba preparados:")
        print(f"   Caso: {test_data['CARATULA']}")
        print(f"   Monto: ${test_data['MONTO_COMPENSACION_NUMEROS']} ({test_data['MONTO_COMPENSACION_LETRAS']})")
        print(f"   Plazo: {test_data['PLAZO_PAGO_DIAS']} días ({test_data['PLAZO_PAGO_LETRAS']})")
        
        # Intentar renderizar la plantilla
        print("\n🔧 Intentando renderizar plantilla...")
        
        doc = DocxTemplate(template_path)
        
        # Obtener variables requeridas
        required_vars = doc.get_undeclared_template_variables()
        print(f"   Variables requeridas por plantilla: {len(required_vars)}")
        
        # Verificar qué variables faltan
        missing_vars = [var for var in required_vars if var not in test_data]
        if missing_vars:
            print(f"   ⚠️ Variables faltantes: {missing_vars}")
            # Agregar valores por defecto
            for var in missing_vars:
                test_data[var] = f"[{var}]"
                print(f"      Agregado valor por defecto para: {var}")
        
        # Intentar renderizar
        try:
            doc.render(test_data)
            
            # Guardar documento de prueba
            test_output = 'test_acuerdo_generado.docx'
            doc.save(test_output)
            
            print(f"✅ Plantilla renderizada exitosamente")
            print(f"📄 Documento de prueba guardado: {test_output}")
            
            # Verificar el archivo generado
            if os.path.exists(test_output):
                file_size = os.path.getsize(test_output)
                print(f"📊 Tamaño del documento generado: {file_size:,} bytes")
                
                if file_size > 0:
                    print("🎉 ¡La plantilla funciona correctamente con el sistema!")
                    return True
                else:
                    print("⚠️ El documento se generó pero está vacío")
                    return False
            else:
                print("❌ No se pudo crear el documento de prueba")
                return False
                
        except Exception as e:
            print(f"❌ Error renderizando plantilla: {e}")
            print("💡 Esto puede indicar problemas de compatibilidad con las variables")
            return False
            
    except Exception as e:
        print(f"❌ Error en prueba de plantilla: {e}")
        return False

def main():
    """Función principal del analizador."""
    print("🔍 ANALIZADOR DE PLANTILLAS DE MEDIACIÓN")
    print("=" * 60)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # 1. Analizar plantilla existente
        template_vars = analyze_existing_template()
        
        # 2. Obtener variables del sistema
        system_vars = get_system_variables()
        
        # 3. Comparar variables
        comparison = compare_variables(template_vars, system_vars)
        
        # 4. Sugerir mejoras
        suggestions = suggest_improvements(comparison)
        
        # 5. Crear guía
        guide_created = create_template_guide()
        
        # 6. Probar plantilla con sistema
        test_result = test_template_with_system()
        
        # Resumen final
        print("\n" + "=" * 60)
        print("📋 RESUMEN DEL ANÁLISIS")
        print("=" * 60)
        
        if template_vars is not False:
            print(f"✅ Plantilla analizada exitosamente")
            if isinstance(template_vars, list):
                print(f"📝 Variables en plantilla: {len(template_vars)}")
        else:
            print(f"❌ No se pudo analizar la plantilla")
        
        print(f"🖥️ Variables del sistema: {len(system_vars)}")
        
        if guide_created:
            print(f"📖 Guía de mejora creada")
        
        if test_result:
            print(f"🧪 Prueba de integración: ✅ EXITOSA")
            print(f"🎉 La plantilla es compatible con el sistema")
        else:
            print(f"🧪 Prueba de integración: ❌ FALLÓ")
            print(f"⚠️ La plantilla necesita ajustes para funcionar correctamente")
        
        print(f"\n💡 Próximos pasos recomendados:")
        print(f"   1. Revisar el documento generado: test_acuerdo_generado.docx")
        print(f"   2. Leer la guía de mejora: guia_plantilla_mediacion.md")
        print(f"   3. Ajustar la plantilla según las sugerencias")
        print(f"   4. Probar nuevamente con casos reales")
        
        return 0 if test_result else 1
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())