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
    logger.info("Sistema no-Windows detectado - usando PrintHost para impresión")

# PrintHost client (para Linux/PythonAnywhere)
PRINTHOST_ENABLED = not HAS_WIN32
if PRINTHOST_ENABLED:
    try:
        from utils.print_client import PrintHostClient
        logger.info("PrintHostClient disponible para impresión remota")
    except ImportError:
        PRINTHOST_ENABLED = False
        logger.warning("PrintHostClient no disponible")

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
    def __init__(self, printer_name=None, printhost_url=None):
        """
        Inicializa la impresora térmica
        
        Args:
            printer_name: Nombre de la impresora (ej: "EPSON TM-T88V Receipt5")
            printhost_url: URL del PrintHost (solo Linux, ej: "http://192.168.1.50:8765")
        
        Modo de operación:
            - Windows: usa win32print directo
            - Linux: usa PrintHostClient (HTTP)
        """
        self.printer_name = printer_name
        self.printhost_url = printhost_url
        self.printer = None
        self.printhost_client = None
        
        if HAS_WIN32:
            # ===== MODO WINDOWS: win32print local =====
            try:
                if not printer_name:
                    self.printer = win32print.GetDefaultPrinter()
                    logger.info(f"Usando impresora predeterminada: {self.printer}")
                else:
                    self.printer = printer_name
                    logger.info(f"Impresora seleccionada: {self.printer}")
            except Exception as e:
                logger.error(f"Error al inicializar impresora: {str(e)}")
                self.printer = None
        
        elif PRINTHOST_ENABLED and printhost_url:
            # ===== MODO LINUX: PrintHost remoto =====
            try:
                self.printhost_client = PrintHostClient(printhost_url)
                if self.printhost_client.health_check():
                    logger.info(f"✅ PrintHost conectado: {printhost_url}")
                else:
                    logger.warning(f"⚠️ PrintHost no responde: {printhost_url}")
            except Exception as e:
                logger.error(f"Error al conectar PrintHost: {e}")
                self.printhost_client = None
        else:
            logger.warning("No hay método de impresión disponible")

    # ===== Serialización de datos para enviar a PrintHost =====
    def _serialize_pedido(self, pedido):
        return {
            'id': getattr(pedido, 'id', None),
            'fecha_hora': getattr(pedido, 'fecha_hora', None).isoformat() if getattr(pedido, 'fecha_hora', None) else None,
            'total': float(getattr(pedido, 'total', 0) or 0),
            'costo_envio': float(getattr(pedido, 'costo_envio', 0) or 0),
            'estado_delivery': getattr(pedido, 'estado_delivery', None),
            'comentarios': getattr(pedido, 'comentarios', None),
        }

    def _serialize_cliente(self, cliente):
        if not cliente or not getattr(cliente, 'persona', None):
            return {}
        persona = cliente.persona
        return {
            'razon_social': getattr(persona, 'razon_social', None),
            'telefono': getattr(persona, 'telefono', None),
            'direccion': getattr(persona, 'direccion', None),
            'documento': getattr(persona, 'documento', None),
        }

    def _serialize_items(self, items):
        serializados = []
        for item in items:
            atributos = {}
            if getattr(item, 'atributos_seleccionados', None):
                import json
                try:
                    atributos = json.loads(item.atributos_seleccionados)
                except Exception:
                    atributos = {}
            serializados.append({
                'nombre': getattr(item.producto, 'nombre', str(item)) if getattr(item, 'producto', None) else str(item),
                'cantidad': getattr(item, 'cantidad', 1),
                'precio_venta': float(getattr(item, 'precio_venta', 0) or 0),
                'subtotal': float(getattr(item, 'cantidad', 1)) * float(getattr(item, 'precio_venta', 0) or 0),
                'atributos': atributos,
            })
        return serializados

    def _payload_pedido(self, pedido, cliente, items, total_con_envio):
        return {
            'pedido': self._serialize_pedido(pedido),
            'cliente': self._serialize_cliente(cliente),
            'items': self._serialize_items(items),
            'total_con_envio': float(total_con_envio or 0) if total_con_envio is not None else None,
        }

    def _payload_comanda(self, pedido, items, tipo):
        return {
            'pedido': self._serialize_pedido(pedido),
            'items': [
                {
                    'nombre': getattr(item, 'nombre', None) or getattr(item.producto, 'nombre', str(item)) if hasattr(item, 'producto') else str(item),
                    'cantidad': item.get('cantidad') if isinstance(item, dict) else getattr(item, 'cantidad', 1),
                }
                for item in items
            ],
            'tipo': tipo,
        }

    def _payload_agregados(self, pedido, productos):
        return {
            'pedido_id': getattr(pedido, 'id', None),
            'productos': productos,
        }

    def _payload_eliminados(self, pedido, productos):
        return {
            'pedido_id': getattr(pedido, 'id', None),
            'productos': productos,
        }

    def _payload_delivery(self, pedido, cliente, productos):
        return {
            'pedido': self._serialize_pedido(pedido),
            'cliente': self._serialize_cliente(cliente),
            'productos': [
                {
                    'nombre': getattr(p.producto, 'nombre', str(p)) if hasattr(p, 'producto') else p.get('nombre') if isinstance(p, dict) else str(p),
                    'cantidad': getattr(p, 'cantidad', None) or (p.get('cantidad') if isinstance(p, dict) else 1),
                }
                for p in productos
            ],
        }

    def _payload_mostrador(self, pedido, items):
        return {
            'pedido': self._serialize_pedido(pedido),
            'items': [
                {
                    'nombre': getattr(item.producto, 'nombre', str(item)) if hasattr(item, 'producto') else str(item),
                    'cantidad': getattr(item, 'cantidad', 1),
                    'precio_venta': float(getattr(item, 'precio_venta', 0) or 0),
                    'subtotal': float(getattr(item, 'cantidad', 1)) * float(getattr(item, 'precio_venta', 0) or 0),
                }
                for item in items
            ],
        }

    def _enviar_printhost(self, job_type, payload, feed=None, cut=None):
        if not self.printhost_client:
            logger.error("PrintHost no disponible")
            return False
        resultado = self.printhost_client.print_job(
            job_type=job_type,
            payload=payload,
            driver=self.printer_name,
            feed=feed,
            cut=cut,
        )
        if resultado.get('ok'):
            return True
        logger.error(f"❌ PrintHost error: {resultado.get('error')}")
        return False
    
    def imprimir_pedido(self, pedido, cliente, items, total_con_envio):
        """
        Imprime el detalle completo del pedido en formato de recibo
        Funciona en Windows (win32print) y Linux (PrintHost)
        """
        # Generar contenido del recibo
        contenido = self._generar_recibo(pedido, cliente, items, total_con_envio)
        
        # Seleccionar método de impresión
        if PRINTHOST_ENABLED and self.printhost_client:
            payload = self._payload_pedido(pedido, cliente, items, total_con_envio)
            return self._enviar_printhost('pedido', payload, feed=5, cut=True)
        if HAS_WIN32 and self.printer:
            return self._imprimir_local_windows(contenido, "Recibo Pedido")
        logger.error("No hay impresora configurada (ni local ni PrintHost)")
        return False
    
    def _imprimir_local_windows(self, contenido, titulo="Documento"):
        """Imprime localmente en Windows usando win32print"""
        if not self.printer:
            logger.error("Impresora Windows no disponible")
            return False
        
        try:
            hprinter = win32print.OpenPrinter(self.printer)
            
            try:
                win32print.StartDocPrinter(hprinter, 1, (titulo, None, "RAW"))
                win32print.StartPagePrinter(hprinter)
                
                # Convertir contenido a bytes y enviar
                contenido_bytes = contenido.encode('utf-8', errors='replace')
                win32print.WritePrinter(hprinter, contenido_bytes)
                
                # Avanzar papel y cortar
                win32print.WritePrinter(hprinter, FEED_LINES(5))
                win32print.WritePrinter(hprinter, CUT_PAPER)
                
                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)
                
                logger.info(f"✅ Documento '{titulo}' impreso localmente")
                return True
                
            finally:
                win32print.ClosePrinter(hprinter)
                
        except Exception as e:
            logger.error(f"❌ Error impresión local: {str(e)}")
            return False
    
    def _imprimir_remoto_printhost(self, contenido, pedido_id, tipo='raw'):
        """Imprime remotamente via PrintHost (HTTP)"""
        if not self.printhost_client:
            logger.error("PrintHost no disponible")
            return False
        
        try:
            resultado = self.printhost_client.print_job(
                job_type=tipo,
                payload={'content': contenido, 'pedido_id': pedido_id},
                driver=self.printer_name or "EPSON TM-T88V Receipt5",
                feed=5,
                cut=True,
            )
            if resultado.get('ok'):
                logger.info(f"✅ Impreso remotamente via PrintHost (pedido #{pedido_id})")
                return True
            error_msg = resultado.get('error', 'Error desconocido')
            logger.error(f"❌ PrintHost error: {error_msg}")
            return False
        except Exception as e:
            logger.error(f"❌ Error impresión remota: {e}")
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
        Funciona en Windows (win32print) y Linux (PrintHost)
        
        Args:
            pedido: Objeto Venta con la información del pedido
            items: Lista de items del carrito (dict) o ProductoVenta
            tipo_pedido: "MOSTRADOR" o "DELIVERY"
        """
        contenido = self._generar_comanda_cocina(pedido, items, tipo_pedido)
        
        if PRINTHOST_ENABLED and self.printhost_client:
            payload = self._payload_comanda(pedido, items, tipo_pedido)
            return self._enviar_printhost('comanda', payload, feed=3, cut=False)
        if HAS_WIN32 and self.printer:
            return self._imprimir_local_windows(contenido, "Comanda Cocina")
        logger.error("No hay impresora configurada")
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
            
            if PRINTHOST_ENABLED and self.printhost_client:
                payload = self._payload_agregados(pedido, productos)
                return self._enviar_printhost('agregados', payload, feed=3, cut=False)
            if HAS_WIN32 and self.printer:
                return self._imprimir_local_windows(contenido, "Comanda Agregados")
            logger.error("No hay impresora configurada")
            return False
                
        except Exception as e:
            logger.error(f"Error imprimir comanda agregados: {str(e)}")
            return False
    
    def imprimir_comanda_eliminados(self, pedido, productos):
        """Imprime comanda con productos ELIMINADOS de un pedido"""
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
            
            if PRINTHOST_ENABLED and self.printhost_client:
                payload = self._payload_eliminados(pedido, productos)
                return self._enviar_printhost('eliminados', payload, feed=3, cut=False)
            if HAS_WIN32 and self.printer:
                return self._imprimir_local_windows(contenido, "Comanda Eliminados")
            logger.error("No hay impresora configurada")
            return False
                
        except Exception as e:
            logger.error(f"Error imprimir comanda eliminados: {str(e)}")
            return False
    
    def imprimir_comprobante_delivery(self, pedido, cliente, productos):
        """
        Imprime el comprobante de delivery para el repartidor
        Se imprime al momento de enviar el pedido
        Funciona en Windows (win32print) y Linux (PrintHost)
        """
        contenido = self._generar_comprobante_delivery(pedido, cliente, productos)
        
        if PRINTHOST_ENABLED and self.printhost_client:
            payload = self._payload_delivery(pedido, cliente, productos)
            return self._enviar_printhost('delivery', payload, feed=4, cut=True)
        if HAS_WIN32 and self.printer:
            return self._imprimir_local_windows(contenido, "Comprobante Delivery")
        logger.error("No hay impresora configurada")
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
    
    def imprimir_pedido_mostrador(self, pedido, items):
        """
        Imprime el detalle de un pedido de mostrador
        Funciona en Windows (win32print) y Linux (PrintHost)
        """
        contenido = self._generar_recibo_mostrador(pedido, items)
        
        if PRINTHOST_ENABLED and self.printhost_client:
            payload = self._payload_mostrador(pedido, items)
            return self._enviar_printhost('pedido', payload, feed=5, cut=True)
        if HAS_WIN32 and self.printer:
            return self._imprimir_local_windows(contenido, "Recibo Mostrador")
        logger.error("No hay impresora configurada")
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
    - PRINTER_NAME = 'EPSON TM-T88V Receipt5'
    - PRINTHOST_URL = 'http://192.168.1.50:8765' (solo producción/Linux)
    """
    if app is None:
        from flask import current_app
        app = current_app
    
    printer_name = app.config.get('PRINTER_NAME', None)
    printhost_url = app.config.get('PRINTHOST_URL', None)
    
    return ThermalPrinter(printer_name, printhost_url)


def get_printer_by_profile(perfil: str, tipo: str = None, app=None):
    """
    Obtiene una instancia de ThermalPrinter según el perfil/tipo configurado en BD.
    Si no hay coincidencia, cae al valor de config `PRINTER_NAME`.
    """
    if app is None:
        from flask import current_app
        app = current_app
    
    printhost_url = app.config.get('PRINTHOST_URL', None)
    
    try:
        from utils.printer_manager import obtener_por_perfil
        pr = obtener_por_perfil(perfil, tipo)
        if pr and pr.driver_name:
            return ThermalPrinter(pr.driver_name, printhost_url)
    except Exception:
        pass
    
    return get_printer(app)