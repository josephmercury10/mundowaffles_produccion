from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request
from sqlalchemy import func, or_
from utils.db import db
from forms import ReporteVentasForm
from src.models.Venta_model import Venta
from src.models.MetodoPago_model import MetodoPago


reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')


def _resolver_rango(form):
    """Devuelve tupla (inicio, fin) en datetime según el rango seleccionado."""
    hoy = date.today()
    ahora = datetime.now()
    inicio = None
    fin = None

    if form.rango.data == 'hoy':
        inicio = datetime.combine(hoy, datetime.min.time())
        fin = datetime.combine(hoy, datetime.max.time())
    elif form.rango.data == 'semana':
        inicio_semana = hoy - timedelta(days=hoy.weekday())
        inicio = datetime.combine(inicio_semana, datetime.min.time())
        fin = datetime.combine(ahora.date(), datetime.max.time())
    elif form.rango.data == 'mes':
        inicio_mes = hoy.replace(day=1)
        inicio = datetime.combine(inicio_mes, datetime.min.time())
        fin = datetime.combine(ahora.date(), datetime.max.time())
    elif form.rango.data == 'personalizado':
        if form.fecha_desde.data:
            inicio = datetime.combine(form.fecha_desde.data, datetime.min.time())
        if form.fecha_hasta.data:
            fin = datetime.combine(form.fecha_hasta.data, datetime.max.time())
    # 'historico' deja sin límites
    return inicio, fin


def _es_venta_activa(venta):
    """
    Determina el estado de una venta:
    - Anulada: si el monto total es 0
    - Delivery: activa si estado_delivery < 3
    - Mostrador: activa si estado_mostrador < 2
    
    Retorna tupla: (es_activa: bool, estado: str)
    """
    try:
        total_float = float(venta.total or 0)
    except Exception:
        total_float = 0
    if total_float == 0:
        return False, 'Anulada'
    
    if venta.tipoventa_id == 2:  # Delivery
        if venta.estado_delivery and venta.estado_delivery < 3:
            return True, 'Activa'
        else:
            return False, 'Cerrada'
    elif venta.tipoventa_id == 1:  # Mostrador
        if venta.estado_mostrador is None or venta.estado_mostrador < 2:
            return True, 'Activa'
        else:
            return False, 'Cerrada'
    
    return False, 'Desconocido'


@reportes_bp.route('/ventas', methods=['GET'])
def ventas():
    form = ReporteVentasForm(request.args, meta={'csrf': False})

    # Poblar métodos de pago activos
    metodos_pago = MetodoPago.query.filter_by(estado=1).order_by(MetodoPago.nombre).all()
    form.metodo_pago.choices = [('', 'Todos')] + [(str(m.id), m.nombre) for m in metodos_pago]

    filtros = []
    inicio, fin = _resolver_rango(form)
    if inicio:
        filtros.append(Venta.fecha_hora >= inicio)
    if fin:
        filtros.append(Venta.fecha_hora <= fin)

    if form.metodo_pago.data:
        try:
            filtros.append(Venta.metodo_pago_id == int(form.metodo_pago.data))
        except ValueError:
            pass

    if form.canal.data == 'mostrador':
        filtros.append(Venta.tipoventa_id == 1)
    elif form.canal.data == 'delivery':
        filtros.append(Venta.tipoventa_id == 2)

    # Filtrado de estado basado en canal
    if form.estado.data == '1':
        # Activas: delivery con estado_delivery < 3, mostrador con estado_mostrador < 2
        filtros.append(
            or_(
                (Venta.tipoventa_id == 2) & (Venta.estado_delivery < 3),
                (Venta.tipoventa_id == 1) & ((Venta.estado_mostrador == None) | (Venta.estado_mostrador < 2))
            )
        )
    elif form.estado.data == '0':
        # Inactivas: delivery con estado_delivery == 3, mostrador con estado_mostrador >= 2
        filtros.append(
            or_(
                (Venta.tipoventa_id == 2) & (Venta.estado_delivery == 3),
                (Venta.tipoventa_id == 1) & (Venta.estado_mostrador >= 2)
            )
        )

    base_query = Venta.query.filter(*filtros)

    ventas = base_query.order_by(Venta.fecha_hora.desc()).limit(200).all()
    total_ventas = base_query.count()

    total_monto_raw = db.session.query(func.coalesce(func.sum(Venta.total), 0)).filter(*filtros).scalar()
    total_monto = float(total_monto_raw or 0)
    ticket_promedio = total_monto / total_ventas if total_ventas else 0
    
    # condicional para sacar el nombre del cliente si es mostrador, ya que en ese caso se guarda en cometarios XD
    

    metodo_label = func.coalesce(MetodoPago.nombre, 'Sin método')
    totales_metodo_raw = (
        db.session.query(
            metodo_label.label('metodo'),
            func.count(Venta.id).label('cantidad'),
            func.coalesce(func.sum(Venta.total), 0).label('monto')
        )
        .select_from(Venta)
        .outerjoin(MetodoPago, Venta.metodo_pago_id == MetodoPago.id)
        .filter(*filtros)
        .group_by(metodo_label)
        .order_by(metodo_label)
        .all()
    )
    totales_metodo = [
        {
            'metodo': fila.metodo,
            'cantidad': fila.cantidad,
            'monto': float(fila.monto or 0)
        }
        for fila in totales_metodo_raw
    ]

    return render_template(
        'reportes/index.html',
        form=form,
        ventas=ventas,
        total_ventas=total_ventas,
        total_monto=total_monto,
        ticket_promedio=ticket_promedio,
        totales_metodo=totales_metodo,
        es_venta_activa=_es_venta_activa,
    )

