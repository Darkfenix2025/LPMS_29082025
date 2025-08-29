#!/usr/bin/env python3
"""
Entidad Base - Modelo de datos común para Clientes y Prospectos
Unifica los campos comunes entre ambas entidades para facilitar conversiones y mantenimiento
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
import date_utils


@dataclass
class EntidadBase:
    """
    Clase base que define los campos comunes entre Clientes y Prospectos.
    Facilita la conversión entre ambas entidades y mantiene consistencia de datos.
    """
    
    # Campos obligatorios comunes
    id: Optional[int] = None
    nombre: str = ""
    
    # Campos de contacto (unificados)
    email: str = ""
    telefono: str = ""
    whatsapp: str = ""
    direccion: str = ""
    
    # Campos adicionales para prospectos que pueden ser útiles en clientes
    contacto: str = ""  # Campo genérico de contacto (usado en prospectos)
    
    # Campos de auditoría
    created_at: Optional[int] = None
    
    # Campos específicos de prospectos (opcionales para clientes)
    fecha_primera_consulta: Optional[date] = None
    estado: str = ""
    notas_generales: str = ""
    
    # Campos de conversión (para trazabilidad)
    convertido_a_cliente_id: Optional[int] = None
    convertido_de_prospecto_id: Optional[int] = None
    fecha_conversion: Optional[date] = None
    
    def __post_init__(self):
        """Inicialización posterior para validar y normalizar datos"""
        # Normalizar campos de texto
        self.nombre = self.nombre.strip() if self.nombre else ""
        self.email = self.email.strip() if self.email else ""
        self.telefono = self.telefono.strip() if self.telefono else ""
        self.whatsapp = self.whatsapp.strip() if self.whatsapp else ""
        self.direccion = self.direccion.strip() if self.direccion else ""
        self.contacto = self.contacto.strip() if self.contacto else ""
        self.notas_generales = self.notas_generales.strip() if self.notas_generales else ""
        
        # Si no hay created_at, usar timestamp actual
        if self.created_at is None:
            self.created_at = int(datetime.now().timestamp())
    
    @classmethod
    def from_cliente_dict(cls, cliente_data: Dict[str, Any]) -> 'EntidadBase':
        """
        Crea una EntidadBase desde un diccionario de datos de cliente.
        
        Args:
            cliente_data (dict): Datos del cliente desde la base de datos
            
        Returns:
            EntidadBase: Instancia con los datos del cliente
        """
        return cls(
            id=cliente_data.get('id'),
            nombre=cliente_data.get('nombre', ''),
            email=cliente_data.get('email', ''),
            telefono=cliente_data.get('telefono', ''),  # Mapear si existe
            whatsapp=cliente_data.get('whatsapp', ''),
            direccion=cliente_data.get('direccion', ''),
            created_at=cliente_data.get('created_at'),
            # Campos específicos de cliente
            contacto=cliente_data.get('email', ''),  # Usar email como contacto genérico
            estado="Cliente Activo",  # Estado por defecto para clientes
            convertido_de_prospecto_id=cliente_data.get('convertido_de_prospecto_id'),
            fecha_conversion=cliente_data.get('fecha_conversion')
        )
    
    @classmethod
    def from_prospecto_dict(cls, prospecto_data: Dict[str, Any]) -> 'EntidadBase':
        """
        Crea una EntidadBase desde un diccionario de datos de prospecto.
        
        Args:
            prospecto_data (dict): Datos del prospecto desde la base de datos
            
        Returns:
            EntidadBase: Instancia con los datos del prospecto
        """
        return cls(
            id=prospecto_data.get('id'),
            nombre=prospecto_data.get('nombre', ''),
            contacto=prospecto_data.get('contacto', ''),
            fecha_primera_consulta=prospecto_data.get('fecha_primera_consulta'),
            estado=prospecto_data.get('estado', 'Consulta Inicial'),
            notas_generales=prospecto_data.get('notas_generales', ''),
            created_at=prospecto_data.get('created_at'),
            convertido_a_cliente_id=prospecto_data.get('convertido_a_cliente_id'),
            fecha_conversion=prospecto_data.get('fecha_conversion'),
            # Extraer información de contacto si está en formato estructurado
            email=cls._extraer_email_de_contacto(prospecto_data.get('contacto', '')),
            telefono=cls._extraer_telefono_de_contacto(prospecto_data.get('contacto', '')),
        )
    
    @staticmethod
    def _extraer_email_de_contacto(contacto: str) -> str:
        """
        Extrae email del campo contacto genérico.
        
        Args:
            contacto (str): Campo contacto del prospecto
            
        Returns:
            str: Email extraído o cadena vacía
        """
        if not contacto:
            return ""
        
        # Buscar patrones de email
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, contacto)
        return matches[0] if matches else ""
    
    @staticmethod
    def _extraer_telefono_de_contacto(contacto: str) -> str:
        """
        Extrae teléfono del campo contacto genérico.
        
        Args:
            contacto (str): Campo contacto del prospecto
            
        Returns:
            str: Teléfono extraído o cadena vacía
        """
        if not contacto:
            return ""
        
        # Buscar patrones de teléfono (números con posibles separadores)
        import re
        # Patrones comunes: +54 11 1234-5678, 011-1234-5678, 1123456789, etc.
        phone_patterns = [
            r'\+?\d{1,3}[\s-]?\d{2,4}[\s-]?\d{4}[\s-]?\d{4}',  # Internacional
            r'\d{3,4}[\s-]?\d{4}[\s-]?\d{4}',  # Nacional
            r'\d{10,11}',  # Solo números
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, contacto)
            if matches:
                # Limpiar el teléfono (quitar espacios y guiones)
                phone = re.sub(r'[\s-]', '', matches[0])
                return phone
        
        return ""
    
    def to_cliente_dict(self) -> Dict[str, Any]:
        """
        Convierte la entidad a un diccionario compatible con la tabla clientes.
        
        Returns:
            dict: Datos formateados para insertar/actualizar en tabla clientes
        """
        # Consolidar información de contacto
        email_final = self.email or self._extraer_email_de_contacto(self.contacto)
        whatsapp_final = self.whatsapp or self._extraer_telefono_de_contacto(self.contacto)
        
        return {
            'nombre': self.nombre,
            'direccion': self.direccion,
            'email': email_final,
            'whatsapp': whatsapp_final,
            'created_at': self.created_at,
            # Campos adicionales para trazabilidad (si la tabla los soporta)
            'convertido_de_prospecto_id': self.convertido_de_prospecto_id,
            'fecha_conversion': self.fecha_conversion
        }
    
    def to_prospecto_dict(self) -> Dict[str, Any]:
        """
        Convierte la entidad a un diccionario compatible con la tabla prospectos.
        
        Returns:
            dict: Datos formateados para insertar/actualizar en tabla prospectos
        """
        # Consolidar información de contacto en el campo genérico
        contacto_consolidado = self.contacto
        if not contacto_consolidado:
            partes_contacto = []
            if self.email:
                partes_contacto.append(f"Email: {self.email}")
            if self.telefono:
                partes_contacto.append(f"Tel: {self.telefono}")
            if self.whatsapp:
                partes_contacto.append(f"WhatsApp: {self.whatsapp}")
            contacto_consolidado = " | ".join(partes_contacto)
        
        return {
            'nombre': self.nombre,
            'contacto': contacto_consolidado,
            'fecha_primera_consulta': self.fecha_primera_consulta or date.today(),
            'estado': self.estado or 'Consulta Inicial',
            'notas_generales': self.notas_generales,
            'created_at': self.created_at,
            'convertido_a_cliente_id': self.convertido_a_cliente_id,
            'fecha_conversion': self.fecha_conversion
        }
    
    def validar_para_cliente(self) -> tuple[bool, str]:
        """
        Valida que los datos sean suficientes para crear un cliente.
        
        Returns:
            tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not self.nombre:
            return False, "El nombre es obligatorio para crear un cliente."
        
        if len(self.nombre) > 255:
            return False, "El nombre es demasiado largo (máximo 255 caracteres)."
        
        # Validar que tenga al menos un método de contacto
        tiene_contacto = any([
            self.email,
            self.telefono,
            self.whatsapp,
            self.contacto,
            self.direccion
        ])
        
        if not tiene_contacto:
            return False, "Debe proporcionar al menos un método de contacto (email, teléfono, WhatsApp o dirección)."
        
        return True, ""
    
    def validar_para_prospecto(self) -> tuple[bool, str]:
        """
        Valida que los datos sean suficientes para crear un prospecto.
        
        Returns:
            tuple[bool, str]: (es_valido, mensaje_error)
        """
        if not self.nombre:
            return False, "El nombre es obligatorio para crear un prospecto."
        
        if len(self.nombre) > 255:
            return False, "El nombre es demasiado largo (máximo 255 caracteres)."
        
        return True, ""
    
    def formatear_fecha_primera_consulta(self) -> str:
        """
        Formatea la fecha de primera consulta para mostrar en la interfaz.
        
        Returns:
            str: Fecha formateada en formato argentino o "N/A"
        """
        if self.fecha_primera_consulta:
            return date_utils.DateFormatter.to_display_format(self.fecha_primera_consulta)
        return "N/A"
    
    def formatear_fecha_conversion(self) -> str:
        """
        Formatea la fecha de conversión para mostrar en la interfaz.
        
        Returns:
            str: Fecha formateada en formato argentino o "N/A"
        """
        if self.fecha_conversion:
            return date_utils.DateFormatter.to_display_format(self.fecha_conversion)
        return "N/A"
    
    def es_convertido(self) -> bool:
        """
        Verifica si el prospecto ha sido convertido a cliente.
        
        Returns:
            bool: True si ha sido convertido, False en caso contrario
        """
        return self.convertido_a_cliente_id is not None
    
    def es_cliente_convertido(self) -> bool:
        """
        Verifica si el cliente fue convertido desde un prospecto.
        
        Returns:
            bool: True si fue convertido desde prospecto, False en caso contrario
        """
        return self.convertido_de_prospecto_id is not None
    
    def obtener_info_conversion(self) -> str:
        """
        Obtiene información legible sobre el estado de conversión.
        
        Returns:
            str: Información sobre la conversión
        """
        if self.es_convertido():
            fecha_str = self.formatear_fecha_conversion()
            return f"Convertido a cliente (ID: {self.convertido_a_cliente_id}) el {fecha_str}"
        elif self.es_cliente_convertido():
            fecha_str = self.formatear_fecha_conversion()
            return f"Convertido desde prospecto (ID: {self.convertido_de_prospecto_id}) el {fecha_str}"
        else:
            return "Sin conversión"
    
    def __str__(self) -> str:
        """Representación en cadena de la entidad"""
        tipo = "Cliente" if self.es_cliente_convertido() or self.estado == "Cliente Activo" else "Prospecto"
        return f"{tipo}: {self.nombre} (ID: {self.id})"
    
    def __repr__(self) -> str:
        """Representación técnica de la entidad"""
        return f"EntidadBase(id={self.id}, nombre='{self.nombre}', estado='{self.estado}')"


