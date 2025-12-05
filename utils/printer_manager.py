import platform
from typing import Optional, List, Dict

from src.models.Printer_model import Printer
from utils.db import db

# Import condicional de win32print (solo Windows)
HAS_WIN32 = platform.system().lower() == 'windows'
if HAS_WIN32:
    try:
        import win32print
    except ImportError:
        HAS_WIN32 = False


def listar_impresoras_windows() -> List[str]:
    if not HAS_WIN32:
        return []
    try:
        printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        return printers
    except Exception:
        return []


def obtener_por_perfil(perfil: str, tipo: Optional[str] = None) -> Optional[Printer]:
    import json
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 Buscando impresora: perfil={perfil}, tipo={tipo}")
    
    try:
        printers = Printer.query.filter_by(estado=1).all()
        logger.info(f"📋 Total impresoras en BD: {len(printers)}")
        
        for p in printers:
            logger.info(f"  📌 Revisando: {p.nombre} (id={p.id})")
            try:
                # Log valores crudos antes de parsear
                logger.info(f"     perfil RAW: {repr(p.perfil)}")
                logger.info(f"     tipo RAW: {repr(p.tipo)}")
                
                perfiles = json.loads(p.perfil) if isinstance(p.perfil, str) else p.perfil
                tipos = json.loads(p.tipo) if isinstance(p.tipo, str) else p.tipo
                
                logger.info(f"     Perfiles parseados: {perfiles}")
                logger.info(f"     Tipos parseados: {tipos}")
                logger.info(f"     ¿'{perfil}' in {perfiles}? {perfil in perfiles}")
                logger.info(f"     ¿'{tipo}' in {tipos}? {tipo in tipos if tipo else 'N/A'}")
                
                if perfil in perfiles:
                    if tipo is None or tipo in tipos:
                        logger.info(f"✅ Impresora encontrada: {p.nombre}")
                        logger.info(f"   driver_name={p.driver_name}, printhost_url={p.printhost_url}")
                        return p
                    else:
                        logger.info(f"   ⚠️ Perfil coincide pero tipo '{tipo}' no está en {tipos}")
                else:
                    logger.info(f"   ⚠️ Perfil '{perfil}' no está en {perfiles}")
                    
            except json.JSONDecodeError as e:
                logger.warning(f"  ⚠️ Error parsing JSON para {p.nombre}: {e}")
                continue
            except Exception as e:
                logger.warning(f"  ⚠️ Error procesando {p.nombre}: {e}")
                import traceback
                logger.warning(traceback.format_exc())
                continue
        
        logger.warning(f"❌ No se encontró impresora con perfil={perfil}, tipo={tipo}")
        return None
    except Exception as e:
        logger.error(f"❌ Error en obtener_por_perfil: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def guardar_driver(printer_id: int, driver_name: str) -> bool:
    pr = Printer.query.get(printer_id)
    if not pr:
        return False
    pr.driver_name = driver_name
    db.session.commit()
    return True


def mapear_perfiles() -> Dict[str, Dict[str, Optional[Printer]]]:
    perfiles = ['general', 'delivery', 'mostrador', 'cocina']
    tipos = ['ticket', 'comanda', 'factura', 'cocina']
    result: Dict[str, Dict[str, Optional[Printer]]] = {}
    for perfil in perfiles:
        result[perfil] = {}
        for tipo in tipos:
            result[perfil][tipo] = obtener_por_perfil(perfil, tipo)
    return result
