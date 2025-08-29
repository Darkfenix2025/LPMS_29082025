#!/usr/bin/env python3
"""
Lazy Loader Module - Sistema de carga diferida para optimizar el arranque del CRM
"""

import importlib
import time
import threading
from typing import Dict, Any, Optional, Callable


class LazyLoader:
    """
    Sistema de carga diferida para módulos pesados del CRM
    """
    
    def __init__(self):
        self._loaded_modules: Dict[str, Any] = {}
        self._loading_locks: Dict[str, threading.Lock] = {}
        self._startup_time = time.time()
        
    def register_module(self, name: str, module_path: str, init_func: Optional[Callable] = None):
        """
        Registra un módulo para carga diferida
        
        Args:
            name: Nombre del módulo para referencia
            module_path: Ruta del módulo para importar
            init_func: Función opcional de inicialización
        """
        if name not in self._loading_locks:
            self._loading_locks[name] = threading.Lock()
            
    def get_module(self, name: str, module_path: str, init_func: Optional[Callable] = None) -> Any:
        """
        Obtiene un módulo, cargándolo si es necesario
        
        Args:
            name: Nombre del módulo
            module_path: Ruta del módulo
            init_func: Función de inicialización opcional
            
        Returns:
            El módulo cargado
        """
        if name in self._loaded_modules:
            return self._loaded_modules[name]
            
        # Usar lock para evitar carga múltiple en threads
        if name not in self._loading_locks:
            self._loading_locks[name] = threading.Lock()
            
        with self._loading_locks[name]:
            # Double-check después del lock
            if name in self._loaded_modules:
                return self._loaded_modules[name]
                
            print(f"[LazyLoader] Cargando módulo: {name}")
            start_time = time.time()
            
            try:
                # Importar el módulo
                module = importlib.import_module(module_path)
                
                # Ejecutar función de inicialización si se proporciona
                if init_func:
                    module = init_func(module)
                    
                self._loaded_modules[name] = module
                
                load_time = time.time() - start_time
                total_time = time.time() - self._startup_time
                print(f"[LazyLoader] ✓ {name} cargado en {load_time:.2f}s (total: {total_time:.2f}s)")
                
                return module
                
            except Exception as e:
                print(f"[LazyLoader] ✗ Error cargando {name}: {e}")
                raise
                
    def is_loaded(self, name: str) -> bool:
        """Verifica si un módulo ya está cargado"""
        return name in self._loaded_modules
        
    def get_loaded_modules(self) -> Dict[str, Any]:
        """Obtiene todos los módulos cargados"""
        return self._loaded_modules.copy()
        
    def clear_module(self, name: str):
        """Limpia un módulo de la caché (para testing)"""
        if name in self._loaded_modules:
            del self._loaded_modules[name]


# Instancia global del lazy loader
lazy_loader = LazyLoader()


class LazyModule:
    """
    Wrapper para módulos que se cargan de forma diferida
    """
    
    def __init__(self, name: str, module_path: str, init_func: Optional[Callable] = None):
        self.name = name
        self.module_path = module_path
        self.init_func = init_func
        self._module = None
        
    def __getattr__(self, attr):
        """Carga el módulo cuando se accede a un atributo"""
        if self._module is None:
            self._module = lazy_loader.get_module(self.name, self.module_path, self.init_func)
        return getattr(self._module, attr)
        
    def __call__(self, *args, **kwargs):
        """Permite que el wrapper sea callable"""
        if self._module is None:
            self._module = lazy_loader.get_module(self.name, self.module_path, self.init_func)
        return self._module(*args, **kwargs)
        
    @property
    def is_loaded(self) -> bool:
        """Verifica si el módulo está cargado"""
        return self._module is not None


def create_lazy_module(name: str, module_path: str, init_func: Optional[Callable] = None) -> LazyModule:
    """
    Crea un módulo lazy
    
    Args:
        name: Nombre del módulo
        module_path: Ruta del módulo
        init_func: Función de inicialización opcional
        
    Returns:
        LazyModule wrapper
    """
    return LazyModule(name, module_path, init_func)


def preload_module(name: str, module_path: str, init_func: Optional[Callable] = None):
    """
    Pre-carga un módulo en background (para módulos que sabemos que se usarán pronto)
    """
    def preload():
        try:
            lazy_loader.get_module(name, module_path, init_func)
        except Exception as e:
            print(f"[LazyLoader] Error en pre-carga de {name}: {e}")
    
    thread = threading.Thread(target=preload, daemon=True)
    thread.start()


def get_startup_stats() -> Dict[str, Any]:
    """
    Obtiene estadísticas de arranque y carga de módulos
    """
    current_time = time.time()
    startup_time = current_time - lazy_loader._startup_time
    
    return {
        'startup_time': startup_time,
        'loaded_modules': list(lazy_loader._loaded_modules.keys()),
        'total_modules_loaded': len(lazy_loader._loaded_modules)
    }