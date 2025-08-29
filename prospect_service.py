#!/usr/bin/env python3
"""
Prospect Service - Capa de servicio para la lógica de negocio de prospectos
Separa la lógica de negocio de la interfaz de usuario
"""

import datetime
from typing import Dict, List, Optional, Tuple, Any
import crm_database as db
import date_utils
from word_export_manager import WordExportManager
from conversion_service import ConversionService
from entidad_base import EntidadBase, EntidadFactory


class ProspectService:
    """Servicio que centraliza toda la lógica de negocio de prospectos"""
    
    def __init__(self):
        self.db = db
        self.word_export_manager = WordExportManager()
        self.conversion_service = ConversionService()
    
    # ========================================
    # VALIDACIÓN DE DATOS
    # ========================================
    
    def validar_datos_prospecto(self, datos: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Valida los datos de un prospecto antes de guardar.
        
        Args:
            datos (dict): Diccionario con los datos del prospecto
            
        Returns:
            tuple[bool, str]: (es_valido, mensaje_error)
        """
        # Validar nombre obligatorio
        nombre = datos.get('nombre', '').strip()
        if not nombre:
            return False, "El nombre del prospecto no puede estar vacío."
        
        # Validar longitud del nombre
        if len(nombre) > 255:
            return False, "El nombre del prospecto es demasiado largo (máximo 255 caracteres)."
        
        # Validar contacto si se proporciona
        contacto = datos.get('contacto', '').strip()
        if contacto and len(contacto) > 255:
            return False, "La información de contacto es demasiado larga (máximo 255 caracteres)."
        
        # Validar notas generales si se proporcionan
        notas_generales = datos.get('notas_generales', '').strip()
        if notas_generales and len(notas_generales) > 2000:
            return False, "Las notas generales son demasiado largas (máximo 2000 caracteres)."
        
        # Validar estado si se proporciona
        estado = datos.get('estado', '')
        estados_validos = ["Consulta Inicial", "En Análisis", "Convertido", "Desestimado"]
        if estado and estado not in estados_validos:
            return False, f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
        
        return True, ""
    
    # ========================================
    # OPERACIONES CRUD DE PROSPECTOS
    # ========================================
    
    def crear_prospecto(self, datos: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Crea un nuevo prospecto después de validar los datos.
        
        Args:
            datos (dict): Datos del prospecto a crear
            
        Returns:
            tuple[bool, str, Optional[int]]: (exito, mensaje, id_prospecto)
        """
        # Validar datos
        es_valido, mensaje_error = self.validar_datos_prospecto(datos)
        if not es_valido:
            return False, mensaje_error, None
        
        try:
            # Crear prospecto en la base de datos
            prospecto_id = self.db.add_prospecto(
                nombre=datos.get('nombre', '').strip(),
                contacto=datos.get('contacto', '').strip(),
                notas_generales=datos.get('notas_generales', '').strip()
            )
            
            if prospecto_id:
                return True, "Prospecto creado exitosamente.", prospecto_id
            else:
                return False, "Error al crear el prospecto en la base de datos.", None
                
        except Exception as e:
            return False, f"Error inesperado al crear prospecto: {str(e)}", None
    
    def editar_prospecto(self, id_prospecto: int, datos: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Edita un prospecto existente después de validar los datos.
        
        Args:
            id_prospecto (int): ID del prospecto a editar
            datos (dict): Nuevos datos del prospecto
            
        Returns:
            tuple[bool, str]: (exito, mensaje)
        """
        # Validar datos
        es_valido, mensaje_error = self.validar_datos_prospecto(datos)
        if not es_valido:
            return False, mensaje_error
        
        try:
            # Verificar que el prospecto existe
            prospecto_existente = self.db.get_prospecto_by_id(id_prospecto)
            if not prospecto_existente:
                return False, "El prospecto no existe."
            
            # Actualizar prospecto en la base de datos
            success = self.db.update_prospecto(
                id_prospecto,
                nombre=datos.get('nombre', '').strip(),
                contacto=datos.get('contacto', '').strip(),
                notas_generales=datos.get('notas_generales', '').strip()
            )
            
            if success:
                return True, "Prospecto actualizado exitosamente."
            else:
                return False, "Error al actualizar el prospecto en la base de datos."
                
        except Exception as e:
            return False, f"Error inesperado al editar prospecto: {str(e)}"
    
    def eliminar_prospecto(self, id_prospecto: int) -> Tuple[bool, str]:
        """
        Elimina un prospecto y todas sus consultas asociadas.
        
        Args:
            id_prospecto (int): ID del prospecto a eliminar
            
        Returns:
            tuple[bool, str]: (exito, mensaje)
        """
        try:
            # Verificar que el prospecto existe
            prospecto_existente = self.db.get_prospecto_by_id(id_prospecto)
            if not prospecto_existente:
                return False, "El prospecto no existe."
            
            # Eliminar prospecto (esto debería eliminar también las consultas por CASCADE)
            success = self.db.delete_prospecto(id_prospecto)
            
            if success:
                return True, f"Prospecto '{prospecto_existente['nombre']}' eliminado exitosamente."
            else:
                return False, "Error al eliminar el prospecto de la base de datos."
                
        except Exception as e:
            return False, f"Error inesperado al eliminar prospecto: {str(e)}"
    
    def obtener_prospecto(self, id_prospecto: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un prospecto por su ID.
        
        Args:
            id_prospecto (int): ID del prospecto
            
        Returns:
            Optional[Dict[str, Any]]: Datos del prospecto o None si no existe
        """
        try:
            return self.db.get_prospecto_by_id(id_prospecto)
        except Exception as e:
            print(f"Error al obtener prospecto {id_prospecto}: {e}")
            return None
    
    def obtener_todos_los_prospectos(self) -> List[Dict[str, Any]]:
        """
        Obtiene todos los prospectos.
        
        Returns:
            List[Dict[str, Any]]: Lista de prospectos
        """
        try:
            return self.db.get_todos_los_prospectos()
        except Exception as e:
            print(f"Error al obtener prospectos: {e}")
            return []
    
    # ========================================
    # OPERACIONES DE BÚSQUEDA Y FILTRADO
    # ========================================
    
    def buscar_prospectos(self, filtros: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Busca prospectos según filtros especificados.
        
        Args:
            filtros (dict): Filtros de búsqueda
                - estados: List[str] - Estados a incluir
                - nombre: str - Búsqueda por nombre (parcial)
                - fecha_desde: datetime.date - Fecha desde
                - fecha_hasta: datetime.date - Fecha hasta
                
        Returns:
            List[Dict[str, Any]]: Lista de prospectos que cumplen los filtros
        """
        try:
            # Obtener todos los prospectos
            prospectos = self.db.get_todos_los_prospectos()
            
            # Aplicar filtros
            if filtros.get('estados'):
                prospectos = [p for p in prospectos if p.get('estado') in filtros['estados']]
            
            if filtros.get('nombre'):
                nombre_filtro = filtros['nombre'].lower()
                prospectos = [p for p in prospectos if nombre_filtro in p.get('nombre', '').lower()]
            
            if filtros.get('fecha_desde') or filtros.get('fecha_hasta'):
                prospectos_filtrados = []
                for p in prospectos:
                    fecha_consulta = p.get('fecha_primera_consulta')
                    if fecha_consulta:
                        # Convertir fecha a objeto date si es string
                        if isinstance(fecha_consulta, str):
                            fecha_consulta = date_utils.DateFormatter.parse_date_input(fecha_consulta)
                        
                        if fecha_consulta:
                            # Aplicar filtro de fecha desde
                            if filtros.get('fecha_desde') and fecha_consulta < filtros['fecha_desde']:
                                continue
                            
                            # Aplicar filtro de fecha hasta
                            if filtros.get('fecha_hasta') and fecha_consulta > filtros['fecha_hasta']:
                                continue
                            
                            prospectos_filtrados.append(p)
                    else:
                        # Si no tiene fecha, incluir solo si no hay filtros de fecha
                        if not filtros.get('fecha_desde') and not filtros.get('fecha_hasta'):
                            prospectos_filtrados.append(p)
                
                prospectos = prospectos_filtrados
            
            return prospectos
            
        except Exception as e:
            print(f"Error al buscar prospectos: {e}")
            return []
    
    def obtener_prospectos_por_estado(self, estado: str) -> List[Dict[str, Any]]:
        """
        Obtiene prospectos filtrados por estado.
        
        Args:
            estado (str): Estado a filtrar
            
        Returns:
            List[Dict[str, Any]]: Lista de prospectos con el estado especificado
        """
        return self.buscar_prospectos({'estados': [estado]})
    
    # ========================================
    # OPERACIONES DE ESTADO
    # ========================================
    
    def cambiar_estado_prospecto(self, id_prospecto: int, nuevo_estado: str) -> Tuple[bool, str]:
        """
        Cambia el estado de un prospecto.
        
        Args:
            id_prospecto (int): ID del prospecto
            nuevo_estado (str): Nuevo estado
            
        Returns:
            tuple[bool, str]: (exito, mensaje)
        """
        try:
            # Validar estado
            estados_validos = ["Consulta Inicial", "En Análisis", "Convertido", "Desestimado"]
            if nuevo_estado not in estados_validos:
                return False, f"Estado inválido. Debe ser uno de: {', '.join(estados_validos)}"
            
            # Verificar que el prospecto existe
            prospecto = self.db.get_prospecto_by_id(id_prospecto)
            if not prospecto:
                return False, "El prospecto no existe."
            
            # Actualizar estado
            success = self.db.update_prospecto_estado(id_prospecto, nuevo_estado)
            
            if success:
                return True, f"Estado cambiado a '{nuevo_estado}' exitosamente."
            else:
                return False, "Error al cambiar el estado en la base de datos."
                
        except Exception as e:
            return False, f"Error inesperado al cambiar estado: {str(e)}"
    
    # ========================================
    # ESTADÍSTICAS
    # ========================================
    
    def obtener_estadisticas_prospectos(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de prospectos.
        
        Returns:
            Dict[str, Any]: Estadísticas de prospectos
        """
        try:
            return self.db.get_estadisticas_prospectos()
        except Exception as e:
            print(f"Error al obtener estadísticas: {e}")
            return {}
    
    # ========================================
    # OPERACIONES DE CONSULTAS
    # ========================================
    
    def obtener_consultas_prospecto(self, id_prospecto: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las consultas de un prospecto.
        
        Args:
            id_prospecto (int): ID del prospecto
            
        Returns:
            List[Dict[str, Any]]: Lista de consultas del prospecto
        """
        try:
            return self.db.get_consultas_by_prospecto_id(id_prospecto)
        except Exception as e:
            print(f"Error al obtener consultas del prospecto {id_prospecto}: {e}")
            return []
    
    # ========================================
    # EXPORTACIÓN DE DOCUMENTOS
    # ========================================
    
    def exportar_consultas_prospecto(self, prospecto: Dict[str, Any], parent_window=None) -> Tuple[bool, str, Optional[str]]:
        """
        Exporta todas las consultas de un prospecto a Word usando el sistema unificado.
        
        Args:
            prospecto (dict): Datos del prospecto
            parent_window: Ventana padre para diálogos
            
        Returns:
            tuple[bool, str, Optional[str]]: (exito, mensaje, ruta_archivo)
        """
        try:
            # Obtener consultas del prospecto
            consultas = self.obtener_consultas_prospecto(prospecto['id'])
            
            if not consultas:
                return False, "Este prospecto no tiene consultas registradas.", None
            
            # Usar WordExportManager para exportar múltiples consultas
            filepath = self.word_export_manager.export_multiple_consultations(
                prospecto, 
                consultas, 
                parent_window
            )
            
            if filepath:
                return True, f"Consultas exportadas exitosamente a: {filepath}", filepath
            else:
                return False, "Error al exportar las consultas.", None
                
        except Exception as e:
            return False, f"Error inesperado al exportar consultas: {str(e)}", None
    
    def exportar_consulta_individual(self, prospecto: Dict[str, Any], consulta: Dict[str, Any], parent_window=None) -> Tuple[bool, str, Optional[str]]:
        """
        Exporta una consulta individual a Word usando el sistema unificado.
        
        Args:
            prospecto (dict): Datos del prospecto
            consulta (dict): Datos de la consulta
            parent_window: Ventana padre para diálogos
            
        Returns:
            tuple[bool, str, Optional[str]]: (exito, mensaje, ruta_archivo)
        """
        try:
            # Usar WordExportManager para exportar consulta individual
            filepath = self.word_export_manager.export_consultation_to_word(
                prospecto,
                consulta,
                parent_window
            )
            
            if filepath:
                return True, f"Consulta exportada exitosamente a: {filepath}", filepath
            else:
                return False, "Error al exportar la consulta.", None
                
        except Exception as e:
            return False, f"Error inesperado al exportar consulta: {str(e)}", None
    
    # ========================================
    # UTILIDADES DE FORMATEO
    # ========================================
    
    def formatear_fecha_para_mostrar(self, fecha) -> str:
        """
        Formatea una fecha para mostrar en la interfaz (formato argentino).
        
        Args:
            fecha: Fecha en cualquier formato
            
        Returns:
            str: Fecha formateada en DD/MM/YYYY o "N/A"
        """
        fecha_str = date_utils.DateFormatter.to_display_format(fecha)
        return fecha_str if fecha_str else "N/A"
    
    def generar_reporte_texto_consultas(self, prospecto: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """
        Genera un reporte de texto con todas las consultas de un prospecto.
        
        Args:
            prospecto (dict): Datos del prospecto
            
        Returns:
            tuple[bool, str, Optional[str]]: (exito, mensaje, contenido_reporte)
        """
        try:
            # Obtener consultas
            consultas = self.obtener_consultas_prospecto(prospecto['id'])
            
            if not consultas:
                return False, "Este prospecto no tiene consultas registradas.", None
            
            # Formatear fecha de primera consulta
            primera_consulta_str = self.formatear_fecha_para_mostrar(prospecto.get('fecha_primera_consulta'))
            
            # Crear contenido del reporte
            report_content = f"""REPORTE DE CONSULTAS - PROSPECTO
{'=' * 60}

DATOS DEL PROSPECTO:
Nombre: {prospecto.get('nombre', 'N/A')}
Contacto: {prospecto.get('contacto', 'N/A')}
Estado: {prospecto.get('estado', 'N/A')}
Primera Consulta: {primera_consulta_str}
Fecha de Reporte: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}

{'=' * 60}

CONSULTAS REGISTRADAS ({len(consultas)}):

"""
            
            for i, consulta in enumerate(consultas, 1):
                # Format consultation date in Argentine format
                fecha_str = self.formatear_fecha_para_mostrar(consulta.get('fecha_consulta'))
                
                report_content += f"""
CONSULTA #{i}
{'-' * 40}
Fecha: {fecha_str}

RELATO ORIGINAL DEL CLIENTE:
{consulta.get('relato_original_cliente', 'No registrado')}

HECHOS REFORMULADOS POR IA:
{consulta.get('hechos_reformulados_ia', 'No procesado')}

ENCUADRE LEGAL PRELIMINAR:
{consulta.get('encuadre_legal_preliminar', 'No completado')}

{'=' * 60}
"""
            
            return True, "Reporte generado exitosamente.", report_content
            
        except Exception as e:
            return False, f"Error al generar reporte: {str(e)}", None
    
    # ========================================
    # OPERACIONES DE CONVERSIÓN
    # ========================================
    
    def convertir_prospecto_a_cliente(self, id_prospecto: int) -> Tuple[bool, str, Optional[int]]:
        """
        Convierte un prospecto a cliente usando el servicio de conversión.
        
        Args:
            id_prospecto (int): ID del prospecto a convertir
            
        Returns:
            tuple[bool, str, Optional[int]]: (exito, mensaje, id_cliente_creado)
        """
        return self.conversion_service.convertir_prospecto_a_cliente(id_prospecto)
    
    def verificar_conversion_reversible(self, id_prospecto: int) -> Tuple[bool, str]:
        """
        Verifica si la conversión de un prospecto puede ser revertida.
        
        Args:
            id_prospecto (int): ID del prospecto
            
        Returns:
            tuple[bool, str]: (es_reversible, razon)
        """
        return self.conversion_service.verificar_conversion_reversible(id_prospecto)
    
    def revertir_conversion(self, id_prospecto: int) -> Tuple[bool, str]:
        """
        Revierte la conversión de un prospecto a cliente si es posible.
        
        Args:
            id_prospecto (int): ID del prospecto
            
        Returns:
            tuple[bool, str]: (exito, mensaje)
        """
        return self.conversion_service.revertir_conversion(id_prospecto)
    
    def obtener_estadisticas_conversion(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre las conversiones de prospectos a clientes.
        
        Returns:
            dict: Estadísticas de conversión
        """
        return self.conversion_service.obtener_estadisticas_conversion()
    
    def buscar_conversiones_recientes(self, dias: int = 30) -> List[Dict[str, Any]]:
        """
        Busca conversiones realizadas en los últimos N días.
        
        Args:
            dias (int): Número de días hacia atrás para buscar
            
        Returns:
            list: Lista de conversiones recientes
        """
        return self.conversion_service.buscar_conversiones_recientes(dias)
    
    # ========================================
    # OPERACIONES CON ENTIDAD BASE
    # ========================================
    
    def crear_entidad_desde_prospecto(self, id_prospecto: int) -> Optional[EntidadBase]:
        """
        Crea una EntidadBase desde un prospecto existente.
        
        Args:
            id_prospecto (int): ID del prospecto
            
        Returns:
            Optional[EntidadBase]: Entidad creada o None si falla
        """
        try:
            prospecto_data = self.obtener_prospecto(id_prospecto)
            if prospecto_data:
                return EntidadFactory.crear_desde_prospecto(prospecto_data)
            return None
        except Exception as e:
            print(f"Error creando entidad desde prospecto {id_prospecto}: {e}")
            return None
    
    def validar_prospecto_para_conversion(self, id_prospecto: int) -> Tuple[bool, str]:
        """
        Valida si un prospecto puede ser convertido a cliente.
        
        Args:
            id_prospecto (int): ID del prospecto
            
        Returns:
            tuple[bool, str]: (puede_convertir, mensaje)
        """
        try:
            entidad = self.crear_entidad_desde_prospecto(id_prospecto)
            if not entidad:
                return False, "No se pudo obtener los datos del prospecto."
            
            # Verificar si ya está convertido
            if entidad.es_convertido():
                return False, f"El prospecto ya fue convertido al cliente ID {entidad.convertido_a_cliente_id}."
            
            # Validar datos para cliente
            return entidad.validar_para_cliente()
            
        except Exception as e:
            return False, f"Error validando prospecto para conversión: {str(e)}"