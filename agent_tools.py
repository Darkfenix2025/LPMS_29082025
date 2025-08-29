import logging
from langchain.tools import StructuredTool
from pydantic.v1 import BaseModel, Field
from typing import Type, Dict, Any, Optional, List, Tuple

# Try to import numexpr for mathematical calculations, fallback to eval if not available
try:
    import numexpr
    NUMEXPR_AVAILABLE = True
except ImportError:
    NUMEXPR_AVAILABLE = False
    print("Warning: numexpr no está disponible. Se utilizará eval() como alternativa para cálculos.")

from case_dialog_manager import CaseManager
import crm_database as db

# Import AI Agreement Generator
try:
    from ai_agreement_generator import AIAgreementGenerator
    AI_GENERATOR_AVAILABLE = True
except ImportError:
    AI_GENERATOR_AVAILABLE = False
    print("Warning: AI Agreement Generator not available")

# Configure comprehensive logging for agent tools
logger = logging.getLogger(__name__)
if not logger.handlers:
    # Create console handler with detailed formatting
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

# Performance tracking
performance_stats = {
    'total_calls': 0,
    'successful_calls': 0,
    'failed_calls': 0,
    'average_duration': 0.0,
    'last_call_time': None
}


class AgentToolsError(Exception):
    """Excepción personalizada para errores en herramientas del agente"""
    pass


def _format_error_message(error_type: str, message: str, context: Dict[str, Any] = None) -> str:
    """
    Formatea mensajes de error de manera consistente y descriptiva.

    Args:
        error_type: Tipo de error (validation, system, critical, etc.)
        message: Mensaje principal del error
        context: Información adicional de contexto

    Returns:
        str: Mensaje de error formateado
    """
    context = context or {}

    # Iconos para diferentes tipos de error
    error_icons = {
        'validation': '[ERROR]',
        'system': '⚠️',
        'critical': '🚨',
        'database': '💾',
        'network': '🌐',
        'file': '📁',
        'permission': '🔒'
    }

    icon = error_icons.get(error_type, '[ERROR]')

    # Construir mensaje base
    formatted_message = f"{icon} Error {error_type}: {message}"

    # Agregar contexto si está disponible
    if context:
        context_lines = []
        for key, value in context.items():
            if value is not None:
                context_lines.append(f"  • {key}: {value}")

        if context_lines:
            formatted_message += "\n" + "\n".join(context_lines)

    return formatted_message


def _format_success_message(message: str, details: Dict[str, Any] = None) -> str:
    """
    Formatea mensajes de éxito de manera consistente y descriptiva.

    Args:
        message: Mensaje principal de éxito
        details: Detalles adicionales del éxito

    Returns:
        str: Mensaje de éxito formateado
    """
    details = details or {}

    formatted_message = f"✅ {message}"

    # Agregar detalles si están disponibles
    if details:
        detail_lines = []
        for key, value in details.items():
            if value is not None:
                detail_lines.append(f"  📋 {key}: {value}")

        if detail_lines:
            formatted_message += "\n" + "\n".join(detail_lines)

    return formatted_message


def _validate_langchain_availability():
    """
    Valida que LangChain esté disponible para usar las herramientas.

    Raises:
        AgentToolsError: Si LangChain no está disponible
    """
    try:
        from langchain.tools import StructuredTool
    except ImportError:
        raise AgentToolsError(
            "LangChain no está disponible. Instale langchain para usar las herramientas del agente."
        )


def _create_case_manager() -> CaseManager:
    """
    Crea una instancia de CaseManager para uso independiente por agentes.

    Returns:
        CaseManager: Instancia configurada para uso sin app_controller

    Raises:
        AgentToolsError: Si no se puede crear la instancia
    """
    import time

    creation_start = time.time()

    try:
        logger.debug("Starting CaseManager creation")

        # Verificar que la clase CaseManager esté disponible
        if not hasattr(CaseManager, '__init__'):
            raise AgentToolsError("CaseManager is not properly imported or defined")

        # Crear CaseManager sin app_controller para uso independiente
        case_manager = CaseManager(app_controller=None)

        # Verificar que la instancia se creó correctamente
        if not isinstance(case_manager, CaseManager):
            raise AgentToolsError("Created instance is not of expected CaseManager type")

        # Verificar que el método requerido existe
        if not hasattr(case_manager, '_generar_documento_con_datos'):
            raise AgentToolsError("CaseManager does not have required _generar_documento_con_datos method")

        creation_duration = time.time() - creation_start
        logger.debug(f"CaseManager created successfully in {creation_duration:.3f}s")
        return case_manager

    except ImportError as e:
        creation_duration = time.time() - creation_start
        error_msg = f"Import error creating CaseManager after {creation_duration:.3f}s: {str(e)}"
        logger.error(error_msg)
        raise AgentToolsError(error_msg)

    except TypeError as e:
        creation_duration = time.time() - creation_start
        error_msg = f"Type error creating CaseManager after {creation_duration:.3f}s: {str(e)}"
        logger.error(error_msg)
        raise AgentToolsError(error_msg)

    except Exception as e:
        creation_duration = time.time() - creation_start
        error_msg = f"Unexpected error creating CaseManager after {creation_duration:.3f}s: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise AgentToolsError(error_msg)


def _validate_case_id(case_id: int) -> bool:
    """
    Valida que el ID del caso sea válido y exista en la base de datos.

    Args:
        case_id: ID del caso a validar

    Returns:
        bool: True si el caso existe, False en caso contrario
    """
    import time

    validation_start = time.time()

    try:
        logger.debug(f"Validating case ID existence: {case_id}")

        # Verificar que el case_id sea un entero positivo
        if not isinstance(case_id, int):
            logger.warning(f"case_id is not an integer: {type(case_id)}")
            return False

        if case_id <= 0:
            logger.warning(f"case_id is not positive: {case_id}")
            return False

        # Verificar que el caso exista en la base de datos
        try:
            # Intentar obtener datos básicos del caso usando la función existente del sistema
            caso_data = db.get_case_by_id(case_id)

            if not caso_data:
                logger.warning(f"Case {case_id} not found in database")
                return False

            # Verificar que el caso tenga datos mínimos requeridos
            if not isinstance(caso_data, dict):
                logger.warning(f"Case {case_id} data has invalid format: {type(caso_data)}")
                return False

            validation_duration = time.time() - validation_start
            logger.debug(f"Case {case_id} validated successfully in {validation_duration:.3f}s")
            return True

        except AttributeError:
            # Si la función get_case_by_id no existe, usar validación básica
            logger.warning("get_case_by_id function not available, using basic validation")
            # Por ahora retornar True para casos básicos, esto se mejorará cuando se tenga acceso completo a la BD
            return True

        except Exception as db_error:
            validation_duration = time.time() - validation_start
            logger.error(f"Database error validating case {case_id} after {validation_duration:.3f}s: {str(db_error)}")
            return False

    except Exception as e:
        validation_duration = time.time() - validation_start
        logger.error(f"Unexpected error validating case_id {case_id} after {validation_duration:.3f}s: {str(e)}", exc_info=True)
        return False


# --- Esquema de Argumentos para Generar Escrito ---
class GenerarEscritoArgs(BaseModel):
    id_del_caso: int = Field(description="ID numérico del caso.")
    monto_compensacion: str = Field(description="Monto total de la compensación.")
    plazo_pago_dias: str = Field(description="Plazo en días para el pago.")
    banco_actor: str = Field(description="Nombre oficial del banco del actor.")
    cbu_actor: str = Field(description="CBU de 22 dígitos de la cuenta del actor.")
    alias_actor: str = Field(description="Alias de la cuenta del actor.")
    cuit_actor: str = Field(description="CUIT o CUIL del actor, con guiones.")


# --- Esquema de Argumentos para Calculadora ---
class CalculadoraArgs(BaseModel):
    expresion: str = Field(description="Expresión matemática válida para ser evaluada. Ej: '15000 * 1.21' o '(100 + 250) / 2'.")


# --- Esquema de Argumentos para Solicitar Herramienta ---
class SolicitarHerramientaArgs(BaseModel):
    descripcion_necesidad: str = Field(description="Descripción técnica detallada de la nueva funcionalidad requerida, qué tarea debería realizar, qué datos necesita como entrada y qué resultado debería producir.")


# --- Esquema de Argumentos para Generar Acuerdo con IA ---
class GenerarAcuerdoIAArgs(BaseModel):
    id_del_caso: int = Field(description="ID numérico del caso.")
    monto_compensacion: str = Field(description="Monto total de la compensación.")
    plazo_pago_dias: str = Field(description="Plazo en días para el pago.")
    banco_actor: str = Field(description="Nombre oficial del banco del actor.")
    cbu_actor: str = Field(description="CBU de 22 dígitos de la cuenta del actor.")
    alias_actor: str = Field(description="Alias de la cuenta del actor.")
    cuit_actor: str = Field(description="CUIT o CUIL del actor, con guiones.")
    documento_ejemplo: Optional[str] = Field(default=None, description="Ruta opcional a un documento de ejemplo para analizar y usar como base.")


