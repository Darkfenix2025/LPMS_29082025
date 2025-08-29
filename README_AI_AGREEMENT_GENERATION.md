# 🤖 Sistema de Generación de Acuerdos con IA - VERSIÓN MEJORADA

## 🚀 NUEVAS FUNCIONALIDADES v2.0 - AGENTE CON ACCESO DIRECTO A BASE DE DATOS

### ✅ Interfaz Mejorada con Acceso Directo a Base de Datos

- **Treeview de casos ordenados alfabéticamente**
- **Búsqueda en tiempo real** por carátula, expediente o cliente
- **Información detallada del caso seleccionado**
- **Doble clic para ver detalles completos**
- **Acceso directo a todos los datos del expediente**
- **Interfaz más intuitiva y profesional**

### ✅ Agente IA con Conocimiento Completo

- **Acceso automático a base de datos de casos**
- **No requiere especificar IDs manualmente**
- **Comprende contexto completo del expediente**
- **Generación inteligente de acuerdos**
- **Consultas en lenguaje natural**

### 🎯 Cómo Usar la Nueva Interfaz

1. **Abrir desde la aplicación principal:**
   - Menú Asistente IA → Agente IA - Generación de Acuerdos

2. **Funcionalidades disponibles:**
   - Ver lista completa de casos ordenados alfabéticamente
   - Usar campo de búsqueda para filtrar casos
   - Seleccionar caso haciendo clic en la fila
   - Ver información del caso en el panel inferior
   - Hacer doble clic para ver detalles completos
   - Escribir consulta en lenguaje natural
   - El agente accede automáticamente a todos los datos

3. **Consultas de ejemplo ahora posibles:**
   - "Genera acuerdo para el caso seleccionado"
   - "Crea acuerdo laboral con representante"
   - "Necesito acuerdo de divorcio"
   - "Genera acuerdo comercial para este expediente"
   - "Acuerdo con monto de $50,000 y 30 días de plazo"

### 📈 Ventajas de la Nueva Versión

- **No necesitas recordar IDs de casos**
- **Búsqueda visual e intuitiva**
- **Acceso directo a información del cliente**
- **Vista previa de expediente y juzgado**
- **Interfaz más profesional y moderna**
- **Mejor experiencia de usuario**
- **Mayor eficiencia en el trabajo diario**

---

## Descripción General

El **Sistema de Generación de Acuerdos con IA** es una funcionalidad avanzada que permite crear acuerdos de mediación personalizados utilizando inteligencia artificial y análisis de documentos de ejemplo. El sistema combina:

- **Análisis inteligente de documentos**: Extrae patrones y estructuras de acuerdos existentes
- **Generación con IA**: Utiliza modelos de lenguaje para crear contenido personalizado
- **Integración con base de datos**: Incorpora automáticamente datos del caso, partes y representantes
- **Múltiples formatos de salida**: Genera documentos Word profesionales

## 🚀 Características Principales

### ✅ Análisis de Documentos de Ejemplo
- **Extracción automática de patrones**: Identifica secciones, placeholders y estructuras
- **Análisis de metadatos**: Extrae información sobre formato y estilo
- **Detección de secciones**: Encabezados, partes involucradas, términos del acuerdo, firmas
- **Recomendaciones inteligentes**: Sugiere mejoras basadas en el análisis

### ✅ Generación con IA Avanzada
- **Contenido personalizado**: Adapta el lenguaje y estructura según el caso específico
- **Manejo de múltiples partes**: Soporte completo para actores y demandados con representantes
- **Validación automática**: Verifica consistencia y completitud del contenido
- **Optimización legal**: Asegura que el lenguaje sea apropiado para documentos legales

### ✅ Integración Completa con el Sistema
- **Acceso a base de datos**: Extrae automáticamente datos del caso y partes involucradas
- **Sistema de agentes**: Integrado con el framework de agentes existente
- **Interfaz unificada**: Funciona tanto desde código como desde el sistema de agentes
- **Manejo de errores robusto**: Logging completo y recuperación de errores

## 📋 Requisitos del Sistema

### Dependencias de Python
```bash
pip install python-docx langchain langchain-community ollama pydantic
```

### Requisitos de Hardware/Software
- **Ollama**: Debe estar ejecutándose con el modelo `gpt-oss:20b`
- **Base de datos**: Sistema CRM con casos y partes configurado
- **Documentos de ejemplo**: Archivos Word (.docx) para análisis (opcional pero recomendado)

## 🏗️ Arquitectura del Sistema

### Componentes Principales

#### 1. `AIAgreementGenerator` (ai_agreement_generator.py)
**Clase principal que coordina todo el proceso de generación.**