class EntidadFactory:
    """Factory para crear instancias de EntidadBase desde diferentes fuentes"""
    
    @staticmethod
    def crear_desde_cliente(cliente_data: Dict[str, Any]) -> EntidadBase:
        """Crea EntidadBase desde datos de cliente"""
        return EntidadBase.from_cliente_dict(cliente_data)
    
    @staticmethod
    def crear_desde_prospecto(prospecto_data: Dict[str, Any]) -> EntidadBase:
        """Crea EntidadBase desde datos de prospecto"""
        return EntidadBase.from_prospecto_dict(prospecto_data)
    
    @staticmethod
    def crear_nuevo_prospecto(nombre: str, contacto: str = "", notas: str = "") -> EntidadBase:
        """Crea una nueva EntidadBase configurada como prospecto"""
        return EntidadBase(
            nombre=nombre,
            contacto=contacto,
            notas_generales=notas,
            fecha_primera_consulta=date.today(),
            estado="Consulta Inicial"
        )
    
    @staticmethod
    def crear_nuevo_cliente(nombre: str, email: str = "", telefono: str = "", direccion: str = "") -> EntidadBase:
        """Crea una nueva EntidadBase configurada como cliente"""
        return EntidadBase(
            nombre=nombre,
            email=email,
            telefono=telefono,
            direccion=direccion,
            estado="Cliente Activo"
        )