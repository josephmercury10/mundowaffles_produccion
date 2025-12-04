"""
Cliente HTTP para comunicarse con PrintHost (Servidor de impresión local en Windows)
Utilizado cuando la app está en PythonAnywhere o Linux

PrintHost debe estar corriendo en el cliente con: python app/printer_host.py
"""

import requests
import logging
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PrintHostClient:
    def __init__(self, 
                 printhost_url: str = "http://localhost:8765",
                 timeout: int = 10):
        """
        Inicializa cliente PrintHost
        
        Args:
            printhost_url: URL del servidor PrintHost (ej: http://192.168.1.100:8765)
            timeout: Timeout para requests (segundos)
        """
        self.printhost_url = printhost_url.rstrip('/')
        self.timeout = timeout
    
    def health_check(self) -> bool:
        """Verifica que PrintHost esté disponible"""
        try:
            resp = requests.get(
                f"{self.printhost_url}/health",
                timeout=self.timeout
            )
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"PrintHost no disponible: {e}")
            return False
    
    def list_printers(self) -> list:
        """Obtiene lista de impresoras disponibles en el cliente"""
        try:
            resp = requests.get(
                f"{self.printhost_url}/printers",
                timeout=self.timeout
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get('printers', [])
            return []
        except Exception as e:
            logger.error(f"Error obteniendo impresoras: {e}")
            return []
    
    def print_raw(self, 
                  driver: str,
                  content: str,
                  feed: int = 3,
                  cut: bool = True) -> Dict[str, Any]:
        """
        Imprime contenido RAW
        
        Args:
            driver: Nombre de impresora (ej: "EPSON TM-T88V Receipt5")
            content: Contenido a imprimir (texto)
            feed: Líneas de avance de papel
            cut: ¿Cortar papel?
        
        Returns:
            {'ok': bool, 'error': str (si falla)}
        """
        try:
            payload = {
                'driver': driver,
                'content': content,
                'feed': feed,
                'cut': cut
            }
            
            resp = requests.post(
                f"{self.printhost_url}/print/raw",
                json=payload,
                timeout=self.timeout
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {'ok': False, 'error': f"Status {resp.status_code}"}
        
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ No se puede conectar a PrintHost: {self.printhost_url}")
            return {'ok': False, 'error': f'No se puede conectar a PrintHost en {self.printhost_url}'}
        
        except Exception as e:
            logger.error(f"Error imprimiendo: {e}")
            return {'ok': False, 'error': str(e)}
    
    def print_pedido(self,
                     driver: str,
                     pedido_id: int,
                     contenido: str) -> Dict[str, Any]:
        """
        Imprime un pedido
        
        Args:
            driver: Nombre de impresora
            pedido_id: ID del pedido
            contenido: Contenido a imprimir
        
        Returns:
            {'ok': bool, 'error': str (si falla)}
        """
        try:
            payload = {
                'driver': driver,
                'pedido_id': pedido_id,
                'contenido': contenido
            }
            
            resp = requests.post(
                f"{self.printhost_url}/print/pedido",
                json=payload,
                timeout=self.timeout
            )
            
            if resp.status_code == 200:
                return resp.json()
            else:
                return {'ok': False, 'error': f"Status {resp.status_code}"}
        
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ No se puede conectar a PrintHost para pedido #{pedido_id}")
            return {'ok': False, 'error': f'PrintHost no disponible'}
        
        except Exception as e:
            logger.error(f"Error imprimiendo pedido #{pedido_id}: {e}")
            return {'ok': False, 'error': str(e)}


def get_printhost_client(app=None) -> PrintHostClient:
    """
    Obtiene cliente PrintHost
    
    Configurar en config.py:
    - DevelopmentConfig: PRINTHOST_URL = None (no usar)
    - ProductionConfig: PRINTHOST_URL = os.environ.get('PRINTHOST_URL', ...)
    """
    if app is None:
        from flask import current_app
        app = current_app
    
    printhost_url = app.config.get('PRINTHOST_URL', 'http://localhost:8765')
    return PrintHostClient(printhost_url)
