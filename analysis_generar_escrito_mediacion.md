# Análisis Completo del Método `generar_escrito_mediacion`

## Resumen Ejecutivo

El método `generar_escrito_mediacion` de la clase `CaseManager` es una función compleja que genera documentos de acuerdo de mediación utilizando plantillas de Word (docx). Actualmente está fuertemente acoplado a la interfaz de usuario de Tkinter y requiere refactorización para separar la lógica de negocio de la UI.

## Ubicación y Estructura

- **Archivo**: `case_dialog_manager.py`
- **Clase**: `CaseManager`
- **Líneas**: 4493-5300+ (aproximadamente 800+ líneas)
- **Método principal**: `generar_escrito_mediacion(self, caso_id)`

## Flujo de Datos Completo

### 1. Validación Inicial
```python
def generar_escrito_mediacion(self, caso_id):
    # 0. Validación inicial de parámetros
    if not self._validate_initial_parameters(caso_id):
        return False
```

### 2. Validación de Dependencias del Sistema
```python
    # 1. Validación de dependencias del sistema
    if not self._validate_system_dependencies():
        return False
```

### 3. Recopilación de Datos del Caso
```python
    # 2. Recopilación y validación de datos del caso
    caso_data = self._collect_and_validate_case_data(caso_id)
    if not caso_data:
        return False
```

### 4. Recopilación de Datos de Partes
```python
    # 3. Recopilación y validación de partes/roles
    parties_data = self._collect_and_validate_parties_data(caso_id)
    if not parties_data:
        return False
```

### 5. **PUNTO CRÍTICO DE UI**: Obtención de Detalles del Acuerdo
```python
    # 4. Obtención de detalles del acuerdo del usuario
    agreement_details = self._collect_agreement_details(parties_data['lista_actores'])
    if not agreement_details:
        return False  # Usuario canceló
```

### 6. Procesamiento de Representantes
```python
    # 5. Procesamiento de representantes
    processed_parties = self._process_representatives(parties_data, caso_id)
    if not processed_parties:
        return False
```

### 7. Construcción del Contexto del Documento
```python
    # 6. Construcción del contexto del documento
    document_context = self._build_document_context(caso_data, processed_parties, agreement_details)
    if not document_context:
        return False
```

### 8. Generación del Documento
```python
    # 7. Generación y validación del documento
    document = self._generate_and_validate_document(document_context)
    if not document:
        return False
```

### 9. **PUNTO CRÍTICO DE UI**: Guardado del Documento
```python
    # 8. Guardado del documento
    if not self._save_document(document, caso_data):
        return False
```

## Métodos Auxiliares Identificados

### Métodos de Validación
1. `_validate_initial_parameters(caso_id)` - Valida parámetros de entrada
2. `_validate_system_dependencies()` - Valida dependencias del sistema
3. `_validate_mediation_dependencies()` - Valida librerías y plantillas
4. `_validate_document_context(context)` - Valida contexto del documento
5. `_validate_template_and_context(template_path, context)` - Valida plantilla

### Métodos de Recopilación de Datos
1. `_collect_and_validate_case_data(caso_id)` - Obtiene datos del caso de BD
2. `_collect_and_validate_parties_data(caso_id)` - Obtiene partes del caso de BD
3. `_collect_agreement_details(lista_actores)` - **DEPENDIENTE DE UI** - Abre diálogo
4. `_process_representatives(parties_data, caso_id)` - Procesa representantes
5. `_ensamblar_representantes(lista_base, todos_los_roles)` - Ensambla representantes

### Métodos de Construcción de Documento
1. `_build_document_context(caso_data, processed_parties, agreement_details)` - Construye contexto
2. `_prepare_safe_context(context, template_required_vars)` - Prepara contexto seguro
3. `_generate_and_validate_document(document_context)` - Genera documento
4. `_save_document(document, caso_data)` - **DEPENDIENTE DE UI** - Guarda con diálogo

### Métodos Auxiliares de Conversión
1. `_safe_number_to_words(number_str)` - Convierte números a letras
2. `_safe_period_to_words(period_str)` - Convierte períodos a letras
3. `_get_spanish_month()` - Obtiene mes en español
4. `_get_main_actor_name(lista_actores)` - Obtiene nombre del actor principal

### Métodos de Manejo de Errores
1. `_handle_critical_error(error, caso_id, operation_start_time)` - Maneja errores críticos
2. `_show_validation_errors(validation_result)` - Muestra errores de validación

