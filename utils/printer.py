import platform
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Imports condicionales para Windows (win32print solo disponible en Windows)
HAS_WIN32 = platform.system().lower() == 'windows'
if HAS_WIN32:
    try:
        import win32print
        import win32api
    except ImportError:
        HAS_WIN32 = False
        logger.warning("win32print no disponible - impresión térmica deshabilitada")
else:
    logger.info("Sistema no-Windows detectado - impresión térmica deshabilitada")

# Comandos ESC/POS para impresoras térmicas
ESC = b'\x1b'  # Escape
GS = b'\x1d'   # Group Separator

# Comando de corte de papel (parcial)
CUT_PAPER = GS + b'V\x01'  # Corte parcial
# Comando de corte de papel (total)  
CUT_PAPER_FULL = GS + b'V\x00'  # Corte total

# Avance de líneas
FEED_LINES = lambda n: ESC + b'd' + bytes([n])  # Avanza n líneas


class ThermalPrinter:
    def __init__(self, printer_name=None):
        """
        Inicializa la impresora térmica usando Windows Print Spooler
        printer_name: nombre de la impresora en Windows (ej: "EPSON TM-T88V Receipt5")
        Si es None, usa la impresora predeterminada
        """
        self.printer_name = printer_name
        self.printer = None
        
        if not HAS_WIN32:
            logger.warning("win32print no disponible - impresora no inicializada")
            return
        
        try:
            if not printer_name:
                # Usar impresora predeterminada
                self.printer = win32print.GetDefaultPrinter()
                logger.info(f"Usando impresora predeterminada: {self.printer}")
            else:
                self.printer = printer_name
                logger.info(f"Impresora seleccionada: {self.printer}")
                
        except Exception as e:
            logger.error(f"Error al inicializar impresora: {str(e)}")
            self.printer = None
    
    def imprimir_pedido(self, pedido, cliente, items, total_con_envio):
        """
        Imprime el detalle completo del pedido en formato de recibo
        """
        if not self.printer:
            logger.error("Impresora no disponible")
            return False
        
        try:
            # Crear contenido de impresión
            contenido = self._generar_recibo(pedido, cliente, items, total_con_envio)
            
            # Imprimir usando Windows Print Spooler
            hprinter = win32print.OpenPrinter(self.printer)
            
            try:
                # Enviar contenido a la impresora
                win32print.StartDocPrinter(hprinter, 1, ("Recibo Pedido", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                
                # Convertir contenido a bytes y enviar
                contenido_bytes = contenido.encode('utf-8', errors='replace')
                win32print.WritePrinter(hprinter, contenido_bytes)
                
                # Avanzar papel y cortar
                win32print.WritePrinter(hprinter, FEED_LINES(5))  # 5 líneas de avance
                win32print.WritePrinter(hprinter, CUT_PAPER)  # Corte parcial
                
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                
                logger.info(f"Pedido {pedido.id} impreso exitosamente")
                return True
                
            finally:
                win32print.ClosePrinter(hprinter)
                
        except Exception as e:
            logger.error(f"Error al imprimir: {str(e)}")
            return False
    
    def _generar_recibo(self, pedido, cliente, items, total_con_envio):
        """Genera el contenido del recibo en formato texto"""
        
        lineas = []
        ancho = 42  # Ancho estándar para 80mm
        
        # Encabezado
        lineas.append(self._centrar("MUNDO WAFFLES", ancho))
        lineas.append(self._centrar("Delivery", ancho))
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        # Información del pedido
        lineas.append(f"Pedido #: {pedido.id}")
        lineas.append(f"Fecha: {pedido.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
        lineas.append("")
        
        # Información del cliente
        lineas.append("CLIENTE:")
        if cliente and cliente.persona:
            lineas.append(f"  {cliente.persona.razon_social}")
            lineas.append(f"  Tel: {cliente.persona.telefono}")
            lineas.append(f"  Dir: {cliente.persona.direccion}")
        lineas.append("")
        
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        # Items
        lineas.append("ITEMS:")
        lineas.append("")
        
        for item in items:
            cantidad = item.cantidad
            producto = item.producto.nombre[:30]  # Limitar longitud
            precio_venta = float(item.precio_venta)
            subtotal = cantidad * precio_venta
            
            lineas.append(f"{producto}")
            lineas.append(f"  x{cantidad} @ ${precio_venta:.2f} = ${subtotal:.2f}")
            
            # Atributos si existen
            if item.atributos_seleccionados:
                import json
                try:
                    atributos = json.loads(item.atributos_seleccionados)
                    for key, value in atributos.items():
                        lineas.append(f"    - {key}: {value}")
                except:
                    pass
            
            lineas.append("")
        
        # Resumen
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        subtotal = float(pedido.total)
        costo_envio = float(pedido.costo_envio) if pedido.costo_envio else 0
        total = subtotal + costo_envio
        
        lineas.append(f"Subtotal:              ${subtotal:>8.2f}")
        lineas.append(f"Envío:                 ${costo_envio:>8.2f}")
        lineas.append("-" * ancho)
        lineas.append(f"TOTAL:                 ${total:>8.2f}")
        lineas.append("")
        lineas.append("")
        
        # Estado
        estado_texto = {
            1: "EN PREPARACION",
            2: "EN CAMINO",
            3: "ENTREGADO"
        }.get(pedido.estado_delivery, "DESCONOCIDO")
        
        lineas.append(self._centrar(f"Estado: {estado_texto}", ancho))
        lineas.append("")
        lineas.append(self._centrar("Gracias por su compra!", ancho))
        lineas.append("")
        lineas.append("")
        lineas.append("")
        
        return "\n".join(lineas)
    
    def imprimir_comanda_cocina(self, pedido, items, tipo_pedido="MOSTRADOR"):
        """
        Imprime una comanda para cocina con los productos a preparar
        Esta comanda se imprime automáticamente al crear un nuevo pedido
        
        Args:
            pedido: Objeto Venta con la información del pedido
            items: Lista de items del carrito (dict) o ProductoVenta
            tipo_pedido: "MOSTRADOR" o "DELIVERY"
        """
        if not self.printer:
            logger.error("Impresora no disponible para comanda")
            return False
        
        try:
            contenido = self._generar_comanda_cocina(pedido, items, tipo_pedido)
            
            hprinter = win32print.OpenPrinter(self.printer)
            
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Comanda Cocina", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                contenido_bytes = contenido.encode('utf-8', errors='replace')
                win32print.WritePrinter(hprinter, contenido_bytes)
                
                # Avanzar papel y cortar
                win32print.WritePrinter(hprinter, FEED_LINES(5))  # 5 líneas de avance
                win32print.WritePrinter(hprinter, CUT_PAPER)  # Corte parcial
                
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                
                logger.info(f"Comanda cocina pedido #{pedido.id} impresa exitosamente")
                return True
                
            finally:
                win32print.ClosePrinter(hprinter)
                
        except Exception as e:
            logger.error(f"Error al imprimir comanda: {str(e)}")
            return False
    
    def _generar_comanda_cocina(self, pedido, items, tipo_pedido):
        """Genera el contenido de la comanda para cocina - versión compacta"""
        
        lineas = []
        ancho = 42
        
        # Encabezado mínimo
        lineas.append("")
        lineas.append(f"#%s   %s" % (pedido.id, tipo_pedido))
        lineas.append(pedido.fecha_hora.strftime('%d/%m %H:%M'))
        lineas.append("-" * ancho)
        
        # Productos con letra grande (doble altura simulada con espaciado)
        for item in items:
            if isinstance(item, dict):
                cantidad = item['cantidad']
                nombre = item['nombre']
            else:
                cantidad = item.cantidad
                nombre = item.producto.nombre if hasattr(item, 'producto') else str(item)
            
            # Formato compacto: cantidad x nombre
            lineas.append(f"{cantidad}x {nombre.upper()}")
        
        lineas.append("-" * ancho)
        lineas.append("")
        
        return "\n".join(lineas)
    
    def imprimir_comanda_agregados(self, pedido, productos):
        """Imprime comanda con productos AGREGADOS a un pedido existente"""
        if not self.printer:
            return False
        
        try:
            lineas = []
            ancho = 42
            
            lineas.append("")
            lineas.append(f"#%s   AGREGADO" % pedido.id)
            lineas.append("-" * ancho)
            
            for item in productos:
                lineas.append(f"{item['cantidad']}x {item['nombre'].upper()}")
            
            lineas.append("-" * ancho)
            lineas.append("")
            
            contenido = "\n".join(lineas)
            
            hprinter = win32print.OpenPrinter(self.printer)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Comanda Agregados", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, contenido.encode('utf-8', errors='replace'))
                win32print.WritePrinter(hprinter, FEED_LINES(3))
                win32print.WritePrinter(hprinter, CUT_PAPER)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                return True
            finally:
                win32print.ClosePrinter(hprinter)
                
        except Exception as e:
            logger.error(f"Error imprimir comanda agregados: {str(e)}")
            return False
    
    def imprimir_comanda_eliminados(self, pedido, productos):
        """Imprime comanda con productos ELIMINADOS de un pedido"""
        if not self.printer:
            return False
        
        try:
            lineas = []
            ancho = 42
            
            lineas.append("")
            lineas.append(f"#%s   ELIMINADO" % pedido.id)
            lineas.append("-" * ancho)
            
            for item in productos:
                lineas.append(f"{item['cantidad']}x {item['nombre'].upper()}")
            
            lineas.append("-" * ancho)
            lineas.append("")
            
            contenido = "\n".join(lineas)
            
            hprinter = win32print.OpenPrinter(self.printer)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Comanda Eliminados", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, contenido.encode('utf-8', errors='replace'))
                win32print.WritePrinter(hprinter, FEED_LINES(3))
                win32print.WritePrinter(hprinter, CUT_PAPER)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                return True
            finally:
                win32print.ClosePrinter(hprinter)
                
        except Exception as e:
            logger.error(f"Error imprimir comanda eliminados: {str(e)}")
            return False
    
    def imprimir_comprobante_delivery(self, pedido, cliente, productos):
        """
        Imprime el comprobante de delivery para el repartidor
        Se imprime al momento de enviar el pedido
        """
        if not self.printer:
            logger.error("Impresora no disponible")
            return False
        
        try:
            contenido = self._generar_comprobante_delivery(pedido, cliente, productos)
            
            hprinter = win32print.OpenPrinter(self.printer)
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Comprobante Delivery", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                win32print.WritePrinter(hprinter, contenido.encode('utf-8', errors='replace'))
                win32print.WritePrinter(hprinter, FEED_LINES(5))
                win32print.WritePrinter(hprinter, CUT_PAPER)
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                logger.info(f"Comprobante delivery #{pedido.id} impreso")
                return True
            finally:
                win32print.ClosePrinter(hprinter)
                
        except Exception as e:
            logger.error(f"Error imprimir comprobante delivery: {str(e)}")
            return False
    
    def _generar_comprobante_delivery(self, pedido, cliente, productos):
        """Genera el contenido del comprobante de delivery"""
        lineas = []
        ancho = 42
        
        # Título
        lineas.append("")
        lineas.append(self._centrar("MUNDO WAFFLES", ancho))
        lineas.append(self._centrar("=" * 20, ancho))
        lineas.append("")
        
        # Número de pedido, fecha y hora
        lineas.append(f"Pedido #: {pedido.id}")
        lineas.append(f"Fecha: {pedido.fecha_hora.strftime('%d/%m/%Y')}")
        lineas.append(f"Hora:  {pedido.fecha_hora.strftime('%H:%M')}")
        lineas.append("")
        
        # Datos del cliente
        lineas.append("-" * ancho)
        lineas.append("DATOS DEL CLIENTE")
        lineas.append("-" * ancho)
        if cliente and cliente.persona:
            lineas.append(f"Nombre: {cliente.persona.razon_social or 'Sin nombre'}")
            lineas.append(f"Fono:   {cliente.persona.telefono or 'Sin telefono'}")
            lineas.append(f"Dir:    {cliente.persona.direccion or 'Sin direccion'}")
        else:
            lineas.append("Cliente no registrado")
        lineas.append("")
        
        # Detalle de productos
        lineas.append("-" * ancho)
        lineas.append("DETALLE DE PRODUCTOS")
        lineas.append("-" * ancho)
        
        subtotal = 0
        for item in productos:
            nombre = item.producto.nombre if hasattr(item, 'producto') else str(item)
            cantidad = item.cantidad
            precio = float(item.precio_venta)
            item_total = cantidad * precio
            subtotal += item_total
            
            lineas.append(f"{cantidad}x {nombre[:25]}")
            lineas.append(f"   ${precio:,.0f} c/u = ${item_total:,.0f}")
        
        lineas.append("")
        lineas.append("-" * ancho)
        
        # Totales
        costo_envio = float(pedido.costo_envio or 0)
        total = subtotal + costo_envio
        
        lineas.append(f"{'Subtotal:':<30} ${subtotal:,.0f}")
        lineas.append(f"{'Costo Envio:':<30} ${costo_envio:,.0f}")
        lineas.append("-" * ancho)
        lineas.append(f"{'TOTAL:':<30} ${total:,.0f}")
        lineas.append("")
        
        # Mensaje final
        lineas.append(self._centrar("Gracias por su preferencia!", ancho))
        lineas.append("")
        lineas.append("")
        
        return "\n".join(lineas)
    
    def imprimir_pedido_mostrador(self, pedido, items):
        """
        Imprime el detalle de un pedido de mostrador
        """
        if not self.printer:
            logger.error("Impresora no disponible")
            return False
        
        try:
            contenido = self._generar_recibo_mostrador(pedido, items)
            
            hprinter = win32print.OpenPrinter(self.printer)
            
            try:
                win32print.StartDocPrinter(hprinter, 1, ("Recibo Mostrador", None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                contenido_bytes = contenido.encode('utf-8', errors='replace')
                win32print.WritePrinter(hprinter, contenido_bytes)
                
                # Avanzar papel y cortar
                win32print.WritePrinter(hprinter, FEED_LINES(5))  # 5 líneas de avance
                win32print.WritePrinter(hprinter, CUT_PAPER)  # Corte parcial
                
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                
                logger.info(f"Pedido mostrador {pedido.id} impreso exitosamente")
                return True
                
            finally:
                win32print.ClosePrinter(hprinter)
                
        except Exception as e:
            logger.error(f"Error al imprimir: {str(e)}")
            return False
    
    def _generar_recibo_mostrador(self, pedido, items):
        """Genera el contenido del recibo de mostrador"""
        
        lineas = []
        ancho = 42
        
        # Encabezado
        lineas.append(self._centrar("MUNDO WAFFLES", ancho))
        lineas.append(self._centrar("Mostrador", ancho))
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        # Información del pedido
        lineas.append(f"Pedido #: {pedido.id}")
        lineas.append(f"Fecha: {pedido.fecha_hora.strftime('%d/%m/%Y %H:%M')}")
        if pedido.comentarios:
            lineas.append(f"Cliente: {pedido.comentarios}")
        lineas.append("")
        
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        # Items
        lineas.append("ITEMS:")
        lineas.append("")
        
        for item in items:
            cantidad = item.cantidad
            producto = item.producto.nombre[:30]
            precio_venta = float(item.precio_venta)
            subtotal = cantidad * precio_venta
            
            lineas.append(f"{producto}")
            lineas.append(f"  x{cantidad} @ ${precio_venta:.2f} = ${subtotal:.2f}")
            lineas.append("")
        
        # Resumen
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        total = float(pedido.total)
        lineas.append("-" * ancho)
        lineas.append(f"TOTAL:                 ${total:>8.2f}")
        lineas.append("")
        lineas.append("")
        
        lineas.append(self._centrar("Gracias por su compra!", ancho))
        lineas.append("")
        lineas.append("")
        lineas.append("")
        
        return "\n".join(lineas)
    
    def _centrar(self, texto, ancho):
        """Centra texto en el ancho especificado"""
        if len(texto) >= ancho:
            return texto[:ancho]
        espacios = (ancho - len(texto)) // 2
        return " " * espacios + texto
    
    def cerrar(self):
        """Cierra la conexión con la impresora"""
        pass  # Windows Print Spooler se cierra automáticamente


def get_printer(app=None):
    """
    Obtiene instancia de impresora según configuración
    Configurar en config.py:
    PRINTER_NAME = 'EPSON TM-T88V Receipt5'
    """
    if app is None:
        from flask import current_app
        app = current_app
    
    printer_name = app.config.get('PRINTER_NAME', None)
    return ThermalPrinter(printer_name)


def get_printer_by_profile(perfil: str, tipo: str = None, app=None):
    """
    Obtiene una instancia de ThermalPrinter según el perfil/tipo configurado en BD.
    Si no hay coincidencia, cae al valor de config `PRINTER_NAME`.
    """
    if app is None:
        from flask import current_app
        app = current_app
    try:
        from utils.printer_manager import obtener_por_perfil
        pr = obtener_por_perfil(perfil, tipo)
        if pr and pr.driver_name:
            return ThermalPrinter(pr.driver_name)
    except Exception:
        pass
    return get_printer(app)