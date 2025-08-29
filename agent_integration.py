"""
Módulo de Integración del Agente IA con LPMS
Integra el agente refactorizado con el sistema de gestión legal existente.
"""

import os
import sys
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Importar el agente refactorizado
from agent_core import AgentCore
import crm_database as db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentIntegrationError(Exception):
    """Excepción para errores de integración del agente"""
    pass


class LPMSAgentIntegration:
    """
    Clase que integra el agente IA refactorizado con el sistema LPMS.
    Permite al agente acceder a datos de casos y generar acuerdos de mediación.
    """

    def __init__(self):
        """Inicializa la integración del agente con LPMS"""
        self.agent_core = None
        self.db_connection = None
        self._initialize_agent()
        self._initialize_database()

    def _initialize_agent(self):
        """Inicializa el núcleo del agente refactorizado"""
        try:
            logger.info("Inicializando agente refactorizado...")
            self.agent_core = AgentCore()
            logger.info("Agente inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando agente: {e}")
            raise AgentIntegrationError(f"No se pudo inicializar el agente: {e}")

    def _initialize_database(self):
        """Inicializa la conexión a la base de datos PostgreSQL"""
        try:
            logger.info("Conectando a base de datos PostgreSQL...")
            self.db_connection = db.connect_db()
            if not self.db_connection:
                raise AgentIntegrationError("No se pudo conectar a la base de datos")
            logger.info("Conexion a base de datos establecida")
        except Exception as e:
            logger.error(f"Error conectando a base de datos: {e}")
            raise AgentIntegrationError(f"Error de conexión a BD: {e}")

    def get_case_data_for_agent(self, case_id: int) -> Dict[str, Any]:
        """
        Obtiene datos completos del caso para el agente.
        Incluye información del caso, partes, actividades y documentos.

        Args:
            case_id: ID del caso en la base de datos

        Returns:
            Dict con toda la información del caso formateada para el agente
        """
        try:
            logger.info(f"Obteniendo datos del caso {case_id}...")

            # Obtener datos básicos del caso
            case_data = db.get_case_by_id(case_id)
            if not case_data:
                raise AgentIntegrationError(f"Caso {case_id} no encontrado")

            # Obtener cliente asociado
            client_data = None
            if case_data.get('cliente_id'):
                client_data = db.get_client_by_id(case_data['cliente_id'])

            # Obtener partes del caso
            parties_data = db.get_roles_by_caso_id(case_id)

            # Obtener actividades del caso
            activities_data = db.get_actividades_by_caso_id(case_id)

            # Formatear datos para el agente
            formatted_data = {
                "id_caso": case_data.get("id"),
                "caratula": case_data.get("caratula", ""),
                "fecha_inicio": case_data.get("fecha_inicio", ""),
                "estado": case_data.get("estado", ""),
                "descripcion": case_data.get("descripcion", ""),
                "cliente": {
                    "id": client_data.get("id") if client_data else None,
                    "nombre": client_data.get("nombre", "") if client_data else "",
                    "direccion": client_data.get("direccion", "") if client_data else "",
                    "email": client_data.get("email", "") if client_data else "",
                    "whatsapp": client_data.get("whatsapp", "") if client_data else ""
                } if client_data else None,
                "partes": [
                    {
                        "rol": party.get("rol", ""),
                        "nombre_completo": party.get("nombre_completo", ""),
                        "tipo_persona": party.get("tipo_persona", ""),
                        "cuit_cuil": party.get("cuit_cuil", ""),
                        "domicilio": party.get("domicilio", ""),
                        "telefono": party.get("telefono", ""),
                        "email": party.get("email", "")
                    } for party in parties_data
                ],
                "actividades": [
                    {
                        "fecha_hora": activity.get("fecha_hora", ""),
                        "tipo_actividad": activity.get("tipo_actividad", ""),
                        "descripcion": activity.get("descripcion", ""),
                        "referencia_documento": activity.get("referencia_documento", "")
                    } for activity in activities_data
                ],
                "fecha_extraccion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"Datos del caso {case_id} obtenidos correctamente")
            return formatted_data

        except Exception as e:
            logger.error(f"Error obteniendo datos del caso {case_id}: {e}")
            raise AgentIntegrationError(f"Error obteniendo datos del caso: {e}")

    def generate_mediation_agreement(self, case_id: int, agreement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Genera un acuerdo de mediación usando el agente refactorizado.

        Args:
            case_id: ID del caso
            agreement_data: Datos del acuerdo (monto, plazo, datos bancarios, etc.)

        Returns:
            Dict con resultado de la generación
        """
        try:
            logger.info(f"Generando acuerdo de mediacion para caso {case_id}...")

            # Obtener datos del caso
            case_data = self.get_case_data_for_agent(case_id)

            # Preparar el prompt para el agente
            prompt_parts = []

            # Información del caso
            prompt_parts.append(f"""
INFORMACION DEL CASO:
- ID: {case_data['id_caso']}
- Caratula: {case_data['caratula']}
- Cliente: {case_data['cliente']['nombre'] if case_data['cliente'] else 'No especificado'}
- Estado: {case_data['estado']}
- Descripcion: {case_data['descripcion']}
""")

            # Partes involucradas
            if case_data['partes']:
                prompt_parts.append("\nPARTES INVOLUCRADAS:")
                for party in case_data['partes']:
                    prompt_parts.append(f"- {party['rol']}: {party['nombre_completo']} (CUIT: {party['cuit_cuil']})")

            # Datos del acuerdo
            prompt_parts.append(f"""
DATOS DEL ACUERDO:
- Monto de compensacion: {agreement_data.get('monto_compensacion', 'No especificado')}
- Plazo de pago: {agreement_data.get('plazo_pago_dias', 'No especificado')} dias
- Banco del actor: {agreement_data.get('banco_actor', 'No especificado')}
- CBU del actor: {agreement_data.get('cbu_actor', 'No especificado')}
- Alias del actor: {agreement_data.get('alias_actor', 'No especificado')}
- CUIT del actor: {agreement_data.get('cuit_actor', 'No especificado')}
""")

            # Instrucción final
            prompt_parts.append("""
INSTRUCCIONES:
Usando la informacion del caso y los datos del acuerdo proporcionados, genera un acuerdo de mediacion completo y profesional siguiendo las mejores practicas legales argentinas.

El acuerdo debe incluir:
1. Identificacion de las partes
2. Antecedentes del caso
3. Acuerdos alcanzados
4. Condiciones de pago
5. Firmas y fecha

Utiliza el formato StructuredTool 'generar_escrito_mediacion_tool' con los parametros proporcionados.
""")

            # Unir el prompt completo
            full_prompt = "\n".join(prompt_parts)

            # Ejecutar el agente
            logger.info("Ejecutando agente para generar acuerdo...")
            response = self.agent_core.run_intent(full_prompt)

            # Procesar respuesta
            result = {
                "success": True,
                "response": response,
                "case_id": case_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            logger.info(f"Acuerdo generado exitosamente para caso {case_id}")
            return result

        except Exception as e:
            logger.error(f"Error generando acuerdo para caso {case_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "case_id": case_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def save_agreement_to_case(self, case_id: int, agreement_result: Dict[str, Any]) -> bool:
        """
        Guarda el acuerdo generado como actividad en el caso.

        Args:
            case_id: ID del caso
            agreement_result: Resultado de la generación del acuerdo

        Returns:
            bool: True si se guardó correctamente
        """
        try:
            logger.info(f"Guardando acuerdo como actividad en caso {case_id}...")

            # Preparar descripcion de la actividad
            descripcion = f"Acuerdo de Mediacion generado por IA\n\n"
            descripcion += f"Resultado: {'Exitoso' if agreement_result['success'] else 'Error'}\n"
            descripcion += f"Fecha: {agreement_result['timestamp']}\n\n"

            if agreement_result['success']:
                descripcion += f"Respuesta del agente:\n{agreement_result['response'][:500]}..."
                if len(agreement_result['response']) > 500:
                    descripcion += "\n\n[Respuesta truncada - ver logs para contenido completo]"
            else:
                descripcion += f"Error: {agreement_result['error']}"

            # Guardar como actividad
            success = db.add_actividad_caso(
                caso_id=case_id,
                fecha_hora=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                tipo_actividad="Acuerdo Mediacion - IA",
                descripcion=descripcion,
                creado_por="Sistema IA",
                referencia_documento="acuerdo_mediacion_ia"
            )

            if success:
                logger.info(f"Acuerdo guardado como actividad en caso {case_id}")
                return True
            else:
                logger.error(f"Error guardando acuerdo como actividad en caso {case_id}")
                return False

        except Exception as e:
            logger.error(f"Error guardando acuerdo en caso {case_id}: {e}")
            return False

    def close(self):
        """Cierra la integración y libera recursos"""
        try:
            if self.db_connection:
                self.db_connection.close()
                logger.info("Conexion a base de datos cerrada")

            if self.agent_core:
                # El agente no tiene metodo close especifico, pero podemos limpiarlo
                self.agent_core = None
                logger.info("Agente limpiado")

            logger.info("Integracion cerrada correctamente")

        except Exception as e:
            logger.error(f"Error cerrando integracion: {e}")


# Función de conveniencia para uso directo
def create_mediation_agreement(case_id: int, agreement_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de conveniencia para crear acuerdos de mediación.
    Útil para integración directa desde otros módulos.

    Args:
        case_id: ID del caso
        agreement_data: Datos del acuerdo

    Returns:
        Dict con resultado de la operación
    """
    integration = None
    try:
        integration = LPMSAgentIntegration()
        result = integration.generate_mediation_agreement(case_id, agreement_data)

        # Guardar como actividad si fue exitoso
        if result['success']:
            integration.save_agreement_to_case(case_id, result)

        return result

    except Exception as e:
        logger.error(f"Error en create_mediation_agreement: {e}")
        return {
            "success": False,
            "error": str(e),
            "case_id": case_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    finally:
        if integration:
            integration.close()


# Función para testing
def test_integration():
    """Función de prueba para verificar la integración"""
    print("Probando integracion del agente con LPMS...")

    try:
        integration = LPMSAgentIntegration()
        print("Integracion inicializada correctamente")

        # Probar obtención de datos de un caso (usar ID de prueba)
        test_case_id = 1  # Cambiar por un ID válido en tu BD
        case_data = integration.get_case_data_for_agent(test_case_id)
        print(f"Datos del caso obtenidos: {case_data['caratula']}")

        integration.close()
        print("Prueba completada exitosamente")

    except Exception as e:
        print(f"Error en prueba: {e}")
        return False

    return True


if __name__ == "__main__":
    # Ejecutar prueba si se llama directamente
    test_integration()