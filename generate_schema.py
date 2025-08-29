#!/usr/bin/env python3
"""
Script para generar el archivo de esquema SQL
"""

import sys
from pathlib import Path

# Agregar el directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

from installer_core.schema_generator import SchemaGenerator
from installer_core import InstallationLogger

def main():
    """Genera el archivo de esquema SQL."""
    print("Generando esquema SQL para CRM Legal...")
    
    # Crear logger
    logger = InstallationLogger(log_dir="schema_logs")
    
    # Crear generador
    generator = SchemaGenerator(logger.get_logger())
    
    # Generar y guardar esquema
    schema_file = "templates/crm_legal_schema.sql"
    success = generator.save_schema_to_file(schema_file)
    
    if success:
        print(f"✓ Esquema SQL generado exitosamente: {schema_file}")
        
        # Mostrar estadísticas
        with open(schema_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = len(content.split('\n'))
            tables = content.count('CREATE TABLE')
            indexes = content.count('CREATE INDEX')
        
        print(f"  - Líneas: {lines}")
        print(f"  - Tablas: {tables}")
        print(f"  - Índices: {indexes}")
    else:
        print("✗ Error generando esquema SQL")
        return False
    
    logger.close()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)