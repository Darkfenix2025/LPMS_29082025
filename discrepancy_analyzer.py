#!/usr/bin/env python3
"""
Analizador de Discrepancias
===========================

Compara la estructura del backup local con la base de datos actual
para identificar problemas de asignación de partes y IDs de casos.

Autor: CRM Legal System
Fecha: 2025
"""

import sys
import os
import json
import configparser
import psycopg2
import psycopg2.extras
from typing import Dict, List, Tuple

class DiscrepancyAnalyzer:
    def __init__(self):
        self.cloud_db_config = None
        self.backup_data = {}
        self.current_data = {}
        self.discrepancies = {}
        
    def load_cloud_database_config(self) -> bool:
        """Carga la configuración de la base de datos en la nube."""
        try:
            config = configparser.ConfigParser()
            config.read('config.ini')  # Configuración de la nube
            
            if 'postgresql' not in config:
                print("❌ No se encontró configuración postgresql en config.ini")
                return False
                
            self.cloud_db_config = {
                'host': config.get('postgresql', 'host'),
                'port': config.get('postgresql', 'port', fallback='5432'),
                'database': config.get('postgresql', 'database'),
                'user': config.get('postgresql', 'user'),
                'password': config.get('postgresql', 'password'),
                'sslmode': config.get('postgresql', 'sslmode', fallback='require')
            }
            
            print(f"✅ Configuración de nube cargada: {self.cloud_db_config['database']} en {self.cloud_db_config['host']}")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando configuración de nube: {e}")
            return False
    
    def load_backup_analysis(self) -> bool:
        """Carga los resultados del análisis del backup."""
        try:
            if not os.path.exists('backup_analysis_results.json'):
                print("❌ No se encontró backup_analysis_results.json")
                print("   Ejecuta primero backup_analyzer.py")
                return False
                
            with open('backup_analysis_results.json', 'r', encoding='utf-8') as f:
                self.backup_data = json.load(f)
                
            print(f"✅ Datos del backup cargados:")
            print(f"   Casos: {len(self.backup_data.get('casos', []))}")
            print(f"   Partes: {len(self.backup_data.get('partes_assignments', []))}")
            print(f"   Roles: {len(self.backup_data.get('roles_assignments', []))}")
            print(f"   Casos genéricos: {self.backup_data.get('generic_cases', [])}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error cargando análisis del backup: {e}")
            return False
    
    def analyze_current_database(self) -> bool:
        """Analiza la estructura actual de la base de datos en la nube."""
        try:
            print("🔍 Analizando base de datos actual en la nube...")
            
            conn = psycopg2.connect(
                host=self.cloud_db_config['host'],
                port=self.cloud_db_config['port'],
                database=self.cloud_db_config['database'],
                user=self.cloud_db_config['user'],
                password=self.cloud_db_config['password'],
                sslmode=self.cloud_db_config['sslmode']
            )
            
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. Analizar casos actuales
                print("📋 Analizando casos actuales...")
                cur.execute("""
                    SELECT id, caratula, cliente_id, created_at
                    FROM casos 
                    ORDER BY id
                """)
                casos_actuales = cur.fetchall()
                
                self.current_data['casos'] = []
                for caso in casos_actuales:
                    self.current_data['casos'].append({
                        'id': caso['id'],
                        'caratula': caso['caratula'],
                        'cliente_id': caso['cliente_id'],
                        'created_at': caso['created_at']
                    })
                
                print(f"  Total casos actuales: {len(casos_actuales)}")
                
                # 2. Analizar clientes actuales
                print("👥 Analizando clientes actuales...")
                cur.execute("""
                    SELECT id, nombre, direccion, email
                    FROM clientes 
                    ORDER BY id
                """)
                clientes_actuales = cur.fetchall()
                
                self.current_data['clientes'] = []
                generic_client_ids = []
                
                for cliente in clientes_actuales:
                    self.current_data['clientes'].append({
                        'id': cliente['id'],
                        'nombre': cliente['nombre'],
                        'direccion': cliente['direccion'],
                        'email': cliente['email']
                    })
                    
                    # Identificar clientes genéricos
                    if ('audiencia' in cliente['nombre'].lower() or
                        '00 -' in cliente['nombre'] or
                        'generico' in cliente['nombre'].lower()):
                        generic_client_ids.append(cliente['id'])
                
                print(f"  Total clientes actuales: {len(clientes_actuales)}")
                print(f"  Clientes genéricos actuales: {generic_client_ids}")
                
                # 3. Identificar casos genéricos actuales
                generic_case_ids = []
                for caso in self.current_data['casos']:
                    if caso['cliente_id'] in generic_client_ids:
                        generic_case_ids.append(caso['id'])
                
                self.current_data['generic_cases'] = generic_case_ids
                print(f"  Casos genéricos actuales: {generic_case_ids}")
                
                # 4. Analizar roles actuales
                print("👔 Analizando roles actuales...")
                cur.execute("""
                    SELECT r.id, r.caso_id, r.contacto_id, r.rol_principal, c.nombre_completo
                    FROM roles_en_caso r
                    LEFT JOIN contactos c ON r.contacto_id = c.id
                    ORDER BY r.caso_id, r.id
                """)
                roles_actuales = cur.fetchall()
                
                self.current_data['roles_assignments'] = []
                for rol in roles_actuales:
                    self.current_data['roles_assignments'].append({
                        'rol_id': rol['id'],
                        'caso_id': rol['caso_id'],
                        'contacto_id': rol['contacto_id'],
                        'rol_principal': rol['rol_principal'],
                        'nombre_completo': rol['nombre_completo']
                    })
                
                print(f"  Total roles actuales: {len(roles_actuales)}")
                
                # 5. Verificar roles en casos genéricos actuales
                roles_en_genericos = [r for r in self.current_data['roles_assignments'] 
                                    if r['caso_id'] in generic_case_ids]
                
                if roles_en_genericos:
                    print(f"  ⚠️ Roles en casos genéricos actuales: {len(roles_en_genericos)}")
                    for rol in roles_en_genericos:
                        print(f"    - {rol['nombre_completo']} en caso {rol['caso_id']}")
                else:
                    print(f"  ✅ No hay roles en casos genéricos actuales")
                
                return True
                
        except Exception as e:
            print(f"❌ Error analizando base de datos actual: {e}")
            return False
            
        finally:
            if 'conn' in locals():
                conn.close()
    
    def compare_case_structures(self) -> Dict:
        """Compara las estructuras de casos entre backup y actual."""
        print("🔍 Comparando estructuras de casos...")
        
        backup_casos = {c['id']: c for c in self.backup_data.get('casos', [])}
        current_casos = {c['id']: c for c in self.current_data.get('casos', [])}
        
        comparison = {
            'backup_range': (min(backup_casos.keys()), max(backup_casos.keys())) if backup_casos else (0, 0),
            'current_range': (min(current_casos.keys()), max(current_casos.keys())) if current_casos else (0, 0),
            'backup_count': len(backup_casos),
            'current_count': len(current_casos),
            'id_conflicts': [],
            'missing_in_current': [],
            'extra_in_current': [],
            'generic_case_mismatch': {}
        }
        
        print(f"  Backup: {comparison['backup_count']} casos (IDs {comparison['backup_range'][0]}-{comparison['backup_range'][1]})")
        print(f"  Actual: {comparison['current_count']} casos (IDs {comparison['current_range'][0]}-{comparison['current_range'][1]})")
        
        # Identificar conflictos de IDs
        for caso_id in backup_casos:
            if caso_id in current_casos:
                backup_caso = backup_casos[caso_id]
                current_caso = current_casos[caso_id]
                
                if backup_caso['caratula'] != current_caso['caratula']:
                    comparison['id_conflicts'].append({
                        'id': caso_id,
                        'backup_caratula': backup_caso['caratula'],
                        'current_caratula': current_caso['caratula']
                    })
        
        # Casos faltantes en actual
        for caso_id in backup_casos:
            if caso_id not in current_casos:
                comparison['missing_in_current'].append(backup_casos[caso_id])
        
        # Casos extra en actual
        for caso_id in current_casos:
            if caso_id not in backup_casos:
                comparison['extra_in_current'].append(current_casos[caso_id])
        
        # Comparar casos genéricos
        backup_generic = set(self.backup_data.get('generic_cases', []))
        current_generic = set(self.current_data.get('generic_cases', []))
        
        comparison['generic_case_mismatch'] = {
            'backup_generic': list(backup_generic),
            'current_generic': list(current_generic),
            'should_be_generic': list(backup_generic - current_generic),
            'should_not_be_generic': list(current_generic - backup_generic)
        }
        
        print(f"  Conflictos de ID: {len(comparison['id_conflicts'])}")
        print(f"  Faltantes en actual: {len(comparison['missing_in_current'])}")
        print(f"  Extra en actual: {len(comparison['extra_in_current'])}")
        print(f"  Casos genéricos incorrectos: {len(comparison['generic_case_mismatch']['should_not_be_generic'])}")
        
        return comparison
    
    def analyze_parts_assignments(self) -> Dict:
        """Analiza las asignaciones incorrectas de partes."""
        print("🎭 Analizando asignaciones de partes...")
        
        analysis = {
            'roles_in_generic_cases': [],
            'incorrect_assignments': [],
            'case_203_analysis': None
        }
        
        # 1. Roles en casos genéricos (problema principal)
        current_generic_cases = set(self.current_data.get('generic_cases', []))
        roles_in_generics = [
            r for r in self.current_data.get('roles_assignments', [])
            if r['caso_id'] in current_generic_cases
        ]
        
        analysis['roles_in_generic_cases'] = roles_in_generics
        
        print(f"  Roles en casos genéricos: {len(roles_in_generics)}")
        for rol in roles_in_generics:
            print(f"    - {rol['nombre_completo']} en caso genérico {rol['caso_id']}")
        
        # 2. Análisis específico del caso 203
        caso_203_roles = [
            r for r in self.current_data.get('roles_assignments', [])
            if r['caso_id'] == 203
        ]
        
        if caso_203_roles:
            # Buscar el caso 203 en los datos actuales
            caso_203_info = next((c for c in self.current_data.get('casos', []) if c['id'] == 203), None)
            
            analysis['case_203_analysis'] = {
                'caso_info': caso_203_info,
                'roles_count': len(caso_203_roles),
                'roles': caso_203_roles,
                'is_generic': 203 in current_generic_cases,
                'should_have_roles': False  # Los casos genéricos no deberían tener roles
            }
            
            print(f"\\n  📋 ANÁLISIS DEL CASO 203:")
            if caso_203_info:
                print(f"    Carátula: {caso_203_info['caratula']}")
                print(f"    Cliente ID: {caso_203_info['cliente_id']}")
            print(f"    Es genérico: {203 in current_generic_cases}")
            print(f"    Roles asignados: {len(caso_203_roles)}")
            for rol in caso_203_roles:
                print(f"      - {rol['nombre_completo']} ({rol['rol_principal']})")
        
        # 3. Buscar asignaciones que deberían estar en otros casos
        backup_partes = self.backup_data.get('partes_assignments', [])
        
        for rol in roles_in_generics:
            # Buscar si esta parte debería estar en otro caso según el backup
            nombre_parte = rol['nombre_completo']
            
            # Buscar en el backup dónde debería estar esta parte
            backup_assignment = next(
                (p for p in backup_partes if p['nombre'].strip().upper() == nombre_parte.strip().upper()),
                None
            )
            
            if backup_assignment:
                analysis['incorrect_assignments'].append({
                    'current_case_id': rol['caso_id'],
                    'correct_case_id': backup_assignment['caso_id'],
                    'nombre': nombre_parte,
                    'rol_id': rol['rol_id'],
                    'contacto_id': rol['contacto_id']
                })
        
        print(f"  Asignaciones incorrectas identificadas: {len(analysis['incorrect_assignments'])}")
        
        return analysis
    
    def generate_correction_plan(self) -> Dict:
        """Genera un plan de corrección basado en las discrepancias encontradas."""
        print("📋 Generando plan de corrección...")
        
        plan = {
            'cleanup_generic_cases': [],
            'reassign_parts': [],
            'case_id_corrections': [],
            'summary': {}
        }
        
        # 1. Limpiar casos genéricos
        for rol in self.discrepancies['parts_analysis']['roles_in_generic_cases']:
            plan['cleanup_generic_cases'].append({
                'action': 'remove_role',
                'rol_id': rol['rol_id'],
                'caso_id': rol['caso_id'],
                'nombre': rol['nombre_completo'],
                'reason': 'Caso genérico no debe tener partes'
            })
        
        # 2. Reasignar partes a casos correctos
        for assignment in self.discrepancies['parts_analysis']['incorrect_assignments']:
            plan['reassign_parts'].append({
                'action': 'move_role',
                'rol_id': assignment['rol_id'],
                'from_case_id': assignment['current_case_id'],
                'to_case_id': assignment['correct_case_id'],
                'nombre': assignment['nombre'],
                'reason': 'Restaurar asignación original del backup'
            })
        
        # 3. Resumen del plan
        plan['summary'] = {
            'roles_to_remove': len(plan['cleanup_generic_cases']),
            'roles_to_reassign': len(plan['reassign_parts']),
            'total_changes': len(plan['cleanup_generic_cases']) + len(plan['reassign_parts'])
        }
        
        print(f"  Roles a remover de casos genéricos: {plan['summary']['roles_to_remove']}")
        print(f"  Roles a reasignar: {plan['summary']['roles_to_reassign']}")
        print(f"  Total de cambios: {plan['summary']['total_changes']}")
        
        return plan
    
    def generate_report(self) -> str:
        """Genera un reporte completo de discrepancias."""
        report = []
        report.append("=" * 60)
        report.append("REPORTE DE DISCREPANCIAS - BACKUP vs ACTUAL")
        report.append("=" * 60)
        
        # Resumen de casos
        case_comparison = self.discrepancies['case_comparison']
        report.append(f"\\n📋 CASOS:")
        report.append(f"  Backup: {case_comparison['backup_count']} casos")
        report.append(f"  Actual: {case_comparison['current_count']} casos")
        report.append(f"  Conflictos de ID: {len(case_comparison['id_conflicts'])}")
        
        # Casos genéricos
        generic_mismatch = case_comparison['generic_case_mismatch']
        report.append(f"\\n🏷️ CASOS GENÉRICOS:")
        report.append(f"  En backup: {generic_mismatch['backup_generic']}")
        report.append(f"  En actual: {generic_mismatch['current_generic']}")
        report.append(f"  Incorrectamente genéricos: {generic_mismatch['should_not_be_generic']}")
        
        # Análisis de partes
        parts_analysis = self.discrepancies['parts_analysis']
        report.append(f"\\n🎭 PARTES:")
        report.append(f"  Roles en casos genéricos: {len(parts_analysis['roles_in_generic_cases'])}")
        report.append(f"  Asignaciones incorrectas: {len(parts_analysis['incorrect_assignments'])}")
        
        # Caso 203 específico
        if parts_analysis['case_203_analysis']:
            case_203 = parts_analysis['case_203_analysis']
            report.append(f"\\n📋 CASO 203 (PROBLEMA PRINCIPAL):")
            report.append(f"  Es genérico: {case_203['is_generic']}")
            report.append(f"  Roles asignados: {case_203['roles_count']} (debería ser 0)")
            if case_203['caso_info']:
                report.append(f"  Carátula: {case_203['caso_info']['caratula']}")
        
        # Plan de corrección
        correction_plan = self.discrepancies['correction_plan']
        report.append(f"\\n🔧 PLAN DE CORRECCIÓN:")
        report.append(f"  Roles a remover: {correction_plan['summary']['roles_to_remove']}")
        report.append(f"  Roles a reasignar: {correction_plan['summary']['roles_to_reassign']}")
        report.append(f"  Total cambios: {correction_plan['summary']['total_changes']}")
        
        return "\\n".join(report)

def main():
    """Función principal."""
    print("🔍 ANALIZADOR DE DISCREPANCIAS")
    print("=" * 50)
    
    analyzer = DiscrepancyAnalyzer()
    
    # 1. Cargar configuraciones
    if not analyzer.load_cloud_database_config():
        return False
    
    if not analyzer.load_backup_analysis():
        return False
    
    # 2. Analizar base de datos actual
    if not analyzer.analyze_current_database():
        return False
    
    # 3. Comparar estructuras
    analyzer.discrepancies = {}
    analyzer.discrepancies['case_comparison'] = analyzer.compare_case_structures()
    analyzer.discrepancies['parts_analysis'] = analyzer.analyze_parts_assignments()
    analyzer.discrepancies['correction_plan'] = analyzer.generate_correction_plan()
    
    # 4. Generar reporte
    report = analyzer.generate_report()
    print(f"\\n{report}")
    
    # 5. Guardar resultados
    with open('discrepancy_analysis_results.json', 'w', encoding='utf-8') as f:
        json.dump(analyzer.discrepancies, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\\n💾 Resultados guardados en discrepancy_analysis_results.json")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)