# --- Lógica de las Funciones ---
def _ejecutar_generacion_escrito(
    id_del_caso: int,
    monto_compensacion: str,
    plazo_pago_dias: str,
    banco_actor: str,
    cbu_actor: str,
    alias_actor: str,
    cuit_actor: str
) -> str:
    """
    Función principal que ejecuta la generación del escrito de mediación.
    Extraída y adaptada de la herramienta original.
    """
    import time
    import datetime
    import traceback

    # Initialize comprehensive monitoring
    operation_start_time = time.time()
    operation_id = f"agent_tool_{id_del_caso}_{int(operation_start_time)}"

    # Update global performance stats
    global performance_stats
    performance_stats['total_calls'] += 1
    performance_stats['last_call_time'] = datetime.datetime.now()

    # Phase timing tracking
    phase_times = {}

    try:
        # Log operation start with full context
        logger.info(f"[{operation_id}] Starting mediation agreement generation")
        logger.info(f"[{operation_id}] Input parameters: case_id={id_del_caso}, monto={monto_compensacion}, plazo={plazo_pago_dias}")
        logger.debug(f"[{operation_id}] Full parameters: banco={banco_actor}, cbu={cbu_actor[:4]}..., alias={alias_actor}, cuit={cuit_actor[:5]}...")

        # Validar disponibilidad de LangChain
        phase_start = time.time()
        _validate_langchain_availability()
        phase_times['langchain_validation'] = time.time() - phase_start

        # =====================================================================
        # FASE 1: VALIDACIÓN COMPREHENSIVA DE PARÁMETROS DE ENTRADA
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 1: Comprehensive parameter validation")

        validation_errors = []

        # 1.1 Validar tipo y valor del ID del caso
        try:
            if id_del_caso is None:
                validation_errors.append("id_del_caso es requerido y no puede ser None")
            elif not isinstance(id_del_caso, int):
                validation_errors.append(f"id_del_caso debe ser un entero, recibido: {type(id_del_caso).__name__}")
            elif id_del_caso <= 0:
                validation_errors.append(f"id_del_caso debe ser un entero positivo mayor a 0, recibido: {id_del_caso}")
        except Exception as e:
            validation_errors.append(f"Error validando id_del_caso: {str(e)}")

        # 1.2 Validar parámetros de string requeridos
        required_string_params = {
            'monto_compensacion': monto_compensacion,
            'plazo_pago_dias': plazo_pago_dias,
            'banco_actor': banco_actor,
            'cbu_actor': cbu_actor,
            'alias_actor': alias_actor,
            'cuit_actor': cuit_actor
        }

        for param_name, param_value in required_string_params.items():
            try:
                if param_value is None:
                    validation_errors.append(f"{param_name} es requerido y no puede ser None")
                elif not isinstance(param_value, str):
                    validation_errors.append(f"{param_name} debe ser un string, recibido: {type(param_value).__name__}")
                elif not param_value.strip():
                    validation_errors.append(f"{param_name} no puede estar vacío o contener solo espacios")
                elif len(param_value.strip()) > 500:  # Límite razonable de longitud
                    validation_errors.append(f"{param_name} excede la longitud máxima permitida (500 caracteres)")
            except Exception as e:
                validation_errors.append(f"Error validando {param_name}: {str(e)}")

        # 1.3 Validaciones específicas de formato y contenido

        # Validar monto de compensación
        if monto_compensacion and isinstance(monto_compensacion, str):
            try:
                # Limpiar el monto y validar que sea un número
                monto_limpio = monto_compensacion.strip().replace(',', '.')
                monto_float = float(monto_limpio)

                if monto_float < 0:
                    validation_errors.append("monto_compensacion no puede ser negativo")
                elif monto_float == 0:
                    validation_errors.append("monto_compensacion debe ser mayor a 0")
                elif monto_float > 999999999.99:  # Límite razonable
                    validation_errors.append("monto_compensacion excede el límite máximo permitido")

                # Validar formato decimal (máximo 2 decimales)
                if '.' in monto_limpio:
                    decimales = monto_limpio.split('.')[1]
                    if len(decimales) > 2:
                        validation_errors.append("monto_compensacion no puede tener más de 2 decimales")

            except (ValueError, TypeError) as e:
                validation_errors.append(f"monto_compensacion debe ser un número válido, error: {str(e)}")

        # Validar plazo de pago
        if plazo_pago_dias and isinstance(plazo_pago_dias, str):
            try:
                plazo_int = int(plazo_pago_dias.strip())
                if plazo_int <= 0:
                    validation_errors.append("plazo_pago_dias debe ser un número positivo")
                elif plazo_int > 3650:  # Máximo 10 años
                    validation_errors.append("plazo_pago_dias excede el límite máximo permitido (3650 días)")
            except (ValueError, TypeError) as e:
                validation_errors.append(f"plazo_pago_dias debe ser un número entero válido, error: {str(e)}")

        # Validar CBU
        if cbu_actor and isinstance(cbu_actor, str):
            try:
                # Limpiar CBU (remover espacios, guiones, etc.)
                cbu_limpio = ''.join(filter(str.isdigit, cbu_actor))

                if len(cbu_limpio) != 22:
                    validation_errors.append(f"cbu_actor debe tener exactamente 22 dígitos, encontrados: {len(cbu_limpio)}")
                elif not cbu_limpio.isdigit():
                    validation_errors.append("cbu_actor debe contener solo dígitos numéricos")

            except Exception as e:
                validation_errors.append(f"Error validando cbu_actor: {str(e)}")

        # Validar CUIT/CUIL
        if cuit_actor and isinstance(cuit_actor, str):
            try:
                # Limpiar CUIT (remover guiones y espacios)
                cuit_limpio = ''.join(filter(str.isdigit, cuit_actor))

                if len(cuit_limpio) != 11:
                    validation_errors.append(f"cuit_actor debe tener exactamente 11 dígitos, encontrados: {len(cuit_limpio)}")
                elif not cuit_limpio.isdigit():
                    validation_errors.append("cuit_actor debe contener solo dígitos numéricos")
                else:
                    # Validar formato básico de CUIT (primeros 2 dígitos)
                    prefijo = cuit_limpio[:2]
                    prefijos_validos = ['20', '23', '24', '27', '30', '33', '34']
                    if prefijo not in prefijos_validos:
                        validation_errors.append(f"cuit_actor tiene un prefijo inválido: {prefijo}")

            except Exception as e:
                validation_errors.append(f"Error validando cuit_actor: {str(e)}")

        # Validar alias bancario
        if alias_actor and isinstance(alias_actor, str):
            try:
                alias_limpio = alias_actor.strip()
                if len(alias_limpio) > 20:
                    validation_errors.append("alias_actor no puede exceder 20 caracteres")
                elif len(alias_limpio) < 6:
                    validation_errors.append("alias_actor debe tener al menos 6 caracteres")

                # Validar caracteres permitidos (letras, números, puntos)
                import re
                if not re.match(r'^[a-zA-Z0-9.]+$', alias_limpio):
                    validation_errors.append("alias_actor solo puede contener letras, números y puntos")

            except Exception as e:
                validation_errors.append(f"Error validando alias_actor: {str(e)}")

        # Validar nombre del banco
        if banco_actor and isinstance(banco_actor, str):
            try:
                banco_limpio = banco_actor.strip()
                if len(banco_limpio) < 5:
                    validation_errors.append("banco_actor debe tener al menos 5 caracteres")
                elif len(banco_limpio) > 100:
                    validation_errors.append("banco_actor no puede exceder 100 caracteres")

            except Exception as e:
                validation_errors.append(f"Error validando banco_actor: {str(e)}")

        phase_times['parameter_validation'] = time.time() - phase_start

        # Si hay errores de validación, retornar inmediatamente
        if validation_errors:
            performance_stats['failed_calls'] += 1
            total_duration = time.time() - operation_start_time
            error_msg = "Errores de validación encontrados:\n" + "\n".join([f"• {error}" for error in validation_errors])

            logger.error(f"[{operation_id}] Parameter validation failed after {phase_times['parameter_validation']:.3f}s")
            logger.error(f"[{operation_id}] Validation errors: {len(validation_errors)} errors found")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error de validación:\n{error_msg}"

        logger.info(f"[{operation_id}] Parameter validation completed successfully in {phase_times['parameter_validation']:.3f}s")

        # =====================================================================
        # FASE 2: VALIDACIÓN DE EXISTENCIA DEL CASO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 2: Case existence validation")

        try:
            if not _validate_case_id(id_del_caso):
                performance_stats['failed_calls'] += 1
                phase_times['case_validation'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                error_msg = f"El caso con ID {id_del_caso} no existe en la base de datos o no es accesible"
                logger.error(f"[{operation_id}] Case validation failed after {phase_times['case_validation']:.3f}s: {error_msg}")
                logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

                return f"[ERROR] Error de caso: {error_msg}"

            phase_times['case_validation'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Case validation completed successfully in {phase_times['case_validation']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['case_validation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error validando existencia del caso: {str(e)}"
            logger.error(f"[{operation_id}] Case validation error after {phase_times['case_validation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error del sistema: {error_msg}"

        # =====================================================================
        # FASE 3: INICIALIZACIÓN DEL CASE MANAGER
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 3: CaseManager initialization")

        try:
            case_manager = _create_case_manager()
            phase_times['case_manager_init'] = time.time() - phase_start
            logger.info(f"[{operation_id}] CaseManager initialized successfully in {phase_times['case_manager_init']:.3f}s")

        except AgentToolsError as e:
            performance_stats['failed_calls'] += 1
            phase_times['case_manager_init'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error inicializando CaseManager: {str(e)}"
            logger.error(f"[{operation_id}] CaseManager initialization failed after {phase_times['case_manager_init']:.3f}s: {error_msg}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error del sistema: {error_msg}"
        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['case_manager_init'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error inesperado inicializando CaseManager: {str(e)}"
            logger.error(f"[{operation_id}] CaseManager initialization critical error after {phase_times['case_manager_init']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error crítico: {error_msg}"

        # =====================================================================
        # FASE 4: PREPARACIÓN DE DATOS DEL ACUERDO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 4: Agreement data preparation")

        try:
            # Limpiar y preparar todos los datos
            details_acuerdo = {
                "monto_compensacion_numeros": monto_compensacion.strip(),
                "plazo_pago_dias": plazo_pago_dias.strip(),
                "banco_actor": banco_actor.strip(),
                "cbu_actor": cbu_actor.strip(),
                "alias_actor": alias_actor.strip(),
                "cuit_actor": cuit_actor.strip()
            }

            phase_times['data_preparation'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Agreement data prepared successfully in {phase_times['data_preparation']:.3f}s")
            logger.debug(f"[{operation_id}] Data keys: {list(details_acuerdo.keys())}")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['data_preparation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error preparando datos del acuerdo: {str(e)}"
            logger.error(f"[{operation_id}] Data preparation failed after {phase_times['data_preparation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error de procesamiento: {error_msg}"

        # =====================================================================
        # FASE 5: GENERACIÓN DEL DOCUMENTO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 5: Document generation")

        try:
            # Llamar al método de generación con manejo de errores específico
            result = case_manager._generar_documento_con_datos(id_del_caso, details_acuerdo)
            phase_times['document_generation'] = time.time() - phase_start

            if not isinstance(result, dict):
                performance_stats['failed_calls'] += 1
                total_duration = time.time() - operation_start_time

                error_msg = f"Respuesta inválida del generador de documentos: {type(result)}"
                logger.error(f"[{operation_id}] Document generation failed after {phase_times['document_generation']:.3f}s: {error_msg}")
                logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

                return f"[ERROR] Error interno: {error_msg}"

            # Validar estructura de la respuesta
            required_keys = ['success', 'error_message', 'error_type']
            missing_keys = [key for key in required_keys if key not in result]
            if missing_keys:
                performance_stats['failed_calls'] += 1
                total_duration = time.time() - operation_start_time

                error_msg = f"Respuesta incompleta del generador: faltan claves {missing_keys}"
                logger.error(f"[{operation_id}] Document generation failed after {phase_times['document_generation']:.3f}s: {error_msg}")
                logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

                return f"[ERROR] Error interno: {error_msg}"

            logger.info(f"[{operation_id}] Document generation completed in {phase_times['document_generation']:.3f}s")

            # Log performance metrics from CaseManager if available
            if 'performance_metrics' in result:
                case_manager_metrics = result['performance_metrics']
                logger.debug(f"[{operation_id}] CaseManager performance: {case_manager_metrics.get('total_duration', 'N/A'):.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['document_generation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error durante la generación del documento: {str(e)}"
            logger.error(f"[{operation_id}] Document generation critical error after {phase_times['document_generation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error crítico durante generación: {error_msg}"

        # =====================================================================
        # FASE 6: PROCESAMIENTO DEL RESULTADO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 6: Result processing")

        try:
            if result['success']:
                # Éxito - construir mensaje detallado
                performance_stats['successful_calls'] += 1
                phase_times['result_processing'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                # Update average duration
                performance_stats['average_duration'] = (
                    (performance_stats['average_duration'] * (performance_stats['successful_calls'] - 1) + total_duration)
                    / performance_stats['successful_calls']
                )

                filename = result.get('filename_suggestion', 'documento_generado')

                success_msg = (
                    f"✅ Documento de acuerdo de mediación generado exitosamente\n"
                    f"📋 Caso ID: {id_del_caso}\n"
                    f"📄 Nombre sugerido: {filename}\n"
                    f"💰 Monto: ${monto_compensacion}\n"
                    f"📅 Plazo: {plazo_pago_dias} días\n"
                    f"🏦 Banco: {banco_actor}\n"
                    f"⏱️  Completado en {total_duration:.3f}s\n"
                    f"ℹ️  El documento está listo para ser guardado o procesado"
                )

                # Log comprehensive success metrics
                logger.info(f"[{operation_id}] Operation completed successfully in {total_duration:.3f}s")
                logger.info(f"[{operation_id}] Performance breakdown:")
                for phase, duration in phase_times.items():
                    percentage = (duration / total_duration) * 100
                    logger.info(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

                logger.info(f"[{operation_id}] Global stats: {performance_stats['successful_calls']}/{performance_stats['total_calls']} successful, avg: {performance_stats['average_duration']:.3f}s")

                return success_msg

            else:
                # Error - construir mensaje descriptivo
                performance_stats['failed_calls'] += 1
                phase_times['result_processing'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                error_message = result.get('error_message', 'Error desconocido')
                error_type = result.get('error_type', 'unknown')

                # Mapear tipos de error a mensajes más descriptivos
                error_type_descriptions = {
                    'missing_case': 'El caso no fue encontrado en la base de datos',
                    'empty_caratula': 'El caso no tiene carátula definida',
                    'no_parties': 'No se encontraron partes asociadas al caso',
                    'no_actors': 'No se encontraron actores en el caso',
                    'no_defendants': 'No se encontraron demandados en el caso',
                    'missing_dependencies': 'Faltan dependencias del sistema',
                    'template_error': 'Error en la plantilla del documento',
                    'validation_error': 'Error de validación de datos',
                    'database_error': 'Error de acceso a la base de datos',
                    'file_error': 'Error de acceso a archivos',
                    'unexpected_error': 'Error inesperado del sistema'
                }

                error_description = error_type_descriptions.get(error_type, 'Error no categorizado')

                error_msg = (
                    f"[ERROR] Error generando documento para caso {id_del_caso}\n"
                    f"🔍 Tipo: {error_description}\n"
                    f"📝 Detalle: {error_message}\n"
                    f"⏱️  Falló después de {total_duration:.3f}s\n"
                    f"💡 Sugerencia: Verifique los datos del caso y vuelva a intentar"
                )

                # Log comprehensive error metrics
                logger.error(f"[{operation_id}] Operation failed after {total_duration:.3f}s")
                logger.error(f"[{operation_id}] Error type: {error_type}, message: {error_message}")
                logger.info(f"[{operation_id}] Performance breakdown before failure:")
                for phase, duration in phase_times.items():
                    percentage = (duration / total_duration) * 100 if total_duration > 0 else 0
                    logger.info(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

                logger.info(f"[{operation_id}] Global stats: {performance_stats['failed_calls']}/{performance_stats['total_calls']} failed")

                return error_msg

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['result_processing'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error procesando resultado de la generación: {str(e)}"
            logger.error(f"[{operation_id}] Result processing critical error after {total_duration:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error crítico procesando resultado: {error_msg}"

    except Exception as e:
        # Manejo de errores críticos no capturados en niveles anteriores
        performance_stats['failed_calls'] += 1
        total_duration = time.time() - operation_start_time

        error_msg = f"Error crítico inesperado en la herramienta: {str(e)}"
        logger.error(f"[{operation_id}] Critical unexpected error after {total_duration:.3f}s: {error_msg}")
        logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")

        # Log partial performance metrics if available
        if phase_times:
            logger.debug(f"[{operation_id}] Partial performance before critical failure:")
            for phase, duration in phase_times.items():
                percentage = (duration / total_duration) * 100 if total_duration > 0 else 0
                logger.debug(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

        logger.info(f"[{operation_id}] Global stats: {performance_stats['failed_calls']}/{performance_stats['total_calls']} failed")

        return f"[ERROR] Error crítico: {error_msg} (falló después de {total_duration:.3f}s)"


def _ejecutar_calculo(expresion: str) -> str:
    """
    Ejecuta cálculos matemáticos utilizando numexpr si está disponible,
    o eval() como alternativa con medidas de seguridad.
    """
    try:
        expresion = expresion.strip()

        if NUMEXPR_AVAILABLE:
            # Usar numexpr para cálculos más eficientes y seguros
            resultado = numexpr.evaluate(expresion).item()
        else:
            # Fallback usando eval() con restricciones de seguridad
            # Solo permitir operaciones matemáticas básicas
            import re
            if not re.match(r'^[0-9+\-*/().\s]+$', expresion):
                return f"Error: La expresión contiene caracteres no permitidos. Solo se permiten números y operadores matemáticos básicos (+, -, *, /, (), .)."

            # Evaluar con restricciones
            resultado = eval(expresion, {"__builtins__": {}}, {})

        return f"El resultado del cálculo '{expresion}' es: {resultado}"

    except ZeroDivisionError:
        return f"Error: División por cero en la expresión '{expresion}'"
    except (ValueError, TypeError) as e:
        return f"Error de tipo en la expresión '{expresion}': {str(e)}"
    except SyntaxError:
        return f"Error de sintaxis en la expresión '{expresion}'. Verifica que sea una expresión matemática válida."
    except Exception as e:
        return f"Error al evaluar la expresión '{expresion}': {str(e)}"


def _registrar_solicitud_herramienta(descripcion_necesidad: str) -> str:
    log_file = "tool_requests.log"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"--- NUEVA SOLICITUD DE HERRAMIENTA ---\n{descripcion_necesidad}\n----------------------------------------\n\n")
        return "He registrado tu solicitud. El equipo de desarrollo ha sido notificado."
    except Exception as e:
        return f"No pude registrar la solicitud debido a un error: {e}"


def _ejecutar_generacion_acuerdo_ia(
    id_del_caso: int,
    monto_compensacion: str,
    plazo_pago_dias: str,
    banco_actor: str,
    cbu_actor: str,
    alias_actor: str,
    cuit_actor: str,
    documento_ejemplo: Optional[str] = None
) -> str:
    """
    Función principal que ejecuta la generación de acuerdos de mediación usando IA y documentos de ejemplo.
    """
    import time
    import datetime
    import traceback

    # Initialize comprehensive monitoring
    operation_start_time = time.time()
    operation_id = f"ai_agreement_tool_{id_del_caso}_{int(operation_start_time)}"

    # Update global performance stats
    global performance_stats
    performance_stats['total_calls'] += 1
    performance_stats['last_call_time'] = datetime.datetime.now()

    try:
        logger.info(f"[{operation_id}] Starting AI-powered agreement generation")
        logger.info(f"[{operation_id}] Input parameters: case_id={id_del_caso}, monto={monto_compensacion}, plazo={plazo_pago_dias}")
        logger.debug(f"[{operation_id}] Full parameters: banco={banco_actor}, cbu={cbu_actor[:4]}..., alias={alias_actor}, cuit={cuit_actor[:5]}...")

        # Validar disponibilidad del generador de IA
        if not AI_GENERATOR_AVAILABLE:
            performance_stats['failed_calls'] += 1
            total_duration = time.time() - operation_start_time

            error_msg = "El generador de acuerdos con IA no está disponible. Verifique que ai_agreement_generator.py esté instalado correctamente."
            logger.error(f"[{operation_id}] AI Generator not available after {total_duration:.3f}s")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error del sistema: {error_msg}"

        # =====================================================================
        # FASE 1: VALIDACIÓN COMPREHENSIVA DE PARÁMETROS DE ENTRADA
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 1: Comprehensive parameter validation")

        validation_errors = []

        # 1.1 Validar tipo y valor del ID del caso
        try:
            if id_del_caso is None:
                validation_errors.append("id_del_caso es requerido y no puede ser None")
            elif not isinstance(id_del_caso, int):
                validation_errors.append(f"id_del_caso debe ser un entero, recibido: {type(id_del_caso).__name__}")
            elif id_del_caso <= 0:
                validation_errors.append(f"id_del_caso debe ser un entero positivo mayor a 0, recibido: {id_del_caso}")
        except Exception as e:
            validation_errors.append(f"Error validando id_del_caso: {str(e)}")

        # 1.2 Validar parámetros de string requeridos
        required_string_params = {
            'monto_compensacion': monto_compensacion,
            'plazo_pago_dias': plazo_pago_dias,
            'banco_actor': banco_actor,
            'cbu_actor': cbu_actor,
            'alias_actor': alias_actor,
            'cuit_actor': cuit_actor
        }

        for param_name, param_value in required_string_params.items():
            try:
                if param_value is None:
                    validation_errors.append(f"{param_name} es requerido y no puede ser None")
                elif not isinstance(param_value, str):
                    validation_errors.append(f"{param_name} debe ser un string, recibido: {type(param_value).__name__}")
                elif not param_value.strip():
                    validation_errors.append(f"{param_name} no puede estar vacío o contener solo espacios")
                elif len(param_value.strip()) > 500:  # Límite razonable de longitud
                    validation_errors.append(f"{param_name} excede la longitud máxima permitida (500 caracteres)")
            except Exception as e:
                validation_errors.append(f"Error validando {param_name}: {str(e)}")

        # 1.3 Validaciones específicas de formato y contenido
        # (Mismas validaciones que la herramienta original)

        # Validar monto de compensación
        if monto_compensacion and isinstance(monto_compensacion, str):
            try:
                monto_limpio = monto_compensacion.strip().replace(',', '.')
                monto_float = float(monto_limpio)

                if monto_float < 0:
                    validation_errors.append("monto_compensacion no puede ser negativo")
                elif monto_float == 0:
                    validation_errors.append("monto_compensacion debe ser mayor a 0")
                elif monto_float > 999999999.99:
                    validation_errors.append("monto_compensacion excede el límite máximo permitido")

                if '.' in monto_limpio:
                    decimales = monto_limpio.split('.')[1]
                    if len(decimales) > 2:
                        validation_errors.append("monto_compensacion no puede tener más de 2 decimales")

            except (ValueError, TypeError) as e:
                validation_errors.append(f"monto_compensacion debe ser un número válido, error: {str(e)}")

        # Validar plazo de pago
        if plazo_pago_dias and isinstance(plazo_pago_dias, str):
            try:
                plazo_int = int(plazo_pago_dias.strip())
                if plazo_int <= 0:
                    validation_errors.append("plazo_pago_dias debe ser un número positivo")
                elif plazo_int > 3650:
                    validation_errors.append("plazo_pago_dias excede el límite máximo permitido (3650 días)")
            except (ValueError, TypeError) as e:
                validation_errors.append(f"plazo_pago_dias debe ser un número entero válido, error: {str(e)}")

        # Validar CBU
        if cbu_actor and isinstance(cbu_actor, str):
            try:
                cbu_limpio = ''.join(filter(str.isdigit, cbu_actor))

                if len(cbu_limpio) != 22:
                    validation_errors.append(f"cbu_actor debe tener exactamente 22 dígitos, encontrados: {len(cbu_limpio)}")
                elif not cbu_limpio.isdigit():
                    validation_errors.append("cbu_actor debe contener solo dígitos numéricos")

            except Exception as e:
                validation_errors.append(f"Error validando cbu_actor: {str(e)}")

        # Validar CUIT/CUIL
        if cuit_actor and isinstance(cuit_actor, str):
            try:
                cuit_limpio = ''.join(filter(str.isdigit, cuit_actor))

                if len(cuit_limpio) != 11:
                    validation_errors.append(f"cuit_actor debe tener exactamente 11 dígitos, encontrados: {len(cuit_limpio)}")
                elif not cuit_limpio.isdigit():
                    validation_errors.append("cuit_actor debe contener solo dígitos numéricos")
                else:
                    prefijo = cuit_limpio[:2]
                    prefijos_validos = ['20', '23', '24', '27', '30', '33', '34']
                    if prefijo not in prefijos_validos:
                        validation_errors.append(f"cuit_actor tiene un prefijo inválido: {prefijo}")

            except Exception as e:
                validation_errors.append(f"Error validando cuit_actor: {str(e)}")

        # Validar alias bancario
        if alias_actor and isinstance(alias_actor, str):
            try:
                alias_limpio = alias_actor.strip()
                if len(alias_limpio) > 20:
                    validation_errors.append("alias_actor no puede exceder 20 caracteres")
                elif len(alias_limpio) < 6:
                    validation_errors.append("alias_actor debe tener al menos 6 caracteres")

                import re
                if not re.match(r'^[a-zA-Z0-9.]+$', alias_limpio):
                    validation_errors.append("alias_actor solo puede contener letras, números y puntos")

            except Exception as e:
                validation_errors.append(f"Error validando alias_actor: {str(e)}")

        # Validar nombre del banco
        if banco_actor and isinstance(banco_actor, str):
            try:
                banco_limpio = banco_actor.strip()
                if len(banco_limpio) < 5:
                    validation_errors.append("banco_actor debe tener al menos 5 caracteres")
                elif len(banco_limpio) > 100:
                    validation_errors.append("banco_actor no puede exceder 100 caracteres")

            except Exception as e:
                validation_errors.append(f"Error validando banco_actor: {str(e)}")

        # Validar documento de ejemplo si se proporciona
        if documento_ejemplo and isinstance(documento_ejemplo, str):
            try:
                if not documento_ejemplo.strip():
                    documento_ejemplo = None  # Tratar como None si está vacío
                elif not os.path.exists(documento_ejemplo.strip()):
                    validation_errors.append(f"El documento de ejemplo no existe: {documento_ejemplo}")
                elif not documento_ejemplo.strip().endswith(('.docx', '.doc')):
                    validation_errors.append("El documento de ejemplo debe ser un archivo .docx o .doc")
            except Exception as e:
                validation_errors.append(f"Error validando documento_ejemplo: {str(e)}")

        phase_times['parameter_validation'] = time.time() - phase_start

        # Si hay errores de validación, retornar inmediatamente
        if validation_errors:
            performance_stats['failed_calls'] += 1
            total_duration = time.time() - operation_start_time
            error_msg = "Errores de validación encontrados:\n" + "\n".join([f"• {error}" for error in validation_errors])

            logger.error(f"[{operation_id}] Parameter validation failed after {phase_times['parameter_validation']:.3f}s")
            logger.error(f"[{operation_id}] Validation errors: {len(validation_errors)} errors found")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error de validación:\n{error_msg}"

        logger.info(f"[{operation_id}] Parameter validation completed successfully in {phase_times['parameter_validation']:.3f}s")

        # =====================================================================
        # FASE 2: VALIDACIÓN DE EXISTENCIA DEL CASO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 2: Case existence validation")

        try:
            if not _validate_case_id(id_del_caso):
                performance_stats['failed_calls'] += 1
                phase_times['case_validation'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                error_msg = f"El caso con ID {id_del_caso} no existe en la base de datos o no es accesible"
                logger.error(f"[{operation_id}] Case validation failed after {phase_times['case_validation']:.3f}s: {error_msg}")
                logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

                return f"[ERROR] Error de caso: {error_msg}"

            phase_times['case_validation'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Case validation completed successfully in {phase_times['case_validation']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['case_validation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error validando existencia del caso: {str(e)}"
            logger.error(f"[{operation_id}] Case validation error after {phase_times['case_validation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error del sistema: {error_msg}"

        # =====================================================================
        # FASE 3: INICIALIZACIÓN DEL GENERADOR DE ACUERDOS CON IA
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 3: AI Agreement Generator initialization")

        try:
            ai_generator = AIAgreementGenerator(example_document_path=documento_ejemplo)
            phase_times['ai_generator_init'] = time.time() - phase_start
            logger.info(f"[{operation_id}] AI Agreement Generator initialized successfully in {phase_times['ai_generator_init']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['ai_generator_init'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error inicializando generador de acuerdos con IA: {str(e)}"
            logger.error(f"[{operation_id}] AI Generator initialization failed after {phase_times['ai_generator_init']:.3f}s: {error_msg}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error del sistema: {error_msg}"

        # =====================================================================
        # FASE 4: PREPARACIÓN DE DATOS DEL ACUERDO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 4: Agreement data preparation")

        try:
            details_acuerdo = {
                "monto_compensacion_numeros": monto_compensacion.strip(),
                "plazo_pago_dias": plazo_pago_dias.strip(),
                "banco_actor": banco_actor.strip(),
                "cbu_actor": cbu_actor.strip(),
                "alias_actor": alias_actor.strip(),
                "cuit_actor": cuit_actor.strip()
            }

            phase_times['data_preparation'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Agreement data prepared successfully in {phase_times['data_preparation']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['data_preparation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error preparando datos del acuerdo: {str(e)}"
            logger.error(f"[{operation_id}] Data preparation failed after {phase_times['data_preparation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error de procesamiento: {error_msg}"

        # =====================================================================
        # FASE 5: GENERACIÓN DEL ACUERDO CON IA
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 5: AI-powered agreement generation")

        try:
            result = ai_generator.generate_agreement_with_ai(
                case_id=id_del_caso,
                agreement_details=details_acuerdo,
                example_document_path=documento_ejemplo
            )

            phase_times['ai_generation'] = time.time() - phase_start

            if not isinstance(result, dict):
                performance_stats['failed_calls'] += 1
                total_duration = time.time() - operation_start_time

                error_msg = f"Respuesta inválida del generador de IA: {type(result)}"
                logger.error(f"[{operation_id}] AI generation failed after {phase_times['ai_generation']:.3f}s: {error_msg}")
                logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

                return f"[ERROR] Error interno: {error_msg}"

            logger.info(f"[{operation_id}] AI agreement generation completed in {phase_times['ai_generation']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['ai_generation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error durante la generación del acuerdo con IA: {str(e)}"
            logger.error(f"[{operation_id}] AI generation critical error after {phase_times['ai_generation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error crítico durante generación con IA: {error_msg}"

        # =====================================================================
        # FASE 6: PROCESAMIENTO DEL RESULTADO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 6: Result processing")

        try:
            if result['success']:
                performance_stats['successful_calls'] += 1
                phase_times['result_processing'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                performance_stats['average_duration'] = (
                    (performance_stats['average_duration'] * (performance_stats['successful_calls'] - 1) + total_duration)
                    / performance_stats['successful_calls']
                )

                filename = result.get('filename', 'acuerdo_generado_con_ia.docx')

                success_msg = (
                    f"✅ Acuerdo de mediación generado exitosamente con IA\n"
                    f"📋 Caso ID: {id_del_caso}\n"
                    f"📄 Nombre del archivo: {filename}\n"
                    f"💰 Monto: ${monto_compensacion}\n"
                    f"📅 Plazo: {plazo_pago_dias} días\n"
                    f"🏦 Banco: {banco_actor}\n"
                    f"🤖 Generado con IA usando análisis de documento de ejemplo\n"
                    f"⏱️  Completado en {total_duration:.3f}s\n"
                    f"ℹ️  El documento está listo para ser revisado y guardado"
                )

                logger.info(f"[{operation_id}] Operation completed successfully in {total_duration:.3f}s")
                logger.info(f"[{operation_id}] Performance breakdown:")
                for phase, duration in phase_times.items():
                    percentage = (duration / total_duration) * 100
                    logger.info(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

                logger.info(f"[{operation_id}] Global stats: {performance_stats['successful_calls']}/{performance_stats['total_calls']} successful, avg: {performance_stats['average_duration']:.3f}s")

                return success_msg

            else:
                performance_stats['failed_calls'] += 1
                phase_times['result_processing'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                error_message = result.get('error_message', 'Error desconocido')
                error_type = result.get('error_type', 'unknown')

                error_type_descriptions = {
                    'case_data_error': 'No se pudieron obtener los datos del caso',
                    'content_generation_error': 'Error generando contenido con IA',
                    'document_creation_error': 'Error creando el documento Word',
                    'internal_error': 'Error interno del sistema'
                }

                error_description = error_type_descriptions.get(error_type, 'Error no categorizado')

                error_msg = (
                    f"[ERROR] Error generando acuerdo con IA para caso {id_del_caso}\n"
                    f"🔍 Tipo: {error_description}\n"
                    f"📝 Detalle: {error_message}\n"
                    f"⏱️  Falló después de {total_duration:.3f}s\n"
                    f"💡 Sugerencia: Verifique los datos del caso y el documento de ejemplo"
                )

                logger.error(f"[{operation_id}] Operation failed after {total_duration:.3f}s")
                logger.error(f"[{operation_id}] Error type: {error_type}, message: {error_message}")
                logger.info(f"[{operation_id}] Performance breakdown before failure:")
                for phase, duration in phase_times.items():
                    percentage = (duration / total_duration) * 100 if total_duration > 0 else 0
                    logger.info(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

                logger.info(f"[{operation_id}] Global stats: {performance_stats['failed_calls']}/{performance_stats['total_calls']} failed")

                return error_msg

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['result_processing'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error procesando resultado de la generación con IA: {str(e)}"
            logger.error(f"[{operation_id}] Result processing critical error after {total_duration:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error crítico procesando resultado con IA: {error_msg}"

    except Exception as e:
        performance_stats['failed_calls'] += 1
        total_duration = time.time() - operation_start_time

        error_msg = f"Error crítico inesperado en la herramienta de IA: {str(e)}"
        logger.error(f"[{operation_id}] Critical unexpected error after {total_duration:.3f}s: {error_msg}")
        logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")

        if 'phase_times' in locals():
            logger.debug(f"[{operation_id}] Partial performance before critical failure:")
            for phase, duration in phase_times.items():
                percentage = (duration / total_duration) * 100 if total_duration > 0 else 0
                logger.debug(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

        logger.info(f"[{operation_id}] Global stats: {performance_stats['failed_calls']}/{performance_stats['total_calls']} failed")

        return f"[ERROR] Error crítico: {error_msg} (falló después de {total_duration:.3f}s)"


# --- Creación de las Herramientas Estructuradas ---
generar_escrito_mediacion_tool = StructuredTool.from_function(
    func=_ejecutar_generacion_escrito,
    name="generar_escrito_mediacion_tool",
    description="Genera un documento de Acuerdo de Mediación para un caso específico del sistema LPMS. Esta herramienta permite crear automáticamente documentos legales de acuerdo de mediación sin necesidad de interacción manual con la interfaz de usuario.",
    args_schema=GenerarEscritoArgs
)

calculadora_matematica_tool = StructuredTool.from_function(
    func=_ejecutar_calculo,
    name="calculadora_matematica_tool",
    description="Úsala para realizar cualquier operación aritmética precisa. No intentes hacer cálculos por tu cuenta.",
    args_schema=CalculadoraArgs
)

solicitar_nueva_herramienta_tool = StructuredTool.from_function(
    func=_registrar_solicitud_herramienta,
    name="solicitar_nueva_herramienta_tool",
    description="Úsala como último recurso si no puedes cumplir la petición del usuario con las herramientas existentes.",
    args_schema=SolicitarHerramientaArgs
)

# --- Esquema de Argumentos para Generar Acuerdo con Template ---
class GenerarAcuerdoTemplateArgs(BaseModel):
    id_del_caso: int = Field(description="ID numérico del caso.")
    monto_compensacion: str = Field(description="Monto total de la compensación.")
    plazo_pago_dias: str = Field(description="Plazo en días para el pago.")
    banco_actor: str = Field(description="Nombre oficial del banco del actor.")
    cbu_actor: str = Field(description="CBU de 22 dígitos de la cuenta del actor.")
    alias_actor: str = Field(description="Alias de la cuenta del actor.")
    cuit_actor: str = Field(description="CUIT o CUIL del actor, con guiones.")


def _ejecutar_generacion_acuerdo_template(
    id_del_caso: int,
    monto_compensacion: str,
    plazo_pago_dias: str,
    banco_actor: str,
    cbu_actor: str,
    alias_actor: str,
    cuit_actor: str
) -> str:
    """
    Función principal que ejecuta la generación de acuerdos usando templates de texto.
    """
    import time
    import datetime
    import traceback

    # Initialize comprehensive monitoring
    operation_start_time = time.time()
    operation_id = f"template_agreement_tool_{id_del_caso}_{int(operation_start_time)}"

    # Initialize phase timing tracking
    phase_times = {}

    # Update global performance stats
    global performance_stats
    performance_stats['total_calls'] += 1
    performance_stats['last_call_time'] = datetime.datetime.now()

    try:
        logger.info(f"[{operation_id}] Starting template-based agreement generation")
        logger.info(f"[{operation_id}] Input parameters: case_id={id_del_caso}, monto={monto_compensacion}, plazo={plazo_pago_dias}")

        # =====================================================================
        # FASE 1: VALIDACIÓN COMPREHENSIVA DE PARÁMETROS DE ENTRADA
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 1: Comprehensive parameter validation")

        validation_errors = []

        # 1.1 Validar tipo y valor del ID del caso
        try:
            if id_del_caso is None:
                validation_errors.append("id_del_caso es requerido y no puede ser None")
            elif not isinstance(id_del_caso, int):
                validation_errors.append(f"id_del_caso debe ser un entero, recibido: {type(id_del_caso).__name__}")
            elif id_del_caso <= 0:
                validation_errors.append(f"id_del_caso debe ser un entero positivo mayor a 0, recibido: {id_del_caso}")
        except Exception as e:
            validation_errors.append(f"Error validando id_del_caso: {str(e)}")

        # 1.2 Validar parámetros de string requeridos
        required_string_params = {
            'monto_compensacion': monto_compensacion,
            'plazo_pago_dias': plazo_pago_dias,
            'banco_actor': banco_actor,
            'cbu_actor': cbu_actor,
            'alias_actor': alias_actor,
            'cuit_actor': cuit_actor
        }

        for param_name, param_value in required_string_params.items():
            try:
                if param_value is None:
                    validation_errors.append(f"{param_name} es requerido y no puede ser None")
                elif not isinstance(param_value, str):
                    validation_errors.append(f"{param_name} debe ser un string, recibido: {type(param_value).__name__}")
                elif not param_value.strip():
                    validation_errors.append(f"{param_name} no puede estar vacío o contener solo espacios")
                elif len(param_value.strip()) > 500:  # Límite razonable de longitud
                    validation_errors.append(f"{param_name} excede la longitud máxima permitida (500 caracteres)")
            except Exception as e:
                validation_errors.append(f"Error validando {param_name}: {str(e)}")

        # 1.3 Validaciones específicas de formato y contenido
        # (Mismas validaciones que las otras herramientas)

        # Validar monto de compensación
        if monto_compensacion and isinstance(monto_compensacion, str):
            try:
                monto_limpio = monto_compensacion.strip().replace(',', '.')
                monto_float = float(monto_limpio)

                if monto_float < 0:
                    validation_errors.append("monto_compensacion no puede ser negativo")
                elif monto_float == 0:
                    validation_errors.append("monto_compensacion debe ser mayor a 0")
                elif monto_float > 999999999.99:
                    validation_errors.append("monto_compensacion excede el límite máximo permitido")

                if '.' in monto_limpio:
                    decimales = monto_limpio.split('.')[1]
                    if len(decimales) > 2:
                        validation_errors.append("monto_compensacion no puede tener más de 2 decimales")

            except (ValueError, TypeError) as e:
                validation_errors.append(f"monto_compensacion debe ser un número válido, error: {str(e)}")

        # Validar plazo de pago
        if plazo_pago_dias and isinstance(plazo_pago_dias, str):
            try:
                plazo_int = int(plazo_pago_dias.strip())
                if plazo_int <= 0:
                    validation_errors.append("plazo_pago_dias debe ser un número positivo")
                elif plazo_int > 3650:
                    validation_errors.append("plazo_pago_dias excede el límite máximo permitido (3650 días)")
            except (ValueError, TypeError) as e:
                validation_errors.append(f"plazo_pago_dias debe ser un número entero válido, error: {str(e)}")

        # Validar CBU
        if cbu_actor and isinstance(cbu_actor, str):
            try:
                cbu_limpio = ''.join(filter(str.isdigit, cbu_actor))

                if len(cbu_limpio) != 22:
                    validation_errors.append(f"cbu_actor debe tener exactamente 22 dígitos, encontrados: {len(cbu_limpio)}")
                elif not cbu_limpio.isdigit():
                    validation_errors.append("cbu_actor debe contener solo dígitos numéricos")

            except Exception as e:
                validation_errors.append(f"Error validando cbu_actor: {str(e)}")

        # Validar CUIT/CUIL
        if cuit_actor and isinstance(cuit_actor, str):
            try:
                cuit_limpio = ''.join(filter(str.isdigit, cuit_actor))

                if len(cuit_limpio) != 11:
                    validation_errors.append(f"cuit_actor debe tener exactamente 11 dígitos, encontrados: {len(cuit_limpio)}")
                elif not cuit_limpio.isdigit():
                    validation_errors.append("cuit_actor debe contener solo dígitos numéricos")
                else:
                    prefijo = cuit_limpio[:2]
                    prefijos_validos = ['20', '23', '24', '27', '30', '33', '34']
                    if prefijo not in prefijos_validos:
                        validation_errors.append(f"cuit_actor tiene un prefijo inválido: {prefijo}")

            except Exception as e:
                validation_errors.append(f"Error validando cuit_actor: {str(e)}")

        # Validar alias bancario
        if alias_actor and isinstance(alias_actor, str):
            try:
                alias_limpio = alias_actor.strip()
                if len(alias_limpio) > 20:
                    validation_errors.append("alias_actor no puede exceder 20 caracteres")
                elif len(alias_limpio) < 6:
                    validation_errors.append("alias_actor debe tener al menos 6 caracteres")

                import re
                if not re.match(r'^[a-zA-Z0-9.]+$', alias_limpio):
                    validation_errors.append("alias_actor solo puede contener letras, números y puntos")

            except Exception as e:
                validation_errors.append(f"Error validando alias_actor: {str(e)}")

        # Validar nombre del banco
        if banco_actor and isinstance(banco_actor, str):
            try:
                banco_limpio = banco_actor.strip()
                if len(banco_limpio) < 5:
                    validation_errors.append("banco_actor debe tener al menos 5 caracteres")
                elif len(banco_limpio) > 100:
                    validation_errors.append("banco_actor no puede exceder 100 caracteres")

            except Exception as e:
                validation_errors.append(f"Error validando banco_actor: {str(e)}")

        phase_times['parameter_validation'] = time.time() - phase_start

        # Si hay errores de validación, retornar inmediatamente
        if validation_errors:
            performance_stats['failed_calls'] += 1
            total_duration = time.time() - operation_start_time
            error_msg = "Errores de validación encontrados:\n" + "\n".join([f"• {error}" for error in validation_errors])

            logger.error(f"[{operation_id}] Parameter validation failed after {phase_times['parameter_validation']:.3f}s")
            logger.error(f"[{operation_id}] Validation errors: {len(validation_errors)} errors found")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error de validación:\n{error_msg}"

        logger.info(f"[{operation_id}] Parameter validation completed successfully in {phase_times['parameter_validation']:.3f}s")

        # =====================================================================
        # FASE 2: VALIDACIÓN DE EXISTENCIA DEL CASO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 2: Case existence validation")

        try:
            if not _validate_case_id(id_del_caso):
                performance_stats['failed_calls'] += 1
                phase_times['case_validation'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                error_msg = f"El caso con ID {id_del_caso} no existe en la base de datos o no es accesible"
                logger.error(f"[{operation_id}] Case validation failed after {phase_times['case_validation']:.3f}s: {error_msg}")
                logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

                return f"[ERROR] Error de caso: {error_msg}"

            phase_times['case_validation'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Case validation completed successfully in {phase_times['case_validation']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['case_validation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error validando existencia del caso: {str(e)}"
            logger.error(f"[{operation_id}] Case validation error after {phase_times['case_validation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error del sistema: {error_msg}"

        # =====================================================================
        # FASE 3: INICIALIZACIÓN DEL GENERADOR DE TEMPLATES
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 3: Template Generator initialization")

        try:
            # Importar el generador de templates
            from agent_template_generator import AgentTemplateGenerator

            template_generator = AgentTemplateGenerator()
            phase_times['template_generator_init'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Template Generator initialized successfully in {phase_times['template_generator_init']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['template_generator_init'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error inicializando generador de templates: {str(e)}"
            logger.error(f"[{operation_id}] Template Generator initialization failed after {phase_times['template_generator_init']:.3f}s: {error_msg}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error del sistema: {error_msg}"

        # =====================================================================
        # FASE 4: PREPARACIÓN DE DATOS DEL ACUERDO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 4: Agreement data preparation")

        try:
            details_acuerdo = {
                "monto_compensacion_numeros": monto_compensacion.strip(),
                "monto_compensacion_letras": "CANTIDAD EN LETRAS",  # Se puede mejorar con num2words
                "plazo_pago_dias": plazo_pago_dias.strip(),
                "plazo_pago_letras": "DIAS EN LETRAS",  # Se puede mejorar con num2words
                "banco_actor": banco_actor.strip(),
                "cbu_actor": cbu_actor.strip(),
                "alias_actor": alias_actor.strip(),
                "cuit_actor": cuit_actor.strip()
            }

            phase_times['data_preparation'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Agreement data prepared successfully in {phase_times['data_preparation']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['data_preparation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error preparando datos del acuerdo: {str(e)}"
            logger.error(f"[{operation_id}] Data preparation failed after {phase_times['data_preparation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error de procesamiento: {error_msg}"

        # =====================================================================
        # FASE 5: GENERACIÓN DEL ACUERDO CON TEMPLATE
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 5: Template-based agreement generation")

        try:
            agreement_text = template_generator.generate_agreement_from_template(
                case_id=id_del_caso,
                agreement_data=details_acuerdo
            )

            phase_times['template_generation'] = time.time() - phase_start
            logger.info(f"[{operation_id}] Template agreement generation completed in {phase_times['template_generation']:.3f}s")

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['template_generation'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error durante la generación del acuerdo con template: {str(e)}"
            logger.error(f"[{operation_id}] Template generation critical error after {phase_times['template_generation']:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error crítico durante generación con template: {error_msg}"

        # =====================================================================
        # FASE 6: PROCESAMIENTO DEL RESULTADO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 6: Result processing")

        try:
            if agreement_text and not agreement_text.startswith("ERROR"):
                performance_stats['successful_calls'] += 1
                phase_times['result_processing'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                performance_stats['average_duration'] = (
                    (performance_stats['average_duration'] * (performance_stats['successful_calls'] - 1) + total_duration)
                    / performance_stats['successful_calls']
                )

                success_msg = (
                    f"✅ Acuerdo de mediación generado exitosamente con template\n"
                    f"📋 Caso ID: {id_del_caso}\n"
                    f"📄 Tipo: Acuerdo basado en template de texto\n"
                    f"💰 Monto: ${monto_compensacion}\n"
                    f"📅 Plazo: {plazo_pago_dias} días\n"
                    f"🏦 Banco: {banco_actor}\n"
                    f"📝 Generado usando modelo_acuerdo.txt como base\n"
                    f"⏱️  Completado en {total_duration:.3f}s\n"
                    f"ℹ️  El acuerdo está listo para ser revisado y usado"
                )

                logger.info(f"[{operation_id}] Operation completed successfully in {total_duration:.3f}s")
                logger.info(f"[{operation_id}] Performance breakdown:")
                for phase, duration in phase_times.items():
                    percentage = (duration / total_duration) * 100
                    logger.info(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

                logger.info(f"[{operation_id}] Global stats: {performance_stats['successful_calls']}/{performance_stats['total_calls']} successful, avg: {performance_stats['average_duration']:.3f}s")

                return success_msg

            else:
                performance_stats['failed_calls'] += 1
                phase_times['result_processing'] = time.time() - phase_start
                total_duration = time.time() - operation_start_time

                error_msg = (
                    f"[ERROR] Error generando acuerdo con template para caso {id_del_caso}\n"
                    f"📝 Detalle: {agreement_text if agreement_text else 'Error desconocido'}\n"
                    f"⏱️  Falló después de {total_duration:.3f}s\n"
                    f"💡 Sugerencia: Verifique el archivo modelo_acuerdo.txt y los datos del caso"
                )

                logger.error(f"[{operation_id}] Operation failed after {total_duration:.3f}s")
                logger.error(f"[{operation_id}] Error message: {agreement_text}")
                logger.info(f"[{operation_id}] Performance breakdown before failure:")
                for phase, duration in phase_times.items():
                    percentage = (duration / total_duration) * 100 if total_duration > 0 else 0
                    logger.info(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

                logger.info(f"[{operation_id}] Global stats: {performance_stats['failed_calls']}/{performance_stats['total_calls']} failed")

                return error_msg

        except Exception as e:
            performance_stats['failed_calls'] += 1
            phase_times['result_processing'] = time.time() - phase_start
            total_duration = time.time() - operation_start_time

            error_msg = f"Error procesando resultado de la generación con template: {str(e)}"
            logger.error(f"[{operation_id}] Result processing critical error after {total_duration:.3f}s: {error_msg}")
            logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")
            logger.info(f"[{operation_id}] Operation failed after {total_duration:.3f}s")

            return f"[ERROR] Error crítico procesando resultado con template: {error_msg}"

    except Exception as e:
        performance_stats['failed_calls'] += 1
        total_duration = time.time() - operation_start_time

        error_msg = f"Error crítico inesperado en la herramienta de template: {str(e)}"
        logger.error(f"[{operation_id}] Critical unexpected error after {total_duration:.3f}s: {error_msg}")
        logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")

        if 'phase_times' in locals():
            logger.debug(f"[{operation_id}] Partial performance before critical failure:")
            for phase, duration in phase_times.items():
                percentage = (duration / total_duration) * 100 if total_duration > 0 else 0
                logger.debug(f"[{operation_id}]   - {phase}: {duration:.3f}s ({percentage:.1f}%)")

        logger.info(f"[{operation_id}] Global stats: {performance_stats['failed_calls']}/{performance_stats['total_calls']} failed")

        return f"[ERROR] Error crítico: {error_msg} (falló después de {total_duration:.3f}s)"


generar_acuerdo_ia_tool = StructuredTool.from_function(
    func=_ejecutar_generacion_acuerdo_ia,
    name="generar_acuerdo_ia_tool",
    description="Genera acuerdos de mediación usando IA avanzada y análisis de documentos de ejemplo. Esta herramienta puede analizar documentos de ejemplo para extraer patrones y estructuras, luego usar IA para generar nuevos acuerdos basados en datos del caso. Es ideal para crear documentos legales personalizados con contenido generado por IA.",
    args_schema=GenerarAcuerdoIAArgs
)

generar_acuerdo_template_tool = StructuredTool.from_function(
    func=_ejecutar_generacion_acuerdo_template,
    name="generar_acuerdo_template_tool",
    description="Genera acuerdos de mediación usando templates de texto personalizables. Esta herramienta utiliza un archivo modelo_acuerdo.txt como base y reemplaza automáticamente los datos del caso seleccionado. Es perfecta para generar acuerdos rápidos y consistentes basados en plantillas predefinidas.",
    args_schema=GenerarAcuerdoTemplateArgs
)


# --- Esquema de Argumentos para Generar Acuerdo Integrado ---
class GenerarAcuerdoIntegradoArgs(BaseModel):
    cliente_id: Optional[int] = Field(default=None, description="ID del cliente (opcional - si no se especifica, se mostrarán todos los clientes)")
    caso_id: Optional[int] = Field(default=None, description="ID del caso (opcional - si no se especifica, se mostrarán los casos del cliente)")
    monto_compensacion: Optional[str] = Field(default=None, description="Monto total de la compensación.")
    plazo_pago_dias: Optional[str] = Field(default=None, description="Plazo en días para el pago.")
    banco_actor: Optional[str] = Field(default=None, description="Nombre oficial del banco del actor.")
    cbu_actor: Optional[str] = Field(default=None, description="CBU de 22 dígitos de la cuenta del actor.")
    alias_actor: Optional[str] = Field(default=None, description="Alias de la cuenta del actor.")
    cuit_actor: Optional[str] = Field(default=None, description="CUIT o CUIL del actor, con guiones.")
    metodo_generacion: str = Field(default="template", description="Método de generación: 'template', 'ia', o 'escrito'")


def _ejecutar_generacion_acuerdo_integrado(
    cliente_id: Optional[int] = None,
    caso_id: Optional[int] = None,
    monto_compensacion: Optional[str] = None,
    plazo_pago_dias: Optional[str] = None,
    banco_actor: Optional[str] = None,
    cbu_actor: Optional[str] = None,
    alias_actor: Optional[str] = None,
    cuit_actor: Optional[str] = None,
    metodo_generacion: str = "template"
) -> str:
    """
    Función integrada que maneja todo el flujo de generación de acuerdos de mediación.
    Incluye selección de cliente, caso y generación del acuerdo.
    """
    import time
    import datetime
    import traceback

    operation_start_time = time.time()
    operation_id = f"integrated_agreement_tool_{int(operation_start_time)}"

    try:
        logger.info(f"[{operation_id}] Starting integrated agreement generation workflow")
        logger.info(f"[{operation_id}] Method: {metodo_generacion}, Client: {cliente_id}, Case: {caso_id}")

        # =====================================================================
        # FASE 1: OBTENER LISTA DE CLIENTES SI NO SE ESPECIFICA UNO
        # =====================================================================

        if cliente_id is None:
            phase_start = time.time()
            logger.info(f"[{operation_id}] Phase 1: Getting clients list")

            try:
                clients = db.get_clients()
                if not clients:
                    return "[ERROR] No se encontraron clientes en la base de datos."

                # Mostrar lista de clientes para selección
                client_list = "\n".join([f"* ID {c['id']}: {c['nombre']}" for c in clients[:10]])  # Limitar a 10 para no sobrecargar
                if len(clients) > 10:
                    client_list += f"\n... y {len(clients) - 10} clientes más"

                return f"Lista de clientes disponibles:\n\n{client_list}\n\nPor favor, especifica el cliente_id que deseas usar para continuar."

            except Exception as e:
                logger.error(f"[{operation_id}] Error getting clients: {str(e)}")
                return f"[ERROR] Error obteniendo lista de clientes: {str(e)}"

        # =====================================================================
        # FASE 2: OBTENER CASOS DEL CLIENTE SI NO SE ESPECIFICA UN CASO
        # =====================================================================

        if caso_id is None:
            phase_start = time.time()
            logger.info(f"[{operation_id}] Phase 2: Getting cases for client {cliente_id}")

            try:
                cases = db.get_cases_by_client(cliente_id)
                if not cases:
                    return f"[ERROR] No se encontraron casos para el cliente ID {cliente_id}."

                # Mostrar lista de casos para selección
                case_list = []
                for case in cases[:15]:  # Limitar a 15 casos
                    case_id_display = case['id']
                    expediente = f"{case.get('numero_expediente', '')}/{case.get('anio_caratula', '')}" if case.get('numero_expediente') and case.get('anio_caratula') else case.get('numero_expediente', 'N/A')
                    caratula = case.get('caratula', 'Sin carátula')[:60] + "..." if len(case.get('caratula', '')) > 60 else case.get('caratula', 'Sin carátula')
                    case_list.append(f"* ID {case_id_display}: {expediente} - {caratula}")

                case_list_text = "\n".join(case_list)
                if len(cases) > 15:
                    case_list_text += f"\n... y {len(cases) - 15} casos más"

                return f"Casos disponibles para el cliente ID {cliente_id}:\n\n{case_list_text}\n\nPor favor, especifica el caso_id que deseas usar para generar el acuerdo."

            except Exception as e:
                logger.error(f"[{operation_id}] Error getting cases: {str(e)}")
                return f"[ERROR] Error obteniendo casos del cliente: {str(e)}"

        # =====================================================================
        # FASE 3: VALIDAR DATOS DEL ACUERDO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 3: Validating agreement data")

        # Verificar que todos los datos requeridos estén presentes
        required_fields = {
            'monto_compensacion': monto_compensacion,
            'plazo_pago_dias': plazo_pago_dias,
            'banco_actor': banco_actor,
            'cbu_actor': cbu_actor,
            'alias_actor': alias_actor,
            'cuit_actor': cuit_actor
        }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            field_names = {
                'monto_compensacion': 'monto de compensación',
                'plazo_pago_dias': 'plazo de pago en días',
                'banco_actor': 'nombre del banco',
                'cbu_actor': 'CBU del actor',
                'alias_actor': 'alias de la cuenta',
                'cuit_actor': 'CUIT/CUIL del actor'
            }
            missing_names = [field_names[field] for field in missing_fields]
            return f"[ERROR] Faltan datos requeridos para generar el acuerdo:\n• {chr(10).join(missing_names)}\n\nPor favor, proporciona todos los datos necesarios."

        # =====================================================================
        # FASE 4: GENERAR ACUERDO SEGÚN MÉTODO SELECCIONADO
        # =====================================================================

        phase_start = time.time()
        logger.info(f"[{operation_id}] Phase 4: Generating agreement using {metodo_generacion} method")

        if metodo_generacion == "template":
            # Usar el generador de templates
            result = _ejecutar_generacion_acuerdo_template(
                id_del_caso=caso_id,
                monto_compensacion=monto_compensacion,
                plazo_pago_dias=plazo_pago_dias,
                banco_actor=banco_actor,
                cbu_actor=cbu_actor,
                alias_actor=alias_actor,
                cuit_actor=cuit_actor
            )

        elif metodo_generacion == "ia":
            # Usar el generador con IA
            result = _ejecutar_generacion_acuerdo_ia(
                id_del_caso=caso_id,
                monto_compensacion=monto_compensacion,
                plazo_pago_dias=plazo_pago_dias,
                banco_actor=banco_actor,
                cbu_actor=cbu_actor,
                alias_actor=alias_actor,
                cuit_actor=cuit_actor
            )

        elif metodo_generacion == "escrito":
            # Usar el generador de escritos
            result = _ejecutar_generacion_escrito(
                id_del_caso=caso_id,
                monto_compensacion=monto_compensacion,
                plazo_pago_dias=plazo_pago_dias,
                banco_actor=banco_actor,
                cbu_actor=cbu_actor,
                alias_actor=alias_actor,
                cuit_actor=cuit_actor
            )

        else:
            return f"[ERROR] Método de generación '{metodo_generacion}' no válido. Usa 'template', 'ia', o 'escrito'."

        total_duration = time.time() - operation_start_time
        logger.info(f"[{operation_id}] Integrated workflow completed in {total_duration:.3f}s")

        return result

    except Exception as e:
        total_duration = time.time() - operation_start_time
        error_msg = f"Error crítico en el flujo integrado: {str(e)}"
        logger.error(f"[{operation_id}] Critical error after {total_duration:.3f}s: {error_msg}")
        logger.error(f"[{operation_id}] Stack trace: {traceback.format_exc()}")

        return f"[ERROR] Error crítico en el flujo integrado: {error_msg}"


generar_acuerdo_integrado_tool = StructuredTool.from_function(
    func=_ejecutar_generacion_acuerdo_integrado,
    name="generar_acuerdo_integrado_tool",
    description="Herramienta integrada completa para generar acuerdos de mediación. Maneja todo el flujo: selección de cliente, selección de caso, validación de datos y generación del acuerdo. Evita problemas de interfaz gráfica al trabajar completamente dentro del agente. Soporta múltiples métodos de generación: template, IA, y escrito.",
    args_schema=GenerarAcuerdoIntegradoArgs
)