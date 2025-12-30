import platform
import logging
from datetime import datetime
import sys

logger = logging.getLogger(__name__)

# DEBUG: Escribir información de diagnóstico a un archivo
debug_file = "/tmp/printer_debug.log" if platform.system() != 'Windows' else "C:\\Temp\\printer_debug.log"
try:
    with open(debug_file, "a") as f:
        f.write(f"\n[{datetime.now()}] Cargando utils/printer.py\n")
        f.write(f"  Sistema: {platform.system()}\n")
        f.write(f"  Python: {sys.version}\n")
        f.write(f"  Path: {sys.path[:3]}\n")
except:
    pass

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
        # DEBUG: Log de intento de import
        try:
            with open(debug_file, "a") as f:
                f.write(f"[{datetime.now()}] Intentando importar PrintHostClient...\n")
        except:
            pass
        
        from utils.print_client import PrintHostClient
        logger.info("PrintHostClient disponible para impresión remota")
        
        try:
            with open(debug_file, "a") as f:
                f.write(f"[{datetime.now()}] PrintHostClient importado exitosamente\n")
        except:
            pass
            
    except ImportError as e:
        PRINTHOST_ENABLED = False
        logger.error(f"ImportError cargando PrintHostClient: {e}")
        try:
            with open(debug_file, "a") as f:
                f.write(f"[{datetime.now()}] ImportError: {e}\n")
                import traceback
                f.write(traceback.format_exc())
        except:
            pass
            
    except Exception as e:
        PRINTHOST_ENABLED = False
        logger.error(f"Error inesperado cargando PrintHostClient: {type(e).__name__}: {e}")
        try:
            with open(debug_file, "a") as f:
                f.write(f"[{datetime.now()}] Exception ({type(e).__name__}): {e}\n")
                import traceback
                f.write(traceback.format_exc())
        except:
            pass

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
        
        logger.debug(f"ThermalPrinter.__init__: printer_name={printer_name}, printhost_url={printhost_url}, HAS_WIN32={HAS_WIN32}, PRINTHOST_ENABLED={PRINTHOST_ENABLED}")
        
        if HAS_WIN32:
            # ===== MODO WINDOWS: win32print local =====
            try:
                if not printer_name:
                    self.printer = win32print.GetDefaultPrinter()
                    logger.info(f"✅ Usando impresora predeterminada: {self.printer}")
                else:
                    self.printer = printer_name
                    logger.info(f"✅ Impresora Windows seleccionada: {self.printer}")
            except Exception as e:
                logger.error(f"❌ Error al inicializar impresora Windows: {str(e)}")
                self.printer = None
        
        elif PRINTHOST_ENABLED and printhost_url:
            # ===== MODO LINUX: PrintHost remoto =====
            try:
                self.printhost_client = PrintHostClient(printhost_url)
                if self.printhost_client.health_check():
                    logger.info(f"✅ PrintHost conectado: {printhost_url}")
                else:
                    logger.warning(f"⚠️ PrintHost no responde a health check: {printhost_url}")
            except Exception as e:
                logger.error(f"❌ Error al conectar PrintHost en {printhost_url}: {e}")
                self.printhost_client = None
        else:
            logger.warning(f"⚠️ No hay método de impresión disponible (HAS_WIN32={HAS_WIN32}, PRINTHOST_ENABLED={PRINTHOST_ENABLED}, printhost_url={printhost_url})")

    # ===== Funciones de formato =====
    def _format_precio(self, valor):
        """
        Formatea un valor numérico como precio en pesos chileno
        Ejemplo: 1000 -> $1.000, 1500000 -> $1.500.000
        """
        try:
            valor_int = int(float(valor))
            # Convertir a string y agregar separadores de miles
            valor_str = f"{valor_int:,}".replace(",", ".")
            return f"${valor_str}"
        except (ValueError, TypeError):
            return "$0"

    # ===== Serialización de datos para enviar a PrintHost =====
    def _serialize_pedido(self, pedido):
        # Obtener información del método de pago
        metodo_pago_nombre = None
        if hasattr(pedido, 'metodo_pago') and pedido.metodo_pago:
            metodo_pago_nombre = pedido.metodo_pago.nombre
        
        return {
            'id': getattr(pedido, 'id', None),
            'fecha_hora': getattr(pedido, 'fecha_hora', None).isoformat() if getattr(pedido, 'fecha_hora', None) else None,
            'total': float(getattr(pedido, 'total', 0) or 0),
            'costo_envio': float(getattr(pedido, 'costo_envio', 0) or 0),
            'estado_delivery': getattr(pedido, 'estado_delivery', None),
            'comentarios': getattr(pedido, 'comentarios', None),
            'metodo_pago': metodo_pago_nombre,
            'monto_recibido': float(getattr(pedido, 'monto_recibido', 0) or 0) if getattr(pedido, 'monto_recibido', None) else None,
            'vuelto': float(getattr(pedido, 'vuelto', 0) or 0) if getattr(pedido, 'vuelto', None) else None,
            'referencia_pago': getattr(pedido, 'referencia_pago', None),
        }

    def _serialize_cliente(self, cliente):
        if not cliente or not getattr(cliente, 'persona', None):
            return {}
        persona = cliente.persona
        
        # Serializar documento correctamente
        documento_str = None
        if hasattr(persona, 'documento') and persona.documento:
            if hasattr(persona.documento, 'tipo_documento'):
                documento_str = persona.documento.tipo_documento
            else:
                documento_str = str(persona.documento)
        
        return {
            'razon_social': getattr(persona, 'razon_social', None),
            'telefono': getattr(persona, 'telefono', None),
            'direccion': getattr(persona, 'direccion', None),
            'documento': documento_str,
        }

    def _serialize_items(self, items):
        serializados = []
        for item in items:
            extras = []
            if getattr(item, 'atributos_seleccionados', None):
                import json
                try:
                    atributos = item.atributos_seleccionados
                    if isinstance(atributos, str):
                        atributos = json.loads(atributos)
                    # Ahora es lista de {id, valor, precio_adicional}
                    if isinstance(atributos, list):
                        extras = atributos
                except Exception:
                    extras = []
            serializados.append({
                'nombre': getattr(item.producto, 'nombre', str(item)) if getattr(item, 'producto', None) else str(item),
                'cantidad': getattr(item, 'cantidad', 1),
                'precio_venta': float(getattr(item, 'precio_venta', 0) or 0),
                'subtotal': float(getattr(item, 'cantidad', 1)) * float(getattr(item, 'precio_venta', 0) or 0),
                'extras': extras,
                'notas': getattr(item, 'notas', None) or '',
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
        # Obtener cliente desde relación o desde comentarios (para mostrador)
        cliente_data = {}
        if hasattr(pedido, 'cliente') and getattr(pedido, 'cliente', None):
            # Delivery: cliente desde relación
            cliente_data = self._serialize_cliente(pedido.cliente)
        elif hasattr(pedido, 'comentarios') and getattr(pedido, 'comentarios', None):
            # Mostrador: cliente desde comentarios
            cliente_data = {'razon_social': pedido.comentarios}
        
        items_serializados = []
        for item in items:
            if isinstance(item, dict):
                item_data = {
                    'nombre': item.get('nombre'),
                    'cantidad': item.get('cantidad'),
                    'extras': item.get('extras', []),
                }
            else:
                extras = []
                if hasattr(item, 'atributos_seleccionados') and item.atributos_seleccionados:
                    import json
                    try:
                        atributos = item.atributos_seleccionados
                        if isinstance(atributos, str):
                            atributos = json.loads(atributos)
                        if isinstance(atributos, list):
                            extras = atributos
                    except:
                        pass
                item_data = {
                    'nombre': getattr(item, 'nombre', None) or getattr(item.producto, 'nombre', str(item)) if hasattr(item, 'producto') else str(item),
                    'cantidad': getattr(item, 'cantidad', 1),
                    'extras': extras,
                }
            items_serializados.append(item_data)
        
        return {
            'pedido': self._serialize_pedido(pedido),
            'items': items_serializados,
            'tipo': tipo,
            'cliente': cliente_data,
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
                    'precio_venta': float(getattr(p, 'precio_venta', 0) or 0) if hasattr(p, 'precio_venta') else (float(p.get('precio_venta', 0)) if isinstance(p, dict) else 0),
                }
                for p in productos
            ],
        }

    def _payload_mostrador(self, pedido, items):
        items_serializados = []
        for item in items:
            extras = []
            if hasattr(item, 'atributos_seleccionados') and item.atributos_seleccionados:
                import json
                try:
                    atributos = item.atributos_seleccionados
                    if isinstance(atributos, str):
                        atributos = json.loads(atributos)
                    if isinstance(atributos, list):
                        extras = atributos
                except:
                    pass
            items_serializados.append({
                'nombre': getattr(item.producto, 'nombre', str(item)) if hasattr(item, 'producto') else str(item),
                'cantidad': getattr(item, 'cantidad', 1),
                'precio_venta': float(getattr(item, 'precio_venta', 0) or 0),
                'subtotal': float(getattr(item, 'cantidad', 1)) * float(getattr(item, 'precio_venta', 0) or 0),
                'extras': extras,
            })
        return {
            'pedido': self._serialize_pedido(pedido),
            'items': items_serializados,
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
        contenido = self._generar_recibo(pedido, cliente, items)
        
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
    
    def _generar_recibo(self, pedido, cliente, items):
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
            lineas.append(f"  Nombre:  {cliente.persona.razon_social}")
            lineas.append(f"  Fono: {cliente.persona.telefono}")
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
            
            precio_fmt = self._format_precio(precio_venta)
            subtotal_fmt = self._format_precio(subtotal)
            
            lineas.append(f"{producto}")
            lineas.append(f"  x{cantidad} @ {precio_fmt} = {subtotal_fmt}")
            
            # Extras si existen
            if item.atributos_seleccionados:
                import json
                try:
                    extras = item.atributos_seleccionados
                    if isinstance(extras, str):
                        extras = json.loads(extras)
                    if isinstance(extras, list):
                        for extra in extras:
                            valor = extra.get('valor', '')
                            precio_extra = float(extra.get('precio_adicional', 0))
                            if precio_extra > 0:
                                lineas.append(f"    + {valor} (+${precio_extra:,.0f})")
                            else:
                                lineas.append(f"    + {valor}")
                except:
                    pass
            
            lineas.append("")
        
        # Resumen
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        subtotal = float(pedido.total)
        costo_envio = float(pedido.costo_envio) if pedido.costo_envio else 0
        total = subtotal + costo_envio
        
        subtotal_fmt = self._format_precio(subtotal)
        envio_fmt = self._format_precio(costo_envio)
        total_fmt = self._format_precio(total)
        
        lineas.append(f"Subtotal:              {subtotal_fmt:>10}")
        lineas.append(f"Envío:                 {envio_fmt:>10}")
        lineas.append("-" * ancho)
        lineas.append(f"TOTAL:                 {total_fmt:>10}")
        lineas.append("")
        lineas.append("")
        
        lineas.append("")
        lineas.append(self._centrar("Gracias por su compra!", ancho))

        
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
        """
        Genera el contenido de la comanda para cocina - optimizado
        Formato:
        - Tipo de venta (MOSTRADOR/DELIVERY) en grande
        - Hora y cliente
        - Productos en letra grande
        - Mínimo papel posible
        """
        
        lineas = []
        ancho = 42
        
        # ===== ENCABEZADO COMPACTO =====
        # Tipo de venta (MOSTRADOR/DELIVERY) - centrado
        lineas.append("")
        lineas.append(self._centrar(f"=== {tipo_pedido} ===", ancho))
        
        # Pedido #, fecha y hora en una línea
        hora = pedido.fecha_hora.strftime('%H:%M')
        lineas.append(f"#{pedido.id:4d}  {hora}")
        
        # Cliente si disponible
        if hasattr(pedido, 'cliente') and pedido.cliente and hasattr(pedido.cliente, 'persona'):
            cliente_nombre = pedido.cliente.persona.razon_social[:20]  # Limitar a 20 caracteres
            lineas.append(f"CLIENTE: {cliente_nombre}")
        
        lineas.append("")
        
        # ===== PRODUCTOS (lo más importante) =====
        # Sin línea divisoria arriba para ahorrar papel
        for item in items:
            if isinstance(item, dict):
                cantidad = item['cantidad']
                nombre = item['nombre']
                extras = item.get('extras', [])
            else:
                cantidad = item.cantidad
                nombre = item.producto.nombre if hasattr(item, 'producto') else str(item)
                # Obtener extras del item
                extras = []
                if hasattr(item, 'atributos_seleccionados') and item.atributos_seleccionados:
                    import json
                    try:
                        atributos = item.atributos_seleccionados
                        if isinstance(atributos, str):
                            atributos = json.loads(atributos)
                        if isinstance(atributos, list):
                            extras = atributos
                    except:
                        pass
            
            # Formato: [cantidad]x NOMBRE (en mayúsculas para legibilidad)
            # Limitar nombre a 35 caracteres para que quepa con cantidad
            nombre_limpio = nombre.upper()[:35]
            lineas.append(f"{cantidad}x {nombre_limpio}")
            
            # Mostrar extras si existen
            for extra in extras:
                valor = extra.get('valor', '') if isinstance(extra, dict) else str(extra)
                lineas.append(f"   + {valor.upper()[:32]}")
            
            # Mostrar comentarios si existen
            if isinstance(item, dict):
                comentarios = item.get('comentarios', '')
            else:
                comentarios = item.notas if hasattr(item, 'notas') else ''
            
            if comentarios:
                lineas.append(f"   >> {comentarios.upper()[:35]}")
        
        lineas.append("")
        
        return "\n".join(lineas)
    
    def imprimir_comanda_agregados(self, pedido, productos):
        """Imprime comanda con productos AGREGADOS a un pedido existente"""
        try:
            lineas = []
            ancho = 42
            
            lineas.append("")
            lineas.append(self._centrar("=== AGREGADOS ===", ancho))
            lineas.append(f"Pedido #{pedido.id}")
            lineas.append("")
            
            for item in productos:
                nombre = item['nombre'].upper()[:35]
                lineas.append(f"{item['cantidad']}x {nombre}")
                # Mostrar extras si existen
                extras = item.get('extras', [])
                for extra in extras:
                    valor = extra.get('valor', '') if isinstance(extra, dict) else str(extra)
                    lineas.append(f"   + {valor.upper()[:32]}")
                # Mostrar comentarios si existen
                comentarios = item.get('comentarios', '')
                if comentarios:
                    lineas.append(f"   >> {comentarios.upper()[:35]}")
            
            lineas.append("")
            
            contenido = "\n".join(lineas)
            
            if PRINTHOST_ENABLED and self.printhost_client:
                payload = self._payload_agregados(pedido, productos)
                return self._enviar_printhost('agregados', payload, feed=2, cut=False)
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
            lineas.append(self._centrar("=== ELIMINADOS ===", ancho))
            lineas.append(f"Pedido #{pedido.id}")
            lineas.append("")
            
            for item in productos:
                nombre = item['nombre'].upper()[:35]
                lineas.append(f"{item['cantidad']}x {nombre}")
            
            lineas.append("")
            
            contenido = "\n".join(lineas)
            
            if PRINTHOST_ENABLED and self.printhost_client:
                payload = self._payload_eliminados(pedido, productos)
                return self._enviar_printhost('eliminados', payload, feed=2, cut=False)
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
        lineas.append(self._centrar("COMPROBANTE DELIVERY", ancho))
        lineas.append("")
        
        # Número de pedido, fecha y hora
        lineas.append(f"Pedido #:     {pedido.id}")
        lineas.append(f"Fecha:        {pedido.fecha_hora.strftime('%d/%m/%Y')}")
        lineas.append(f"Hora:         {pedido.fecha_hora.strftime('%H:%M')}")
        lineas.append("")
        
        # Datos del cliente
        lineas.append("=" * ancho)
        lineas.append("CLIENTE")
        lineas.append("=" * ancho)
        if cliente and cliente.persona:
            nombre = cliente.persona.razon_social or 'Sin nombre'
            # Limitar nombre a ancho de ticket
            lineas.append(f"Nombre: {nombre[:35]}")
            telefono = cliente.persona.telefono or 'Sin teléfono'
            lineas.append(f"Teléfono: {telefono}")
            direccion = cliente.persona.direccion or 'Sin dirección'
            # Ajustar dirección a múltiples líneas si es necesario
            if len(direccion) > 35:
                lineas.append(f"Dirección: {direccion[:35]}")
                lineas.append(f"           {direccion[35:70]}")
            else:
                lineas.append(f"Dirección: {direccion}")
        else:
            lineas.append("Cliente no registrado")
        lineas.append("")
        
        # Detalle de productos
        lineas.append("=" * ancho)
        lineas.append("DETALLE DE PRODUCTOS")
        lineas.append("=" * ancho)
        
        subtotal = 0
        for item in productos:
            nombre = item.producto.nombre if hasattr(item, 'producto') else str(item)
            cantidad = item.cantidad
            precio = float(item.precio_venta)
            item_total = cantidad * precio
            subtotal += item_total
            
            # Formato: "2x Waffle Nutella"
            lineas.append(f"{cantidad}x {nombre[:28]}")
            # Precio unitario y total
            precio_fmt = self._format_precio(precio)
            total_fmt = self._format_precio(item_total)
            lineas.append(f"   {precio_fmt} c/u = {total_fmt}")
        
        lineas.append("")
        lineas.append("=" * ancho)
        
        # Totales
        costo_envio = float(pedido.costo_envio or 0)
        total = subtotal + costo_envio
        
        subtotal_fmt = self._format_precio(subtotal)
        envio_fmt = self._format_precio(costo_envio)
        total_fmt = self._format_precio(total)
        
        lineas.append(f"{'Subtotal:':<28} {subtotal_fmt:>11}")
        lineas.append(f"{'Envío:':<28} {envio_fmt:>11}")
        lineas.append("=" * ancho)
        lineas.append(f"{'TOTAL:':<28} {total_fmt:>11}")
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
        
        total = 0
        for item in items:
            cantidad = item.cantidad
            producto = item.producto.nombre[:30]
            precio_venta = float(item.precio_venta)
            subtotal = cantidad * precio_venta
            total += subtotal
            
            precio_fmt = self._format_precio(precio_venta)
            subtotal_fmt = self._format_precio(subtotal)
            
            lineas.append(f"{producto}")
            lineas.append(f"  x{cantidad} @ {precio_fmt} = {subtotal_fmt}")
            
            # Extras si existen
            if item.atributos_seleccionados:
                import json
                try:
                    extras = item.atributos_seleccionados
                    if isinstance(extras, str):
                        extras = json.loads(extras)
                    if isinstance(extras, list):
                        for extra in extras:
                            valor = extra.get('valor', '')
                            precio_extra = float(extra.get('precio_adicional', 0))
                            if precio_extra > 0:
                                lineas.append(f"    + {valor} (+${precio_extra:,.0f})")
                            else:
                                lineas.append(f"    + {valor}")
                except:
                    pass
            
            lineas.append("")
        
        # Resumen
        lineas.append(self._centrar("=" * ancho, ancho))
        lineas.append("")
        
        total_fmt = self._format_precio(total)
        lineas.append(f"TOTAL:                 {total_fmt:>10}")
        lineas.append("")
        lineas.append("")
        
        lineas.append(self._centrar("Gracias por su compra!", ancho))

        
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
    logger.info(f"🔍 get_printer_by_profile: perfil={perfil}, tipo={tipo}, PRINTHOST_URL_config={printhost_url}")
    
    try:
        from utils.printer_manager import obtener_por_perfil
        pr = obtener_por_perfil(perfil, tipo)
        logger.info(f"Resultado obtener_por_perfil: {pr}")
        
        if pr and pr.driver_name:
            logger.info(f"Impresora BD: nombre={pr.nombre}, driver={pr.driver_name}, printhost_url='{pr.printhost_url}'")
            # Usar printhost_url de BD si existe y no está vacío
            url_final = pr.printhost_url if pr.printhost_url and pr.printhost_url.strip() else printhost_url
            logger.info(f"✅ URL final seleccionada: {url_final}")
            return ThermalPrinter(pr.driver_name, url_final)
        else:
            logger.warning(f"❌ No se encontró impresora con perfil={perfil}, tipo={tipo}")
    except Exception as e:
        logger.error(f"❌ Error al buscar impresora por perfil: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("⚠️ Usando impresora por defecto desde config")
    return get_printer(app)