**Métodos principales:**
- `__init__()`: Inicializa el generador con configuración opcional
- `generate_agreement_with_ai()`: Método principal para generar acuerdos
- `_analyze_example_document()`: Analiza documentos de ejemplo
- `_get_case_data_for_ai()`: Extrae datos del caso de la base de datos
- `_generate_content_with_ai()`: Genera contenido usando IA
- `_create_document_from_ai_content()`: Crea documento Word final

#### 2. `generar_acuerdo_ia_tool` (agent_tools.py)
**Herramienta integrada con el sistema de agentes.**

**Funcionalidades:**
- Validación completa de parámetros de entrada
- Integración con métricas de rendimiento
- Manejo de errores y logging detallado
- Interfaz compatible con LangChain

#### 3. Sistema de Agentes (agent_core.py)
**Integración con el framework de agentes existente.**

**Características:**
- Agrega la nueva herramienta a la lista de herramientas disponibles
- Mantiene compatibilidad con el sistema ReAct existente
- Preserva todas las funcionalidades anteriores

## 📖 Uso del Sistema

### 1. Uso Básico (desde código)

```python
from ai_agreement_generator import AIAgreementGenerator

# Inicializar generador
generator = AIAgreementGenerator()

# Datos del acuerdo
agreement_details = {
    "monto_compensacion_numeros": "250000",
    "plazo_pago_dias": "45",
    "banco_actor": "Banco Santander",
    "cbu_actor": "0720123456789012345678",
    "alias_actor": "empresa.legal",
    "cuit_actor": "27-12345678-1"
}

# Generar acuerdo
result = generator.generate_agreement_with_ai(
    case_id=123,
    agreement_details=agreement_details
)

if result['success']:
    print(f"Documento generado: {result['filename']}")
else:
    print(f"Error: {result['error_message']}")
```

### 2. Uso con Documento de Ejemplo

```python
# Inicializar con documento de ejemplo
generator = AIAgreementGenerator(
    example_document_path="ruta/al/documento/ejemplo.docx"
)

# El sistema analizará automáticamente el documento de ejemplo
# y usará sus patrones para generar el nuevo acuerdo
result = generator.generate_agreement_with_ai(
    case_id=123,
    agreement_details=agreement_details,
    example_document_path="ruta/al/documento/ejemplo.docx"
)
```

### 3. Uso desde el Sistema de Agentes

```python
from agent_core import AgentCore

# Inicializar agente
agent = AgentCore()

# Consulta en lenguaje natural
query = """
Genera un acuerdo de mediación usando IA para el caso 123.
Monto: 150000 pesos
Plazo: 30 días
Banco: Banco Nación
CBU: 0720123456789012345678
Alias: empresa.legal
CUIT: 27-12345678-1
"""

# El agente usará automáticamente la herramienta de IA
response = agent.run_intent(query)
print(response)
```

## 🔍 Análisis de Documentos de Ejemplo

### Funcionalidades de Análisis

```python
# Analizar un documento para extraer patrones
analysis = generator.analyze_document_for_patterns("documento_ejemplo.docx")

if 'error' not in analysis:
    print("Metadatos:", analysis['structure']['metadata'])
    print("Patrones encontrados:", analysis['patterns'])
    print("Recomendaciones:", analysis['recommendations'])
```

### Tipos de Patrones Detectados
- **Patrones de encabezado**: Juzgado, expediente, carátula
- **Patrones de partes**: Actores, demandados, representantes
- **Patrones de acuerdo**: Montos, plazos, condiciones
- **Patrones de firma**: Secciones de conformidad y firmas

## 📊 Extracción de Datos del Caso

### Estructura de Datos Extraída

```python
case_data = generator._get_case_data_for_ai(case_id)

# Estructura resultante:
{
    'case_info': {
        'id': 123,
        'caratula': 'DISANTI ADOLFO RUBEN c/ PILISAR S.A. s/ RECLAMO',
        'numero_expediente': 'J-01-00091307-9',
        'juzgado': 'Juzgado Civil 1',
        # ... más campos
    },
    'client': {
        'nombre': 'Juan',
        'apellido': 'Pérez',
        'dni': '12345678',
        'cuit': '20-12345678-1',
        # ... más campos
    },
    'actors': [
        {
            'nombre_completo': 'DISANTI ADOLFO RUBEN',
            'dni': '12345678',
            'cuit': '20-12345678-1',
            'representantes': [
                {
                    'nombre_completo': 'Dr. Juan Pérez',
                    'cuit': '20-87654321-1',
                    'personeria': 'Poder General Judicial'
                }
            ]
        }
    ],
    'defendants': [
        {
            'nombre_completo': 'PILISAR S.A.',
            'cuit': '30-12345678-1',
            'representantes': [...]
        }
    ]
}
```

