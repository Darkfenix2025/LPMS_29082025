"""
Report Manager - Módulo de lógica de negocio para generación de reportes
"""

import csv
import os
from tkinter import filedialog, messagebox
import crm_database as db
import logging
from xlsx_report_formatter import XLSXReportFormatter

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('report_manager')

class ReportManager:
    """
    Clase que maneja la lógica de negocio para la generación de reportes.
    """
    
    def __init__(self, app_controller):
        """
        Inicializa el ReportManager.
        
        Args:
            app_controller: Referencia al controlador principal de la aplicación
        """
        self.app_controller = app_controller
        self.xlsx_formatter = XLSXReportFormatter()
        
        # Definición de columnas disponibles
        self.COLUMNAS_BASICAS = {
            'numero_expediente_anio': 'N° Expediente y Año',
            'caratula': 'Carátula',
            'juzgado': 'Juzgado',
            'etapa_procesal': 'Etapa Procesal'
        }
        
        self.COLUMNAS_ENRIQUECIDAS = {
            'partes_intervinientes': 'Partes Intervinientes (Actores y Demandados)',
            'ultimo_movimiento': 'Último Movimiento Procesal',
            'notas': 'Notas del Caso'
        }
    
    def get_report_data(self, cliente_id, columnas_seleccionadas):
        """
        Obtiene y enriquece los datos para el reporte sin generar un archivo.
        
        Args:
            cliente_id (int or None): ID del cliente para filtrar, None para todos.
            columnas_seleccionadas (list): Lista de claves de columnas a incluir.
            
        Returns:
            list: Lista de diccionarios con los datos de los casos enriquecidos.
        """
        logger.info(f"Obteniendo datos para reporte. Cliente ID: {cliente_id}")
        casos = self._get_base_case_data(cliente_id)
        if not casos:
            logger.info("No se encontraron casos base para los criterios seleccionados.")
            return []
        
        logger.info(f"Obtenidos {len(casos)} casos base. Enriqueciendo...")
        casos_enriquecidos = self._enrich_case_data(casos, columnas_seleccionadas)
        return casos_enriquecidos

    def generar_reporte_casos_xlsx(self, cliente_id, columnas_seleccionadas):
        """
        Genera un reporte de casos en formato XLSX con formato profesional.
        
        Args:
            cliente_id (int or None): ID del cliente para filtrar, None para todos
            columnas_seleccionadas (list): Lista de claves de columnas a incluir
            
        Returns:
            bool: True si el reporte se generó exitosamente, False en caso contrario
        """
        try:
            logger.info(f"Iniciando generación de reporte XLSX para cliente_id: {cliente_id}")
            
            casos_enriquecidos = self.get_report_data(cliente_id, columnas_seleccionadas)
            
            if not casos_enriquecidos:
                messagebox.showinfo(
                    "Sin datos", 
                    "No se encontraron casos activos para los criterios seleccionados.",
                    parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
                )
                return False
            
            return self._export_to_xlsx(casos_enriquecidos, columnas_seleccionadas)
            
        except Exception as e:
            logger.error(f"Error al generar reporte XLSX: {e}")
            messagebox.showerror(
                "Error", 
                f"Error al generar el reporte: {str(e)}",
                parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
            )
            return False
    
    def _get_base_case_data(self, cliente_id):
        """
        Obtiene los datos base de casos desde la base de datos.
        
        Args:
            cliente_id (int or None): ID del cliente para filtrar
            
        Returns:
            list: Lista de diccionarios con datos de casos
        """
        try:
            return db.get_casos_para_reporte(cliente_id)
        except Exception as e:
            logger.error(f"Error al obtener datos base de casos: {e}")
            raise
    
    def _enrich_case_data(self, casos, columnas_seleccionadas):
        """
        Enriquece los datos de casos con información adicional según las columnas seleccionadas.
        
        Args:
            casos (list): Lista de casos base
            columnas_seleccionadas (list): Columnas seleccionadas por el usuario
            
        Returns:
            list: Lista de casos enriquecidos
        """
        logger.info("Enriqueciendo datos de casos...")
        
        for caso in casos:
            try:
                # Agregar partes intervinientes si fue seleccionado
                if 'partes_intervinientes' in columnas_seleccionadas:
                    caso['partes_intervinientes'] = self._format_partes_data(caso['caso_id'])
                
                # Agregar último movimiento si fue seleccionado
                if 'ultimo_movimiento' in columnas_seleccionadas:
                    caso['ultimo_movimiento'] = self._get_ultimo_movimiento(caso['caso_id'])
                    
            except Exception as e:
                logger.warning(f"Error al enriquecer caso {caso['caso_id']}: {e}")
                # Continuar con valores por defecto en caso de error
                if 'partes_intervinientes' in columnas_seleccionadas:
                    caso['partes_intervinientes'] = "Error al obtener datos"
                if 'ultimo_movimiento' in columnas_seleccionadas:
                    caso['ultimo_movimiento'] = "Error al obtener datos"
        
        return casos
    
    def _format_partes_data(self, caso_id):
        """
        Formatea los datos de partes intervinientes para un caso.
        
        Args:
            caso_id (int): ID del caso
            
        Returns:
            str: String formateado con las partes del caso
        """
        try:
            roles = db.get_roles_by_caso_id(caso_id, incluir_jerarquia=False)
            
            if not roles:
                return "Sin partes registradas"
            
            # Agrupar por tipo de rol
            actores = []
            demandados = []
            otros = []
            
            for rol in roles:
                nombre = rol.get('nombre_completo', 'Sin nombre')
                rol_principal = rol.get('rol_principal', 'Sin rol')
                
                if rol_principal == 'Actor':
                    actores.append(nombre)
                elif rol_principal == 'Demandado':
                    demandados.append(nombre)
                else:
                    otros.append(f"{nombre} ({rol_principal})")
            
            # Construir string formateado
            partes_str = []
            if actores:
                partes_str.append(f"Actores: {', '.join(actores)}")
            if demandados:
                partes_str.append(f"Demandados: {', '.join(demandados)}")
            if otros:
                partes_str.append(f"Otros: {', '.join(otros)}")
            
            return ". ".join(partes_str) if partes_str else "Sin partes registradas"
            
        except Exception as e:
            logger.error(f"Error al formatear partes para caso {caso_id}: {e}")
            return "Error al obtener partes"
    
    def _get_ultimo_movimiento(self, caso_id):
        """
        Obtiene el último movimiento procesal de un caso.
        
        Args:
            caso_id (int): ID del caso
            
        Returns:
            str: Último movimiento formateado
        """
        try:
            return db.get_ultimo_movimiento_por_caso_id(caso_id)
        except Exception as e:
            logger.error(f"Error al obtener último movimiento para caso {caso_id}: {e}")
            return "Error al obtener movimiento"
    
    def _export_to_xlsx(self, data, columnas_seleccionadas):
        """
        Exporta los datos a un archivo XLSX con formato profesional.
        
        Args:
            data (list): Datos a exportar
            columnas_seleccionadas (list): Columnas seleccionadas
            
        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            # Solicitar ubicación del archivo
            archivo_xlsx = filedialog.asksaveasfilename(
                title="Guardar reporte como...",
                defaultextension=".xlsx",
                filetypes=[("Archivos Excel", "*.xlsx"), ("Todos los archivos", "*.*")],
                parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
            )
            
            if not archivo_xlsx:
                logger.info("Usuario canceló la selección de archivo")
                return False
            
            # Preparar información de columnas
            columns_info = {}
            
            # Agregar siempre el nombre del cliente al inicio
            if 'nombre_cliente' not in columnas_seleccionadas:
                columns_info['nombre_cliente'] = 'Cliente'
            
            # Agregar columnas seleccionadas
            for col_key in columnas_seleccionadas:
                if col_key in self.COLUMNAS_BASICAS:
                    columns_info[col_key] = self.COLUMNAS_BASICAS[col_key]
                elif col_key in self.COLUMNAS_ENRIQUECIDAS:
                    columns_info[col_key] = self.COLUMNAS_ENRIQUECIDAS[col_key]
            
            # Crear reporte XLSX usando el formateador
            success = self.xlsx_formatter.create_report(data, columns_info, archivo_xlsx)
            
            if success:
                logger.info(f"Reporte XLSX exportado exitosamente a: {archivo_xlsx}")
                messagebox.showinfo(
                    "Éxito", 
                    f"Reporte generado exitosamente.\nArchivo guardado en: {archivo_xlsx}",
                    parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
                )
                return True
            else:
                raise Exception("Error en el formateador XLSX")
            
        except Exception as e:
            logger.error(f"Error al exportar XLSX: {e}")
            messagebox.showerror(
                "Error de exportación", 
                f"Error al guardar el archivo Excel: {str(e)}",
                parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
            )
            return False
    
    def _export_to_csv_fallback(self, data, columnas_seleccionadas):
        """
        Exporta los datos a un archivo CSV (método de fallback).
        
        Args:
            data (list): Datos a exportar
            columnas_seleccionadas (list): Columnas seleccionadas
            
        Returns:
            bool: True si la exportación fue exitosa
        """
        try:
            # Solicitar ubicación del archivo
            archivo_csv = filedialog.asksaveasfilename(
                title="Guardar reporte como...",
                defaultextension=".csv",
                filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
                parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
            )
            
            if not archivo_csv:
                logger.info("Usuario canceló la selección de archivo")
                return False
            
            # Preparar encabezados
            encabezados = []
            campos_mapeados = []
            
            # Agregar columnas básicas
            for col_key in columnas_seleccionadas:
                if col_key in self.COLUMNAS_BASICAS:
                    encabezados.append(self.COLUMNAS_BASICAS[col_key])
                    campos_mapeados.append(col_key)
                elif col_key in self.COLUMNAS_ENRIQUECIDAS:
                    encabezados.append(self.COLUMNAS_ENRIQUECIDAS[col_key])
                    campos_mapeados.append(col_key)
            
            # Agregar siempre el nombre del cliente
            if 'nombre_cliente' not in campos_mapeados:
                encabezados.insert(0, 'Cliente')
                campos_mapeados.insert(0, 'nombre_cliente')
            
            # Escribir archivo CSV
            with open(archivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Escribir encabezados
                writer.writerow(encabezados)
                
                # Escribir datos
                for caso in data:
                    fila = []
                    for campo in campos_mapeados:
                        if campo == 'numero_expediente_anio':
                            # Combinar número de expediente y año
                            numero = caso.get('numero_expediente', '') or ''
                            anio = caso.get('anio_caratula', '') or ''
                            valor = f"{numero}/{anio}" if numero and anio else numero or anio or 'N/A'
                        else:
                            valor = caso.get(campo, '') or 'N/A'
                        fila.append(str(valor))
                    writer.writerow(fila)
            
            logger.info(f"Reporte exportado exitosamente a: {archivo_csv}")
            messagebox.showinfo(
                "Éxito", 
                f"Reporte generado exitosamente.\nArchivo guardado en: {archivo_csv}",
                parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
            )
            return True
            
        except Exception as e:
            logger.error(f"Error al exportar CSV: {e}")
            messagebox.showerror(
                "Error de exportación", 
                f"Error al guardar el archivo CSV: {str(e)}",
                parent=self.app_controller.root if hasattr(self.app_controller, 'root') else None
            )
            return False