### Métodos de Archivos
1. `_generate_safe_filename(caso_data)` - Genera nombre de archivo seguro
2. `_offer_to_open_document(ruta_guardado, file_size)` - **DEPENDIENTE DE UI** - Ofrece abrir
3. `_open_document(ruta_guardado)` - Abre documento generado

## Dependencias Externas Identificadas

### Librerías Python
1. `docxtpl` - Para plantillas de Word (DocxTemplate)
2. `num2words` - Para conversión de números a letras
3. `tkinter` - Para diálogos de UI (filedialog, messagebox)
4. `datetime` - Para fechas
5. `os` - Para operaciones de archivos
6. `locale` - Para formateo de fechas en español

### Módulos del Proyecto
1. `crm_database` (como `db`) - Para acceso a base de datos
2. `ErrorMessageManager` - Para manejo centralizado de errores
3. Funciones globales:
   - `convertir_numero_a_letras(numero_str)`
   - `convertir_plazo_a_letras(plazo_str)`

### Dependencias de UI (Tkinter)
1. `self.app_controller.root` - Ventana principal para diálogos
2. `filedialog.asksaveasfilename()` - Diálogo para guardar archivo
3. `messagebox.askyesno()` - Diálogos de confirmación
4. `messagebox.showerror()` - Diálogos de error
5. `_ask_agreement_details_dialog(actor_principal)` - **DIÁLOGO PERSONALIZADO**

## Estructura de Datos Crítica

### Entrada del Método
```python
caso_id: int  # ID del caso en la base de datos
```

### Datos del Caso (caso_data)
```python
{
    'id': int,
    'caratula': str,
    'numero_expediente': str,
    'anio_caratula': str,
    'juzgado': str,
    'jurisdiccion': str,
    'etapa_procesal': str,
    'notas': str,
    'cliente_id': int,
    'nombre_cliente': str
}
```

### Datos de Partes (parties_data)
```python
{
    'todos_los_roles': [
        {
            'rol_id': int,
            'caso_id': int,
            'contacto_id': int,
            'rol_principal': str,  # 'Actor', 'Demandado', etc.
            'rol_secundario': str,
            'representa_a_id': int,
            'datos_bancarios': str,
            'notas_del_rol': str,
            'nombre_completo': str,
            'es_persona_juridica': bool,
            'dni': str,
            'cuit': str,
            'domicilio_real': str,
            'domicilio_legal': str,
            'email': str,
            'telefono': str
        }
    ],
    'lista_actores': [...],  # Filtrado de todos_los_roles
    'lista_demandados': [...]  # Filtrado de todos_los_roles
}
```

### **CRÍTICO**: Detalles del Acuerdo (agreement_details)
```python
{
    'monto_compensacion_numeros': str,  # "150000.50"
    'plazo_pago_dias': str,            # "30"
    'banco_actor': str,                # "Banco Nación"
    'cbu_actor': str,                  # "1234567890123456789012"
    'alias_actor': str,                # "mi.alias.mp"
    'cuit_actor': str                  # "20-12345678-9"
}
```

### Contexto del Documento (document_context)
```python
{
    # Información básica del caso
    'NUMERO_EXPEDIENTE': str,
    'CARATULA': str,
    
    # Fechas del acuerdo
    'DIA_ACUERDO': int,
    'MES_ACUERDO': str,
    'AÑO_ACUERDO': int,
    'FECHA_COMPLETA': str,
    'FECHA_CORTA': str,
    
    # Partes del caso
    'ACTORES': list,
    'DEMANDADOS': list,
    'NOMBRE_ACTOR': str,
    
    # Montos y plazos de compensación
    'MONTO_COMPENSACION_NUMEROS': str,
    'MONTO_COMPENSACION_LETRAS': str,
    'PLAZO_PAGO_DIAS': str,
    'PLAZO_PAGO_LETRAS': str,
    
    # Datos bancarios del actor
    'BANCO_ACTOR': str,
    'CBU_ACTOR': str,
    'ALIAS_ACTOR': str,
    'CUIT_ACTOR': str,
    
    # Variables adicionales
    'MONTO_HONORARIOS_NUMEROS': str,
    'MONTO_HONORARIOS_LETRAS': str,
    'HONORARIOS_LETRAS': str,
    'PLAZO_PAGO_HONORARIOS_DIAS': str,
    'LUGAR_ACUERDO': str,
    'MEDIADOR': str,
    'CENTRO_MEDIACION': str,
    'OBSERVACIONES': str,
    'CLAUSULAS_ADICIONALES': str,
    'rep': dict
}
```

## Puntos Críticos de Acoplamiento con UI

