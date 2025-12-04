"""
Cliente HTTP liviano para PrintHost.
Objetivo: el servidor Flask solo envía instrucciones; todo el formateo y
detalle de impresora sucede en el cliente (PrintHost en Windows).
"""

import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class PrintHostClient:
    def __init__(self,
                 printhost_url: str = "http://localhost:8765",
                 timeout: int = 10):
        self.printhost_url = printhost_url.rstrip('/')
        self.timeout = timeout

    # ===== Utils =====
    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.printhost_url}{path}"
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
            return {'ok': False, 'error': f"Status {resp.status_code}"}
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ No se puede conectar a PrintHost: {self.printhost_url}")
            return {'ok': False, 'error': f'PrintHost no disponible en {self.printhost_url}'}
        except Exception as e:
            logger.error(f"Error en POST {path}: {e}")
            return {'ok': False, 'error': str(e)}

    # ===== Health & discovery =====
    def health_check(self) -> bool:
        try:
            resp = requests.get(f"{self.printhost_url}/health", timeout=self.timeout)
            return resp.status_code == 200
        except Exception as e:
            logger.warning(f"PrintHost no disponible: {e}")
            return False

    def list_printers(self) -> list:
        try:
            resp = requests.get(f"{self.printhost_url}/printers", timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json().get('printers', [])
            return []
        except Exception as e:
            logger.error(f"Error obteniendo impresoras: {e}")
            return []

    # ===== Generic job =====
    def print_job(self,
                  job_type: str,
                  payload: Dict[str, Any],
                  driver: Optional[str] = None,
                  feed: Optional[int] = None,
                  cut: Optional[bool] = None) -> Dict[str, Any]:
        """Envía un trabajo de impresión genérico al PrintHost."""
        body = {
            'type': job_type,
            'payload': payload,
        }
        if driver:
            body['driver'] = driver
        if feed is not None:
            body['feed'] = feed
        if cut is not None:
            body['cut'] = cut

        return self._post('/print/job', body)

    # ===== Backwards-compatible helpers =====
    def print_raw(self, driver: str, content: str, feed: int = 3, cut: bool = True) -> Dict[str, Any]:
        return self.print_job(
            job_type='raw',
            payload={'content': content},
            driver=driver,
            feed=feed,
            cut=cut,
        )

    def print_pedido(self, driver: str, pedido_id: int, contenido: str) -> Dict[str, Any]:
        return self.print_job(
            job_type='pedido',
            payload={'pedido_id': pedido_id, 'contenido': contenido},
            driver=driver,
        )


def get_printhost_client(app=None) -> PrintHostClient:
    """Obtiene cliente PrintHost con la URL definida en config."""
    if app is None:
        from flask import current_app
        app = current_app

    printhost_url = app.config.get('PRINTHOST_URL', 'http://localhost:8765')
    return PrintHostClient(printhost_url)
