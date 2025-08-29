#!/usr/bin/env python3
"""
Agent Template Generator - Generador de acuerdos usando templates
Utiliza un modelo de acuerdo base para generar documentos personalizados
"""

import os
import datetime
from typing import Dict, List, Any, Optional
import crm_database as db

class AgentTemplateGenerator:
    """Generador de acuerdos usando templates de texto"""

    def __init__(self, template_path: str = "modelo_acuerdo.txt"):
        self.template_path = template_path
        self.template_content = ""
        self._load_template()

    def _load_template(self):
        """Cargar el template de acuerdo"""
        try:
            if os.path.exists(self.template_path):
                # Try different encodings, starting with latin-1 for compatibility with Windows
                encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
                for encoding in encodings_to_try:
                    try:
                        with open(self.template_path, 'r', encoding=encoding) as f:
                            self.template_content = f.read()
                        print(f"[DEBUG] Template cargado desde: {self.template_path} (encoding: {encoding})")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise UnicodeDecodeError("Could not decode file with any of the attempted encodings")
            else:
                print(f"[WARNING] Template no encontrado: {self.template_path}")
                self._create_default_template()
        except Exception as e:
            print(f"[ERROR] Error cargando template: {e}")
            self._create_default_template()

    def _create_default_template(self):
        """Crear un template básico por defecto"""
        self.template_content = """ACUERDO DE MEDIACIÓN

En la Ciudad Autónoma de Buenos Aires, a los {DIA_ACUERDO} días del mes de {MES_ACUERDO} de {AÑO_ACUERDO}, comparecen las siguientes partes:

ACTORES:
{ACTORES_LIST}

DEMANDADOS:
{DEMANDADOS_LIST}

Las partes acuerdan lo siguiente:

MONTO: ${MONTO_COMPENSACION_NUMEROS} ({MONTO_COMPENSACION_LETRAS})
PLAZO: {PLAZO_PAGO_DIAS} días
BANCO: {BANCO_ACTOR}
CBU: {CBU_ACTOR}

FIRMAS:
{FIRMAS_ACTORES}
{FIRMAS_DEMANDADOS}
"""

    def generate_agreement_from_template(self, case_id: int, agreement_data: Dict[str, Any]) -> str:
        """
        Generar acuerdo usando el template y datos del caso

        Args:
            case_id: ID del caso
            agreement_data: Datos del acuerdo (monto, plazo, etc.)

        Returns:
            str: Acuerdo generado en formato de texto
        """
        try:
            # Obtener datos del caso
            case_data = self._get_case_data(case_id)
            if not case_data:
                return "ERROR: No se pudo obtener la información del caso"

            # Preparar datos para el template
            template_data = self._prepare_template_data(case_data, agreement_data)

            # Generar acuerdo usando el template
            agreement_text = self.template_content.format(**template_data)

            return agreement_text

        except Exception as e:
            return f"ERROR generando acuerdo: {str(e)}"

    def generate_agreement_from_template_with_mock_data(self, case_id, agreement_data):
        """
        Generar acuerdo usando datos ficticios para testing
        No requiere acceso a la base de datos
        """
        try:
            # Datos ficticios del caso para testing
            mock_case_data = {
                'case': {
                    'id': case_id or 999,
                    'numero_expediente': 'TEST-001-2024',
                    'caratula': 'TEST CASE - Acuerdo de Prueba',
                    'juzgado': 'Juzgado Civil 1',
                    'jurisdiccion': 'Ciudad Autónoma de Buenos Aires'
                },
                'actors': [
                    {
                        'nombre_completo': 'Juan Carlos Pérez',
                        'dni': '12345678',
                        'cuit': '20-12345678-1',
                        'representantes': [
                            {
                                'nombre_completo': 'Dr. María González',
                                'cuit': '27-87654321-1',
                                'personeria': 'Poder General Judicial'
                            }
                        ]
                    }
                ],
                'defendants': [
                    {
                        'nombre_completo': 'Empresa XYZ S.A.',
                        'cuit': '30-11223344-1',
                        'representantes': [
                            {
                                'nombre_completo': 'Lic. Carlos Rodríguez',
                                'cuit': '20-44332211-1',
                                'personeria': 'Apoderado'
                            }
                        ]
                    }
                ]
            }

            # Preparar datos para el template
            template_data = self._prepare_template_data(mock_case_data, agreement_data)

            # Generar acuerdo usando el template
            agreement_text = self.template_content.format(**template_data)

            return agreement_text

        except Exception as e:
            return f"ERROR generando acuerdo con datos ficticios: {str(e)}"

    def _get_case_data(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Obtener datos completos del caso"""
        try:
            case = db.get_case_by_id(case_id)
            if not case:
                return None

            # Obtener partes del caso
            actors = []
            defendants = []

            # Aquí iría la lógica para obtener actores y demandados
            # Por ahora, devolver datos básicos del caso
            return {
                'case': case,
                'actors': actors,
                'defendants': defendants
            }

        except Exception as e:
            print(f"[ERROR] Obteniendo datos del caso: {e}")
            return None

    def _prepare_template_data(self, case_data: Dict[str, Any], agreement_data: Dict[str, Any]) -> Dict[str, str]:
        """Preparar datos para el template"""
        case = case_data['case']

        # Datos básicos del caso
        template_data = {
            'NUMERO_EXPEDIENTE': case.get('numero_expediente', 'SIN EXPEDIENTE'),
            'CARATULA': case.get('caratula', 'SIN CARÁTULA'),
            'JUZGADO': case.get('juzgado', 'SIN JUZGADO'),
            'DIA_ACUERDO': str(datetime.date.today().day),
            'MES_ACUERDO': self._get_month_name(datetime.date.today().month),
            'AÑO_ACUERDO': str(datetime.date.today().year),
            'LUGAR_ACUERDO': 'Ciudad Autónoma de Buenos Aires',
            'CENTRO_MEDIACION': 'Centro de Mediación correspondiente',
            'MEDIADOR': 'Mediador designado',
        }

        # Datos del acuerdo
        template_data.update({
            'MONTO_COMPENSACION_NUMEROS': agreement_data.get('monto_compensacion_numeros', '0'),
            'MONTO_COMPENSACION_LETRAS': agreement_data.get('monto_compensacion_letras', 'CERO'),
            'PLAZO_PAGO_DIAS': agreement_data.get('plazo_pago_dias', '30'),
            'PLAZO_PAGO_LETRAS': agreement_data.get('plazo_pago_letras', 'TREINTA'),
            'BANCO_ACTOR': agreement_data.get('banco_actor', 'SIN ESPECIFICAR'),
            'CBU_ACTOR': agreement_data.get('cbu_actor', 'SIN ESPECIFICAR'),
            'ALIAS_ACTOR': agreement_data.get('alias_actor', 'SIN ESPECIFICAR'),
            'CUIT_ACTOR': agreement_data.get('cuit_actor', 'SIN ESPECIFICAR'),
        })

        # Preparar listas de partes
        actors_list = self._format_parties_list(case_data.get('actors', []), "ACTOR")
        defendants_list = self._format_parties_list(case_data.get('defendants', []), "DEMANDADO")

        template_data.update({
            'ACTORES_LIST': actors_list,
            'DEMANDADOS_LIST': defendants_list,
            'FIRMAS_ACTORES': self._format_signatures(case_data.get('actors', [])),
            'FIRMAS_DEMANDADOS': self._format_signatures(case_data.get('defendants', [])),
            'FIRMA_MEDIADOR': '_____________________\nMediador',
            'FIRMA_JUEZ': '_____________________\nJuez',
        })

        return template_data

    def _get_month_name(self, month: int) -> str:
        """Obtener nombre del mes en español"""
        months = [
            'enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
            'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'
        ]
        return months[month - 1] if 1 <= month <= 12 else 'enero'

    def _format_parties_list(self, parties: List[Dict[str, Any]], party_type: str) -> str:
        """Formatear lista de partes para el template"""
        if not parties:
            return f"- No hay {party_type.lower()}s registrados"

        formatted = []
        for party in parties:
            name = party.get('nombre_completo', 'Sin nombre')
            formatted.append(f"- {name}")

            # Agregar representantes si existen
            representatives = party.get('representantes', [])
            for rep in representatives:
                rep_name = rep.get('nombre_completo', 'Sin nombre')
                formatted.append(f"  Representado por: {rep_name}")

        return '\n'.join(formatted)

    def _format_signatures(self, parties: List[Dict[str, Any]]) -> str:
        """Formatear firmas de las partes"""
        if not parties:
            return "_____________________\nFirma"

        signatures = []
        for party in parties:
            name = party.get('nombre_completo', 'Sin nombre')
            signatures.append(f"_____________________\n{name}")

            # Agregar firmas de representantes
            representatives = party.get('representantes', [])
            for rep in representatives:
                rep_name = rep.get('nombre_completo', 'Sin nombre')
                signatures.append(f"_____________________\n{rep_name} (Representante)")

        return '\n\n'.join(signatures)

# Función para integrar con el sistema de agentes
def generate_agreement_with_template_tool(case_id: int, agreement_details: Dict[str, Any]) -> str:
    """
    Herramienta para generar acuerdos usando templates
    Integrada con el sistema de agentes
    """
    try:
        generator = AgentTemplateGenerator()
        agreement = generator.generate_agreement_from_template(case_id, agreement_details)

        # Aquí se podría guardar el acuerdo generado como documento
        # Por ahora solo lo retornamos

        return f"Acuerdo generado exitosamente:\n\n{agreement}"

    except Exception as e:
        return f"Error generando acuerdo con template: {str(e)}"

if __name__ == "__main__":
    # Ejemplo de uso
    generator = AgentTemplateGenerator()

    # Datos de ejemplo
    agreement_data = {
        'monto_compensacion_numeros': '50000',
        'monto_compensacion_letras': 'CINCUENTA MIL',
        'plazo_pago_dias': '30',
        'plazo_pago_letras': 'TREINTA',
        'banco_actor': 'Banco Nación',
        'cbu_actor': '0720123456789012345678',
        'alias_actor': 'empresa.legal',
        'cuit_actor': '27-12345678-1'
    }

    # Generar acuerdo (necesitaría un case_id válido)
    print("Template Generator listo para usar")
    print("Para usar: generate_agreement_with_template_tool(case_id, agreement_data)")