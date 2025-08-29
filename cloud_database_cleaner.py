#!/usr/bin/env python3
"""
Cloud Database Cleaner
Limpia completamente la base de datos en la nube para preparar una migración fresca.
Los datos locales se mantienen intactos y protegidos.
"""

import psycopg2
import configparser
import logging
from typing import List, Tuple
import sys
from datetime import datetime

class CloudDatabaseCleaner:
    def __init__(self, local_config_file: str, cloud_config_file: str):
        """
        Inicializa el limpiador con las configuraciones de ambas bases de datos.
        
        Args:
            local_config_file: Archivo de configuración para la base local (solo para verificación)
            cloud_config_file: Archivo de configuración para la base en la nube
        """
        self.local_config_file = local_config_file
        self.cloud_config_file = cloud_config_file
        self.setup_logging()
        
    def setup_logging(self):
        """Configura el sistema de logging."""
        # Crear handlers con codificación UTF-8
        file_handler = logging.FileHandler(
            f'cloud_cleanup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
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
        
    def test_local_connection(self) -> bool:
        """
        Verifica que la conexión local funcione correctamente.
        Esto es una medida de seguridad para asegurar que los datos locales estén accesibles.
        """
        try:
            local_config = self.load_config(self.local_config_file)
            conn = psycopg2.connect(**local_config)
            
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
                table_count = cursor.fetchone()[0]
                
            conn.close()
            self.logger.info(f"✓ Conexión local verificada. {table_count} tablas encontradas.")
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Error conectando a la base local: {e}")
            return False
            
    def get_cloud_connection(self):
        """Obtiene una conexión a la base de datos en la nube."""
        cloud_config = self.load_config(self.cloud_config_file)
        return psycopg2.connect(**cloud_config)
        
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
            
    def get_table_dependencies(self, conn) -> List[Tuple[str, str]]:
        """
        Obtiene las dependencias de llaves foráneas entre tablas.
        Retorna una lista de tuplas (tabla_dependiente, tabla_referenciada).
        """
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    tc.table_name as dependent_table,
                    ccu.table_name as referenced_table
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu 
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                ORDER BY tc.table_name, ccu.table_name
            """)
            return cursor.fetchall()
            
    def calculate_deletion_order(self, tables: List[str], dependencies: List[Tuple[str, str]]) -> List[str]:
        """
        Calcula el orden correcto para eliminar las tablas respetando las dependencias.
        Las tablas dependientes se eliminan antes que las tablas referenciadas.
        """
        # Crear un grafo de dependencias
        dependents = {}
        for table in tables:
            dependents[table] = set()
            
        for dependent, referenced in dependencies:
            if dependent in dependents and referenced in dependents:
                dependents[referenced].add(dependent)
                
        # Ordenamiento topológico
        deletion_order = []
        remaining = set(tables)
        
        while remaining:
            # Encontrar tablas sin dependientes
            no_dependents = [table for table in remaining if not dependents[table] & remaining]
            
            if not no_dependents:
                # Si hay ciclos, eliminar todas las restantes (con CASCADE)
                deletion_order.extend(list(remaining))
                break
                
            # Agregar al orden de eliminación
            deletion_order.extend(no_dependents)
            
            # Remover de remaining
            for table in no_dependents:
                remaining.remove(table)
                
        return deletion_order
        
    def drop_all_tables(self, conn) -> bool:
        """
        Elimina todas las tablas de la base de datos usando CASCADE.
        """
        try:
            tables = self.get_all_tables(conn)
            if not tables:
                self.logger.info("No hay tablas para eliminar en la base de datos en la nube.")
                return True
                
            self.logger.info(f"Encontradas {len(tables)} tablas para eliminar: {', '.join(tables)}")
            
            with conn.cursor() as cursor:
                deleted_count = 0
                
                # Intentar eliminar todas las tablas con CASCADE
                # Esto debería manejar las dependencias automáticamente
                for table in tables:
                    try:
                        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                        deleted_count += 1
                        self.logger.info(f"Tabla eliminada: {table}")
                    except Exception as e:
                        self.logger.warning(f"Error eliminando tabla {table}: {e}")
                        
                conn.commit()
                
            # Verificar que todas las tablas fueron eliminadas
            remaining_tables = self.get_all_tables(conn)
            if remaining_tables:
                self.logger.warning(f"Quedan {len(remaining_tables)} tablas: {', '.join(remaining_tables)}")
                
                # Intentar una segunda pasada para las tablas restantes
                with conn.cursor() as cursor:
                    for table in remaining_tables:
                        try:
                            cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                            deleted_count += 1
                            self.logger.info(f"Tabla eliminada (segunda pasada): {table}")
                        except Exception as e:
                            self.logger.error(f"No se pudo eliminar tabla {table}: {e}")
                    conn.commit()
                
            self.logger.info(f"Eliminación completada. {deleted_count} tablas procesadas.")
            
            # Verificación final
            final_tables = self.get_all_tables(conn)
            if not final_tables:
                self.logger.info("Todas las tablas eliminadas exitosamente.")
                return True
            else:
                self.logger.error(f"Quedan {len(final_tables)} tablas sin eliminar: {', '.join(final_tables)}")
                return False
            
        except Exception as e:
            self.logger.error(f"Error durante la eliminación de tablas: {e}")
            conn.rollback()
            return False
            
    def clean_cloud_database(self) -> bool:
        """
        Proceso principal para limpiar la base de datos en la nube.
        """
        self.logger.info("=== INICIANDO LIMPIEZA DE BASE DE DATOS EN LA NUBE ===")
        
        # 1. Verificar que la base local esté accesible
        self.logger.info("Paso 1: Verificando acceso a la base de datos local...")
        if not self.test_local_connection():
            self.logger.error("✗ No se puede acceder a la base local. Abortando por seguridad.")
            return False
            
        # 2. Conectar a la base en la nube
        self.logger.info("Paso 2: Conectando a la base de datos en la nube...")
        try:
            cloud_conn = self.get_cloud_connection()
            self.logger.info("✓ Conexión a la nube establecida.")
        except Exception as e:
            self.logger.error(f"✗ Error conectando a la nube: {e}")
            return False
            
        try:
            # 3. Eliminar todas las tablas
            self.logger.info("Paso 3: Eliminando todas las tablas de la base en la nube...")
            if not self.drop_all_tables(cloud_conn):
                return False
                
            # 4. Verificar que la limpieza fue exitosa
            remaining_tables = self.get_all_tables(cloud_conn)
            if remaining_tables:
                self.logger.warning(f"⚠ Quedan {len(remaining_tables)} tablas: {', '.join(remaining_tables)}")
            else:
                self.logger.info("✓ Base de datos en la nube completamente limpia.")
                
            return True
            
        finally:
            cloud_conn.close()
            self.logger.info("Conexión a la nube cerrada.")
            
    def run(self) -> bool:
        """Ejecuta el proceso completo de limpieza."""
        try:
            return self.clean_cloud_database()
        except Exception as e:
            self.logger.error(f"✗ Error inesperado: {e}")
            return False


def main():
    """Función principal."""
    print("=== LIMPIADOR DE BASE DE DATOS EN LA NUBE ===")
    print("Este script eliminará TODOS los datos de la base de datos en la nube.")
    print("Los datos locales permanecerán intactos y protegidos.")
    print()
    
    # Confirmar la operación
    response = input("¿Está seguro de que desea continuar? (escriba 'SI' para confirmar): ")
    if response != 'SI':
        print("Operación cancelada.")
        return
        
    # Configurar archivos
    local_config = "config(1).ini"  # Base local
    cloud_config = "config.ini"     # Base en la nube
    
    # Ejecutar limpieza
    cleaner = CloudDatabaseCleaner(local_config, cloud_config)
    success = cleaner.run()
    
    if success:
        print("\n✓ LIMPIEZA COMPLETADA EXITOSAMENTE")
        print("La base de datos en la nube está lista para una migración fresca.")
    else:
        print("\n✗ LIMPIEZA FALLÓ")
        print("Revise los logs para más detalles.")
        
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)