#!/usr/bin/env python3
"""
Script to analyze placeholders in agreement template and map them to database fields.
"""

import os
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path

def read_template_file(file_path: str) -> str:
    """Read the template file and return its content."""
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
                print(f"Successfully read file with encoding: {encoding}")
                return content
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading template file: {e}")
            return ""

    print("Could not read file with any of the attempted encodings")
    return ""

def extract_placeholders(text: str) -> List[str]:
    """Extract all placeholders from the template text."""
    placeholders = []

    # Patterns for different placeholder formats used in the system
    patterns = [
        r'\{([^{}]+)\}',        # {variable_name}
        r'\{\{([^}]+)\}\}',     # {{variable_name}}
        r'\[([^\]]+)\]',        # [VARIABLE_NAME]
        r'<<([^>]+)>>',         # <<Variable>>
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            # Reconstruct the full placeholder
            if pattern == r'\{([^{}]+)\}':
                placeholders.append(f"{{{match}}}")
            elif pattern == r'\{\{([^}]+)\}\}':
                placeholders.append(f"{{{{{match}}}}}")  # Double braces
            elif pattern == r'\[([^\]]+)\]':
                placeholders.append(f"[{match}]")
            elif pattern == r'<<([^>]+)>>':
                placeholders.append(f"<<{match}>>")

    return sorted(list(set(placeholders)))

def analyze_database_fields() -> Dict[str, List[str]]:
    """Analyze available database fields from the schema."""
    # Based on the crm_database.py analysis
    database_fields = {
        'casos': [
            'id', 'cliente_id', 'numero_expediente', 'anio_caratula', 'caratula',
            'juzgado', 'jurisdiccion', 'etapa_procesal', 'notas', 'ruta_carpeta',
            'ruta_carpeta_movimientos', 'ruta_vector_db', 'estado_indexacion',
            'inactivity_threshold_days', 'inactivity_enabled', 'created_at',
            'last_activity_timestamp', 'last_inactivity_notification_timestamp'
        ],
        'contactos': [
            'id', 'nombre_completo', 'es_persona_juridica', 'dni', 'cuit',
            'domicilio_real', 'domicilio_legal', 'email', 'telefono',
            'notas_generales', 'created_at'
        ],
        'roles_en_caso': [
            'id', 'caso_id', 'contacto_id', 'rol_principal', 'rol_secundario',
            'representa_a_id', 'datos_bancarios', 'notas_del_rol', 'created_at'
        ],
        'clientes': [
            'id', 'nombre', 'direccion', 'email', 'whatsapp', 'created_at'
        ],
        'datos_usuario': [
            'id', 'nombre_abogado', 'matricula_nacion', 'matricula_pba',
            'matricula_federal', 'domicilio_procesal_caba', 'zona_notificacion',
            'domicilio_procesal_pba', 'telefono_estudio', 'email_estudio',
            'cuit', 'legajo_prev', 'domicilio_electronico_pba',
            'cuenta_bancaria_honorarios', 'otros_datos'
        ]
    }

    return database_fields

def map_placeholders_to_fields(placeholders: List[str], db_fields: Dict[str, List[str]]) -> Dict[str, Dict]:
    """Map template placeholders to database fields."""

    mapping = {}

    # Direct mappings based on analysis from codebase
    direct_mappings = {
        # Case information
        '{numero_expediente}': {
            'table': 'casos',
            'field': 'numero_expediente',
            'description': 'Case file number',
            'status': 'mapped'
        },
        '{caratula}': {
            'table': 'casos',
            'field': 'caratula',
            'description': 'Case title/caption',
            'status': 'mapped'
        },
        '{{caratula}}': {
            'table': 'casos',
            'field': 'caratula',
            'description': 'Case title/caption (double braces)',
            'status': 'mapped'
        },
        '[NUMERO_EXPEDIENTE]': {
            'table': 'casos',
            'field': 'numero_expediente',
            'description': 'Case file number (old format)',
            'status': 'mapped'
        },
        '[CARATULA]': {
            'table': 'casos',
            'field': 'caratula',
            'description': 'Case title/caption (old format)',
            'status': 'mapped'
        },

        # Date/time placeholders
        '{fecha_acuerdo}': {
            'table': None,
            'field': 'generated',
            'description': 'Agreement date (current date)',
            'status': 'generated'
        },
        '{mes_acuerdo}': {
            'table': None,
            'field': 'generated',
            'description': 'Agreement month in Spanish (current month)',
            'status': 'generated'
        },
        '{anio_acuerdo}': {
            'table': None,
            'field': 'generated',
            'description': 'Agreement year (current year)',
            'status': 'generated'
        },

        # Party information
        '{actor.nombre_completo}': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Actor full name (where rol_principal = "Actor")',
            'status': 'mapped'
        },
        '{demandado.nombre_completo}': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Defendant full name (where rol_principal = "Demandado")',
            'status': 'mapped'
        },
        '{{actor_nombre}}': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Actor name (test format)',
            'status': 'mapped'
        },
        '{{demandado_nombre}}': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Defendant name (test format)',
            'status': 'mapped'
        },
        '[NOMBRE_ACTOR]': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Actor full name (old format)',
            'status': 'mapped'
        },
        '[NOMBRE_DEMANDADO]': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Defendant full name (old format)',
            'status': 'mapped'
        },

        # Banking and financial
        '{datos_bancarios}': {
            'table': 'roles_en_caso',
            'field': 'datos_bancarios',
            'description': 'Banking details for the party',
            'status': 'mapped'
        },
        '{{monto_compensacion_numeros}}': {
            'table': None,
            'field': 'parameter',
            'description': 'Compensation amount in numbers (parameter)',
            'status': 'parameter'
        },
        '{{plazo_pago_dias}}': {
            'table': None,
            'field': 'parameter',
            'description': 'Payment deadline in days (parameter)',
            'status': 'parameter'
        },

        # Lawyer information
        '{abogado_actor.nombre_completo}': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Actor lawyer full name (where rol_principal = "Abogado" and represents actor)',
            'status': 'mapped'
        },
        '{abogado_demandado.nombre_completo}': {
            'table': 'contactos',
            'field': 'nombre_completo',
            'description': 'Defendant lawyer full name (where rol_principal = "Abogado" and represents defendant)',
            'status': 'mapped'
        },

        # Agreement parameters
        '{monto_acuerdo}': {
            'table': None,
            'field': 'parameter',
            'description': 'Agreement amount (provided as parameter)',
            'status': 'parameter'
        },
        '{plazo_pago}': {
            'table': None,
            'field': 'parameter',
            'description': 'Payment deadline (provided as parameter)',
            'status': 'parameter'
        }
    }

    # Check each placeholder
    for placeholder in placeholders:
        if placeholder in direct_mappings:
            mapping[placeholder] = direct_mappings[placeholder]
        else:
            mapping[placeholder] = {
                'table': None,
                'field': None,
                'description': 'No mapping found',
                'status': 'unmapped'
            }

    return mapping

