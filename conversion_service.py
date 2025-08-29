#!/usr/bin/env python3
"""
Conversion Service - Maneja la conversión de prospectos a clientes
Servicio que centraliza toda la lógica de conversión entre prospectos y clientes
"""

import datetime
from typing import Dict, List, Optional, Tuple, Any
import crm_database as db


class ConversionService:
    """Servicio que maneja la conversión de prospectos a clientes"""

    def __init__(self):
        self.db = db

    def convertir_prospecto_a_cliente(self, id_prospecto: int) -> Tuple[bool, str, Optional[int]]:
        """
        Convierte un prospecto a cliente.

        Args:
            id_prospecto (int): ID del prospecto a convertir

        Returns:
            tuple[bool, str, Optional[int]]: (exito, mensaje, id_cliente_creado)
        """
        try:
            # Verificar que el prospecto existe
            prospecto = self.db.get_prospecto_by_id(id_prospecto)
            if not prospecto:
                return False, "El prospecto no existe.", None

            # Verificar que no esté ya convertido
            if prospecto.get("estado") == "Convertido":
                cliente_id = prospecto.get("convertido_a_cliente_id")
                return False, f"El prospecto ya fue convertido al cliente ID {cliente_id}.", None

            # Crear cliente con los datos del prospecto
            cliente_data = {
                'nombre': prospecto.get('nombre', ''),
                'contacto': prospecto.get('contacto', ''),
                'direccion': '',  # Prospectos no tienen dirección
                'email': '',
                'whatsapp': '',
                'etiquetas': 'Convertido desde prospecto',
                'notas': f"Convertido desde prospecto ID {id_prospecto}. Primera consulta: {prospecto.get('fecha_primera_consulta', 'N/A')}"
            }

            # Crear el cliente
            cliente_id = self.db.add_cliente(**cliente_data)

            if cliente_id:
                # Actualizar el prospecto como convertido
                fecha_conversion = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.db.update_prospecto_estado(id_prospecto, "Convertido")
                self.db.update_prospecto_conversion(id_prospecto, cliente_id, fecha_conversion)

                # Actualizar timestamp de actividad
                self.db.update_last_activity_for_prospecto(id_prospecto)

                return True, f"Prospecto convertido exitosamente al cliente ID {cliente_id}.", cliente_id
            else:
                return False, "Error al crear el cliente en la base de datos.", None

        except Exception as e:
            return False, f"Error inesperado al convertir prospecto: {str(e)}", None

    def verificar_conversion_reversible(self, id_prospecto: int) -> Tuple[bool, str]:
        """
        Verifica si la conversión de un prospecto puede ser revertida.

        Args:
            id_prospecto (int): ID del prospecto

        Returns:
            tuple[bool, str]: (es_reversible, razon)
        """
        try:
            # Verificar que el prospecto existe
            prospecto = self.db.get_prospecto_by_id(id_prospecto)
            if not prospecto:
                return False, "El prospecto no existe."

            # Verificar que esté convertido
            if prospecto.get("estado") != "Convertido":
                return False, "El prospecto no ha sido convertido."

            cliente_id = prospecto.get("convertido_a_cliente_id")
            if not cliente_id:
                return False, "No se encontró el ID del cliente convertido."

            # Verificar que el cliente existe
            cliente = self.db.get_cliente_by_id(cliente_id)
            if not cliente:
                return True, "El cliente convertido ya no existe (puede ser revertido)."

            # Verificar si el cliente tiene casos asociados
            casos_cliente = self.db.get_casos_by_cliente_id(cliente_id)
            if casos_cliente:
                return False, f"El cliente tiene {len(casos_cliente)} caso(s) asociado(s). No se puede revertir."

            return True, "La conversión puede ser revertida."

        except Exception as e:
            return False, f"Error al verificar reversibilidad: {str(e)}"

    def revertir_conversion(self, id_prospecto: int) -> Tuple[bool, str]:
        """
        Revierte la conversión de un prospecto a cliente si es posible.

        Args:
            id_prospecto (int): ID del prospecto

        Returns:
            tuple[bool, str]: (exito, mensaje)
        """
        try:
            # Verificar que puede ser revertida
            es_reversible, razon = self.verificar_conversion_reversible(id_prospecto)
            if not es_reversible:
                return False, f"No se puede revertir la conversión: {razon}"

            prospecto = self.db.get_prospecto_by_id(id_prospecto)
            cliente_id = prospecto.get("convertido_a_cliente_id")

            # Eliminar el cliente
            if cliente_id:
                cliente_eliminado = self.db.delete_cliente(cliente_id)
                if not cliente_eliminado:
                    return False, "Error al eliminar el cliente convertido."

            # Restaurar el prospecto al estado anterior
            self.db.update_prospecto_estado(id_prospecto, "En Análisis")
            self.db.clear_prospecto_conversion(id_prospecto)

            # Actualizar timestamp de actividad
            self.db.update_last_activity_for_prospecto(id_prospecto)

            return True, f"Conversión revertida exitosamente. Prospecto restaurado al estado 'En Análisis'."

        except Exception as e:
            return False, f"Error inesperado al revertir conversión: {str(e)}"

    def obtener_estadisticas_conversion(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre las conversiones de prospectos a clientes.

        Returns:
            dict: Estadísticas de conversión
        """
        try:
            # Obtener todos los prospectos
            prospectos = self.db.get_todos_los_prospectos()

            total_prospectos = len(prospectos)
            convertidos = len([p for p in prospectos if p.get("estado") == "Convertido"])
            tasa_conversion = (convertidos / total_prospectos * 100) if total_prospectos > 0 else 0

            # Conversiones por mes (últimos 12 meses)
            conversiones_por_mes = {}
            ahora = datetime.datetime.now()

            for i in range(12):
                mes = ahora - datetime.timedelta(days=i*30)
                mes_str = mes.strftime("%Y-%m")
                conversiones_por_mes[mes_str] = 0

            for prospecto in prospectos:
                if prospecto.get("estado") == "Convertido" and prospecto.get("fecha_conversion"):
                    try:
                        fecha_conv = datetime.datetime.strptime(prospecto["fecha_conversion"], "%Y-%m-%d %H:%M:%S")
                        mes_str = fecha_conv.strftime("%Y-%m")
                        if mes_str in conversiones_por_mes:
                            conversiones_por_mes[mes_str] += 1
                    except (ValueError, TypeError):
                        continue

            return {
                "total_prospectos": total_prospectos,
                "convertidos": convertidos,
                "tasa_conversion": round(tasa_conversion, 2),
                "conversiones_por_mes": conversiones_por_mes
            }

        except Exception as e:
            print(f"Error obteniendo estadísticas de conversión: {e}")
            return {}

    def buscar_conversiones_recientes(self, dias: int = 30) -> List[Dict[str, Any]]:
        """
        Busca conversiones realizadas en los últimos N días.

        Args:
            dias (int): Número de días hacia atrás para buscar

        Returns:
            list: Lista de conversiones recientes
        """
        try:
            # Calcular fecha límite
            fecha_limite = datetime.datetime.now() - datetime.timedelta(days=dias)
            fecha_limite_str = fecha_limite.strftime("%Y-%m-%d %H:%M:%S")

            # Obtener prospectos convertidos recientemente
            prospectos = self.db.get_todos_los_prospectos()
            conversiones_recientes = []

            for prospecto in prospectos:
                if (prospecto.get("estado") == "Convertido" and
                    prospecto.get("fecha_conversion") and
                    prospecto["fecha_conversion"] >= fecha_limite_str):

                    conversiones_recientes.append({
                        "prospecto_id": prospecto["id"],
                        "prospecto_nombre": prospecto.get("nombre", "N/A"),
                        "cliente_id": prospecto.get("convertido_a_cliente_id"),
                        "fecha_conversion": prospecto.get("fecha_conversion"),
                        "contacto": prospecto.get("contacto", "N/A")
                    })

            # Ordenar por fecha de conversión (más reciente primero)
            conversiones_recientes.sort(key=lambda x: x["fecha_conversion"], reverse=True)

            return conversiones_recientes

        except Exception as e:
            print(f"Error buscando conversiones recientes: {e}")
            return []