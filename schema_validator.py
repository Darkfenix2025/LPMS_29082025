#!/usr/bin/env python3
"""
Schema Validator
Valida y sincroniza los esquemas entre la base de datos local y la nube.
Puede detectar diferencias y aplicar correcciones automáticamente.
"""

import psycopg2
import configparser
import logging
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ColumnInfo:
    """Información de una columna de tabla."""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    character_maximum_length: Optional[int]
    numeric_precision: Optional[int]
    numeric_scale: Optional[int]

@dataclass
class TableInfo:
    """Información completa de una tabla."""
    name: str
    columns: Dict[str, ColumnInfo]
    primary_keys: List[str]
    foreign_keys: List[Dict]
    indexes: List[Dict]

@dataclass
class ValidationResult:
    """Resultado de la validación de esquemas."""
    is_valid: bool
    missing_tables: List[str]
    extra_tables: List[str]
    column_differences: Dict[str, List[str]]
    foreign_key_issues: List[str]
    fixable_issues: List[str]
    critical_issues: List[str]

class SchemaValidator:
    def __init__(self, local_config_file: str, cloud_config_file: str):
        """
        Inicializa el validador de esquemas.
        
        Args:
            local_config_file: Archivo de configuración para la base local
            cloud_config_file: Archivo de configuración para la base en la nube
        """
        self.local_config_file = local_config_file
        self.cloud_config_file = cloud_config_file
        self.setup_logging()
        
    def setup_logging(self):
        """Configura el sistema de logging."""
        # Crear handlers con codificación UTF-8
        file_handler = logging.FileHandler(
            f'schema_validation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
            encoding='utf-8'
        )
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Configurar formato
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Configurar logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
    def load_config(self, config_file: str) -> dict:
        """Carga la configuración desde un archivo INI."""
        config = configparser.ConfigParser()
        config.read(config_file)
        
        db_config = {
            'host': config.get('postgresql', 'host'),
            'database': config.get('postgresql', 'database'),
            'user': config.get('postgresql', 'user'),
            'password': config.get('postgresql', 'password'),
        }
        
        # Puerto opcional
        if config.has_option('postgresql', 'port') and config.get('postgresql', 'port'):
            db_config['port'] = config.get('postgresql', 'port')
            
        # SSL mode para conexiones en la nube
        if config.has_option('postgresql', 'sslmode'):
            db_config['sslmode'] = config.get('postgresql', 'sslmode')
            
        return db_config
        
    def get_connection(self, config_file: str):
        """Obtiene una conexión a la base de datos."""
        config = self.load_config(config_file)
        return psycopg2.connect(**config)
        
    def get_table_columns(self, conn, table_name: str) -> Dict[str, ColumnInfo]:
        """Obtiene información detallada de las columnas de una tabla."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            columns = {}
            for row in cursor.fetchall():
                col_info = ColumnInfo(
                    name=row[0],
                    data_type=row[1],
                    is_nullable=(row[2] == 'YES'),
                    default_value=row[3],
                    character_maximum_length=row[4],
                    numeric_precision=row[5],
                    numeric_scale=row[6]
                )
                columns[row[0]] = col_info
                
            return columns
            
    def get_table_primary_keys(self, conn, table_name: str) -> List[str]:
        """Obtiene las llaves primarias de una tabla."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
                AND tc.constraint_type = 'PRIMARY KEY'
                ORDER BY kcu.ordinal_position
            """, (table_name,))
            
            return [row[0] for row in cursor.fetchall()]
            
    def get_table_foreign_keys(self, conn, table_name: str) -> List[Dict]:
        """Obtiene las llaves foráneas de una tabla."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_schema = 'public'
                AND tc.table_name = %s
                AND tc.constraint_type = 'FOREIGN KEY'
            """, (table_name,))
            
            foreign_keys = []
            for row in cursor.fetchall():
                foreign_keys.append({
                    'constraint_name': row[0],
                    'column_name': row[1],
                    'referenced_table': row[2],
                    'referenced_column': row[3]
                })
                
            return foreign_keys
            
    def get_table_info(self, conn, table_name: str) -> TableInfo:
        """Obtiene información completa de una tabla."""
        return TableInfo(
            name=table_name,
            columns=self.get_table_columns(conn, table_name),
            primary_keys=self.get_table_primary_keys(conn, table_name),
            foreign_keys=self.get_table_foreign_keys(conn, table_name),
            indexes=[]  # Por simplicidad, no incluimos índices por ahora
        )
        
    def get_all_tables(self, conn) -> List[str]:
        """Obtiene todas las tablas de la base de datos."""
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            return [row[0] for row in cursor.fetchall()]
            
    def compare_columns(self, local_cols: Dict[str, ColumnInfo], 
                       cloud_cols: Dict[str, ColumnInfo]) -> List[str]:
        """Compara las columnas entre dos tablas y retorna las diferencias."""
        differences = []
        
        # Columnas que faltan en la nube
        missing_in_cloud = set(local_cols.keys()) - set(cloud_cols.keys())
        for col in missing_in_cloud:
            differences.append(f"Columna '{col}' falta en la nube")
            
        # Columnas extra en la nube
        extra_in_cloud = set(cloud_cols.keys()) - set(local_cols.keys())
        for col in extra_in_cloud:
            differences.append(f"Columna '{col}' extra en la nube")
            
        # Diferencias en columnas comunes
        common_cols = set(local_cols.keys()) & set(cloud_cols.keys())
        for col in common_cols:
            local_col = local_cols[col]
            cloud_col = cloud_cols[col]
            
            if local_col.data_type != cloud_col.data_type:
                differences.append(f"Columna '{col}': tipo diferente (local: {local_col.data_type}, nube: {cloud_col.data_type})")
                
            if local_col.is_nullable != cloud_col.is_nullable:
                differences.append(f"Columna '{col}': nullable diferente (local: {local_col.is_nullable}, nube: {cloud_col.is_nullable})")
                
        return differences
        
    def validate_table_structures(self) -> ValidationResult:
        """Valida las estructuras de tablas entre ambas bases de datos."""
        self.logger.info("=== INICIANDO VALIDACIÓN DE ESQUEMAS ===")
        
        try:
            # Conectar a ambas bases de datos
            local_conn = self.get_connection(self.local_config_file)
            cloud_conn = self.get_connection(self.cloud_config_file)
            
            try:
                # Obtener listas de tablas
                local_tables = set(self.get_all_tables(local_conn))
                cloud_tables = set(self.get_all_tables(cloud_conn))
                
                self.logger.info(f"Tablas en base local: {len(local_tables)}")
                self.logger.info(f"Tablas en base nube: {len(cloud_tables)}")
                
                # Identificar diferencias en tablas
                missing_tables = list(local_tables - cloud_tables)
                extra_tables = list(cloud_tables - local_tables)
                common_tables = list(local_tables & cloud_tables)
                
                if missing_tables:
                    self.logger.warning(f"Tablas que faltan en la nube: {', '.join(missing_tables)}")
                if extra_tables:
                    self.logger.warning(f"Tablas extra en la nube: {', '.join(extra_tables)}")
                    
                # Validar estructuras de tablas comunes
                column_differences = {}
                for table in common_tables:
                    local_table_info = self.get_table_info(local_conn, table)
                    cloud_table_info = self.get_table_info(cloud_conn, table)
                    
                    differences = self.compare_columns(
                        local_table_info.columns, 
                        cloud_table_info.columns
                    )
                    
                    if differences:
                        column_differences[table] = differences
                        self.logger.warning(f"Diferencias en tabla '{table}': {len(differences)} encontradas")
                        
                # Clasificar problemas
                fixable_issues = []
                critical_issues = []
                
                # Las tablas faltantes son críticas
                if missing_tables:
                    critical_issues.extend([f"Tabla faltante: {table}" for table in missing_tables])
                    
                # Las diferencias de columnas pueden ser reparables
                for table, diffs in column_differences.items():
                    for diff in diffs:
                        if "falta en la nube" in diff:
                            fixable_issues.append(f"{table}: {diff}")
                        else:
                            critical_issues.append(f"{table}: {diff}")
                            
                # Crear resultado
                result = ValidationResult(
                    is_valid=(not missing_tables and not column_differences),
                    missing_tables=missing_tables,
                    extra_tables=extra_tables,
                    column_differences=column_differences,
                    foreign_key_issues=[],  # Por implementar
                    fixable_issues=fixable_issues,
                    critical_issues=critical_issues
                )
                
                # Log del resultado
                if result.is_valid:
                    self.logger.info("Validación exitosa: Los esquemas son compatibles")
                else:
                    self.logger.warning(f"Validación falló: {len(result.critical_issues)} problemas críticos, {len(result.fixable_issues)} reparables")
                    
                return result
                
            finally:
                local_conn.close()
                cloud_conn.close()
                
        except Exception as e:
            self.logger.error(f"Error durante la validación: {e}")
            return ValidationResult(
                is_valid=False,
                missing_tables=[],
                extra_tables=[],
                column_differences={},
                foreign_key_issues=[],
                fixable_issues=[],
                critical_issues=[f"Error de validación: {e}"]
            )
            
    def create_missing_tables(self) -> bool:
        """Crea las tablas que faltan en la base de datos en la nube."""
        self.logger.info("=== CREANDO TABLAS FALTANTES EN LA NUBE ===")
        
        try:
            local_conn = self.get_connection(self.local_config_file)
            cloud_conn = self.get_connection(self.cloud_config_file)
            
            try:
                # Obtener listas de tablas
                local_tables = set(self.get_all_tables(local_conn))
                cloud_tables = set(self.get_all_tables(cloud_conn))
                missing_tables = list(local_tables - cloud_tables)
                
                if not missing_tables:
                    self.logger.info("No hay tablas faltantes para crear")
                    return True
                    
                self.logger.info(f"Creando {len(missing_tables)} tablas faltantes")
                
                # Obtener el esquema completo de la base local
                with local_conn.cursor() as local_cursor:
                    # Usar pg_dump para obtener solo la estructura
                    import subprocess
                    import os
                    
                    # Encontrar pg_dump
                    pg_dump_path = self.find_pg_dump()
                    if not pg_dump_path:
                        self.logger.error("No se pudo encontrar pg_dump")
                        return False
                        
                    # Configuración local
                    local_config = self.load_config(self.local_config_file)
                    
                    # Crear archivo temporal con el esquema
                    schema_file = f"temp_schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
                    
                    cmd = [
                        pg_dump_path,
                        '-h', local_config['host'],
                        '-p', local_config.get('port', '5432'),
                        '-U', local_config['user'],
                        '-d', local_config['database'],
                        '--schema-only',
                        '--no-owner',
                        '--no-privileges',
                        '--file', schema_file
                    ]
                    
                    env = os.environ.copy()
                    env['PGPASSWORD'] = local_config['password']
                    
                    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        # Leer el archivo de esquema y aplicarlo a la nube
                        with open(schema_file, 'r', encoding='utf-8') as f:
                            schema_sql = f.read()
                            
                        # Aplicar el esquema a la base en la nube
                        with cloud_conn.cursor() as cloud_cursor:
                            cloud_cursor.execute(schema_sql)
                            cloud_conn.commit()
                            
                        self.logger.info("Esquema aplicado exitosamente a la base en la nube")
                        
                        # Limpiar archivo temporal
                        os.remove(schema_file)
                        
                        return True
                    else:
                        self.logger.error(f"Error obteniendo esquema: {result.stderr}")
                        return False
                        
            finally:
                local_conn.close()
                cloud_conn.close()
                
        except Exception as e:
            self.logger.error(f"Error creando tablas: {e}")
            return False
            
    def find_pg_dump(self) -> str:
        """Encuentra la ubicación de pg_dump en el sistema."""
        import os
        import subprocess
        
        # Ubicaciones comunes de PostgreSQL en Windows
        common_paths = [
            r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
            r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
            r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
            r"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe",
            r"C:\Program Files\PostgreSQL\13\bin\pg_dump.exe",
        ]
        
        # Primero intentar desde PATH
        try:
            result = subprocess.run(['where', 'pg_dump'], capture_output=True, text=True, shell=True)
            if result.returncode == 0:
                pg_dump_path = result.stdout.strip().split('\n')[0]
                if os.path.exists(pg_dump_path):
                    return pg_dump_path
        except:
            pass
            
        # Buscar en ubicaciones comunes
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        return None
        
    def fix_schema_differences(self) -> bool:
        """Corrige automáticamente las diferencias de esquema reparables."""
        self.logger.info("=== CORRIGIENDO DIFERENCIAS DE ESQUEMA ===")
        
        # Primero validar para identificar problemas
        validation_result = self.validate_table_structures()
        
        if validation_result.is_valid:
            self.logger.info("No hay diferencias que corregir")
            return True
            
        # Si hay tablas faltantes, crearlas
        if validation_result.missing_tables:
            if not self.create_missing_tables():
                return False
                
        # Validar nuevamente después de las correcciones
        final_validation = self.validate_table_structures()
        
        if final_validation.is_valid:
            self.logger.info("Todas las diferencias fueron corregidas exitosamente")
            return True
        else:
            self.logger.warning("Algunas diferencias no pudieron ser corregidas automáticamente")
            return False
            
    def run_validation(self) -> ValidationResult:
        """Ejecuta el proceso completo de validación."""
        try:
            return self.validate_table_structures()
        except Exception as e:
            self.logger.error(f"Error inesperado durante la validación: {e}")
            return ValidationResult(
                is_valid=False,
                missing_tables=[],
                extra_tables=[],
                column_differences={},
                foreign_key_issues=[],
                fixable_issues=[],
                critical_issues=[f"Error inesperado: {e}"]
            )


def main():
    """Función principal."""
    print("=== VALIDADOR DE ESQUEMAS DE BASE DE DATOS ===")
    print("Validando compatibilidad entre base local y nube...")
    print()
    
    # Configurar archivos
    local_config = "config(1).ini"
    cloud_config = "config.ini"
    
    # Ejecutar validación
    validator = SchemaValidator(local_config, cloud_config)
    result = validator.run_validation()
    
    # Mostrar resultados
    print("\n" + "=" * 50)
    if result.is_valid:
        print("✅ VALIDACIÓN EXITOSA")
        print("Los esquemas son compatibles para la migración.")
    else:
        print("❌ VALIDACIÓN FALLÓ")
        print(f"Problemas encontrados:")
        
        if result.missing_tables:
            print(f"  - Tablas faltantes: {len(result.missing_tables)}")
            
        if result.column_differences:
            print(f"  - Tablas con diferencias: {len(result.column_differences)}")
            
        if result.critical_issues:
            print(f"  - Problemas críticos: {len(result.critical_issues)}")
            
        if result.fixable_issues:
            print(f"  - Problemas reparables: {len(result.fixable_issues)}")
            
        # Preguntar si se desea intentar reparar
        if result.fixable_issues or result.missing_tables:
            response = input("\n¿Desea intentar corregir automáticamente? (s/n): ")
            if response.lower() == 's':
                print("\nIntentando correcciones automáticas...")
                if validator.fix_schema_differences():
                    print("✅ Correcciones aplicadas exitosamente")
                else:
                    print("❌ Algunas correcciones fallaron")
                    
    return result.is_valid


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)