def identify_missing_functions(mapping: Dict[str, Dict]) -> List[str]:
    """Identify missing database functions needed for proper mapping."""
    missing_functions = []

    # Check if we need get_partes_by_caso_and_tipo function
    actor_mappings = [k for k, v in mapping.items() if 'actor' in k.lower() and v['status'] == 'mapped']
    defendant_mappings = [k for k, v in mapping.items() if 'demandado' in k.lower() and v['status'] == 'mapped']

    if actor_mappings or defendant_mappings:
        missing_functions.append("get_partes_by_caso_and_tipo(case_id, tipo) - Function called by AI agreement generator but doesn't exist")
        missing_functions.append("get_partes_by_caso_and_tipo(case_id, 'ACTOR') - To get actors for a case")
        missing_functions.append("get_partes_by_caso_and_tipo(case_id, 'DEMANDADO') - To get defendants for a case")

    # Check for lawyer mappings
    lawyer_mappings = [k for k, v in mapping.items() if 'abogado' in k.lower() and v['status'] == 'mapped']
    if lawyer_mappings:
        missing_functions.append("get_representantes_by_party(case_id, party_id) - Function to get lawyers representing a specific party")
        missing_functions.append("get_abogados_by_caso_and_tipo(case_id, tipo) - To get lawyers by case and party type")

    # Check for complex queries needed
    if any('representa_a_id' in str(v.get('description', '')) for v in mapping.values()):
        missing_functions.append("Complex JOIN queries for roles with representation relationships")

    return missing_functions

def generate_report(template_path: str) -> str:
    """Generate a comprehensive analysis report."""

    # Read template and extract placeholders
    template_content = read_template_file(template_path)
    if not template_content:
        return "Error: Could not read template file"

    placeholders = extract_placeholders(template_content)

    # Analyze database fields
    db_fields = analyze_database_fields()

    # Map placeholders to fields
    mapping = map_placeholders_to_fields(placeholders, db_fields)

    # Identify issues
    missing_functions = identify_missing_functions(mapping)

    # Generate report
    report = []
    report.append("=" * 80)
    report.append("PLACEHOLDER ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")

    report.append(f"Template file: {template_path}")
    report.append(f"Total placeholders found: {len(placeholders)}")
    report.append("")

    report.append("PLACEHOLDER MAPPING:")
    report.append("-" * 50)

    for placeholder, info in mapping.items():
        status_icon = {
            'mapped': '[OK]',
            'generated': '[GEN]',
            'parameter': '[PAR]',
            'unmapped': '[ERR]'
        }.get(info['status'], '[UNK]')

        report.append(f"{status_icon} {placeholder}")
        report.append(f"   Status: {info['status']}")
        report.append(f"   Table: {info['table'] or 'N/A'}")
        report.append(f"   Field: {info['field'] or 'N/A'}")
        report.append(f"   Description: {info['description']}")
        report.append("")

    if missing_functions:
        report.append("MISSING DATABASE FUNCTIONS:")
        report.append("-" * 50)
        for func in missing_functions:
            report.append(f"[MISSING] {func}")
        report.append("")

    report.append("SUMMARY:")
    report.append("-" * 50)
    mapped = len([m for m in mapping.values() if m['status'] == 'mapped'])
    generated = len([m for m in mapping.values() if m['status'] == 'generated'])
    parameters = len([m for m in mapping.values() if m['status'] == 'parameter'])
    unmapped = len([m for m in mapping.values() if m['status'] == 'unmapped'])

    report.append(f"[OK] Mapped to database: {mapped}")
    report.append(f"[GEN] Generated values: {generated}")
    report.append(f"[PAR] Parameter values: {parameters}")
    report.append(f"[ERR] Unmapped: {unmapped}")

    if unmapped == 0 and not missing_functions:
        report.append("")
        report.append("[SUCCESS] All placeholders can be properly mapped!")
    else:
        report.append("")
        report.append("[WARNING] Some placeholders need attention.")

    return "\n".join(report)

def main():
    """Main function to run the analysis."""
    import sys

    # Use command line argument if provided, otherwise default
    if len(sys.argv) > 1:
        template_path = sys.argv[1]
    else:
        template_path = "modelo_acuerdo.txt"

    if not os.path.exists(template_path):
        print(f"Error: Template file '{template_path}' not found.")
        return

    report = generate_report(template_path)
    print(report)

    # Save report to file
    report_file = "placeholder_analysis_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: {report_file}")

if __name__ == "__main__":
    main()