### 1. Diálogo de Detalles del Acuerdo
- **Método**: `_collect_agreement_details(lista_actores)`
- **Llamada**: `self._ask_agreement_details_dialog(actor_principal)`
- **Problema**: Abre un diálogo de Tkinter para obtener datos del usuario
- **Solución**: Debe recibir estos datos como parámetro

### 2. Diálogo de Guardado de Archivo
- **Método**: `_save_document(document, caso_data)`
- **Llamada**: `filedialog.asksaveasfilename(...)`
- **Problema**: Abre diálogo para seleccionar ubicación de guardado
- **Solución**: Debe recibir la ruta como parámetro o usar ruta por defecto

### 3. Diálogos de Error y Confirmación
- **Métodos**: Múltiples métodos usan `messagebox`
- **Problema**: Muestran diálogos modales
- **Solución**: Deben retornar mensajes de error en lugar de mostrar diálogos

### 4. Dependencia del App Controller
- **Problema**: `self.app_controller.root` se usa para diálogos padre
- **Solución**: Hacer `app_controller` opcional en el constructor

## Archivos y Recursos Externos

### Plantillas Requeridas
- `plantillas/mediacion/acuerdo_base.docx` - Plantilla principal del documento

### Archivos de Configuración
- Ninguno identificado específicamente para este método

### Directorios de Salida
- El usuario selecciona la ubicación mediante diálogo (debe ser parametrizable)

## Manejo de Errores Actual

### Tipos de Error Manejados
1. **Errores de Validación**: Parámetros inválidos, datos faltantes
2. **Errores de Base de Datos**: Caso no encontrado, partes faltantes
3. **Errores de Dependencias**: Librerías faltantes, plantillas no encontradas
4. **Errores de Archivo**: Permisos, espacio en disco
5. **Errores de Plantilla**: Plantilla corrupta, variables faltantes

### Sistema de Manejo de Errores
- **Clase**: `ErrorMessageManager`
- **Métodos**:
  - `get_error_message(error_type, details)`
  - `show_error_dialog(parent, error_type, details)`
  - `log_error(error_type, details, technical_details)`

## Conclusiones para la Refactorización

### Métodos que Pueden Mantenerse Como Están
1. Todos los métodos de validación
2. Métodos de recopilación de datos de BD
3. Métodos de procesamiento de representantes
4. Métodos de construcción de contexto
5. Métodos de conversión de números/fechas
6. Métodos de generación de documento (excepto guardado)

### Métodos que Requieren Refactorización
1. **`_collect_agreement_details`** - Debe recibir datos como parámetro
2. **`_save_document`** - Debe usar ruta parametrizable
3. **Manejo de errores** - Debe retornar mensajes en lugar de mostrar diálogos

### Estructura de Refactorización Propuesta

#### Método de Lógica Pura
```python
def _generar_documento_con_datos(self, caso_id, details_acuerdo, ruta_guardado=None):
    """
    Genera documento de mediación usando datos proporcionados.
    
    Args:
        caso_id: ID del caso
        details_acuerdo: Diccionario con detalles del acuerdo
        ruta_guardado: Ruta opcional para guardar (si None, genera nombre automático)
        
    Returns:
        dict: {'success': bool, 'message': str, 'file_path': str}
    """
```

#### Método de Orquestación de UI (Refactorizado)
```python
def generar_escrito_mediacion(self, caso_id):
    """
    Orquesta la generación de acuerdo de mediación con interacción de usuario.
    
    Args:
        caso_id: ID del caso
        
    Returns:
        bool: True si exitoso, False si cancelado o error
    """
    # 1. Validaciones y recopilación de datos base
    # 2. Abrir diálogo para obtener detalles del acuerdo
    # 3. Llamar al método de lógica pura
    # 4. Manejar resultado y mostrar mensajes de UI
```

### Datos Requeridos para la Herramienta del Agente
```python
{
    "id_del_caso": int,
    "monto_compensacion": str,
    "plazo_pago_dias": str,
    "banco_actor": str,
    "cbu_actor": str,
    "alias_actor": str,
    "cuit_actor": str
}
```

## Estimación de Complejidad

- **Líneas de código afectadas**: ~800+ líneas
- **Métodos a refactorizar**: 3 métodos principales
- **Métodos a mantener**: ~20 métodos auxiliares
- **Nuevos métodos a crear**: 2 (lógica pura + herramienta del agente)
- **Riesgo de regresión**: Medio (muchos métodos auxiliares se mantienen)
- **Complejidad de testing**: Media (lógica de negocio compleja pero bien estructurada)