## 🎯 Casos de Uso

### Caso 1: Generación Básica
```python
# Generación simple sin documento de ejemplo
generator = AIAgreementGenerator()
result = generator.generate_agreement_with_ai(case_id=123, agreement_details=details)
```

### Caso 2: Con Análisis de Ejemplo
```python
# Usar documento existente como base
generator = AIAgreementGenerator(example_document_path="acuerdo_anterior.docx")
result = generator.generate_agreement_with_ai(case_id=123, agreement_details=details)
```

### Caso 3: Integración con Agentes
```python
# El agente decide automáticamente cuándo usar IA
agent = AgentCore()
response = agent.run_intent("Genera un acuerdo de mediación para el caso 123 con monto 200000")
```

## 📁 Estructura de Archivos Generados

Los documentos se generan en la carpeta `generated_documents/` con nombres descriptivos:

```
generated_documents/
├── Acuerdo_Mediacion_AI_J-01-00091307-9_20241228_143052.docx
├── Acuerdo_Mediacion_AI_Expte_123_20241228_143053.docx
└── ...
```

## ⚙️ Configuración Avanzada

### Variables de Entorno
```bash
# Configuración de Ollama
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_BASE_URL=http://localhost:11434

# Configuración de documentos
DEFAULT_TEMPLATE_PATH=plantillas/mediacion/acuerdo_base.docx
GENERATED_DOCUMENTS_PATH=generated_documents/
```

### Personalización del Prompt de IA
El sistema utiliza prompts especializados para abogados argentinos. Puede personalizarse modificando los templates en `ai_agreement_generator.py`.

## 🧪 Testing

### Ejecutar Tests Completos
```bash
python test_ai_agreement_generation.py
```

### Tests Individuales
```python
# Test básico del generador
python -c "from ai_agreement_generator import AIAgreementGenerator; g = AIAgreementGenerator(); print('✅ Generador operativo')"

# Test de integración con agentes
python -c "from agent_core import AgentCore; a = AgentCore(); print('Herramientas:', [t.name for t in a.tools])"
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. Error de Conexión con Ollama
```
Error: No se pudo conectar con Ollama
Solución: Asegúrate de que Ollama esté ejecutándose: ollama serve
```

#### 2. Documento de Ejemplo No Encontrado
```
Error: Documento de ejemplo no existe
Solución: Verifica la ruta del archivo o usa el generador sin documento de ejemplo
```

#### 3. Error de Base de Datos
```
Error: No se pudieron obtener datos del caso
Solución: Verifica la conexión a la base de datos y que el caso exista
```

#### 4. Librerías Faltantes
```
Error: python-docx no disponible
Solución: pip install python-docx langchain langchain-community ollama
```

## 📈 Métricas y Monitoreo

### Métricas de Rendimiento
- **Tiempo de generación**: Promedio y distribución
- **Tasa de éxito**: Porcentaje de generaciones exitosas
- **Uso de recursos**: Memoria y CPU utilizados
- **Análisis de documentos**: Estadísticas de procesamiento

### Logging
El sistema registra todas las operaciones en logs detallados:
- Inicio y fin de operaciones
- Errores y excepciones
- Métricas de rendimiento
- Análisis de documentos procesados

## 🚀 Próximas Funcionalidades

### Plan de Desarrollo
- [ ] **Aprendizaje continuo**: El sistema aprenderá de documentos generados anteriormente
- [ ] **Múltiples idiomas**: Soporte para acuerdos en diferentes idiomas
- [ ] **Integración con APIs legales**: Conexión con bases de datos jurídicas
- [ ] **Análisis predictivo**: Sugerencias basadas en casos similares
- [ ] **Colaboración**: Múltiples usuarios pueden trabajar en el mismo documento

## 📞 Soporte y Contacto

Para soporte técnico o consultas sobre el sistema:

1. **Revisar logs**: Los archivos de log contienen información detallada sobre errores
2. **Ejecutar tests**: `python test_ai_agreement_generation.py` para diagnóstico
3. **Verificar dependencias**: Asegurarse de que todas las librerías estén instaladas
4. **Documentación**: Esta documentación se mantiene actualizada

## 📝 Licencia y Uso

Este sistema es parte del proyecto LPMS (Legal Practice Management System) y está diseñado para uso profesional en entornos legales argentinos.

---

**Última actualización**: Diciembre 2024
**Versión**: 1.0.0
**Autor**: Sistema de IA LPMS