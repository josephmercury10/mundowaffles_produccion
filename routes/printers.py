from flask import Blueprint, render_template, redirect, url_for, flash, request
from utils.db import db
from src.models.Printer_model import Printer

printers_bp = Blueprint('printers', __name__, url_prefix='/printers')


@printers_bp.route('/')
def index():
    q = request.args.get('q', '').strip()
    estado = request.args.get('estado', 'todos')  # activos|inactivos|todos
    query = Printer.query
    if estado == 'activos':
        query = query.filter(Printer.estado == 1)
    elif estado == 'inactivos':
        query = query.filter(Printer.estado == 0)
    if q:
        like = f"%{q}%"
        query = query.filter(db.or_(Printer.nombre.ilike(like), Printer.driver_name.ilike(like), Printer.perfil.ilike(like)))
    printers = query.order_by(Printer.created_at.desc()).all()
    return render_template('printers/index.html', printers=printers, q=q, estado=estado)


@printers_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            import json
            data = request.form
            tipos = request.form.getlist('tipo')  # múltiples valores
            perfiles = request.form.getlist('perfil')
            if not tipos or not perfiles:
                flash('Debes seleccionar al menos un tipo y un perfil', 'warning')
                return render_template('printers/add.html')
            printer = Printer(
                nombre=data.get('nombre', '').strip(),
                driver_name=data.get('driver_name', '').strip(),
                tipo=json.dumps(tipos),
                perfil=json.dumps(perfiles),
                ancho_caracteres=int(data.get('ancho_caracteres', 42) or 42),
                cortar_papel=data.get('cortar_papel') == 'on',
                feed_lines=int(data.get('feed_lines', 3) or 3),
                estado=1,
            )
            db.session.add(printer)
            db.session.commit()
            flash('Impresora creada correctamente', 'success')
            return redirect(url_for('printers.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear impresora: {e}', 'danger')
    return render_template('printers/add.html')


@printers_bp.route('/update/<int:printer_id>', methods=['GET', 'POST'])
def update(printer_id: int):
    printer = Printer.query.get_or_404(printer_id)
    if request.method == 'POST':
        try:
            import json
            data = request.form
            tipos = request.form.getlist('tipo')
            perfiles = request.form.getlist('perfil')
            if not tipos or not perfiles:
                flash('Debes seleccionar al menos un tipo y un perfil', 'warning')
                return render_template('printers/update.html', printer=printer)
            printer.nombre = data.get('nombre', printer.nombre).strip()
            printer.driver_name = data.get('driver_name', printer.driver_name).strip()
            printer.tipo = json.dumps(tipos)
            printer.perfil = json.dumps(perfiles)
            printer.ancho_caracteres = int(data.get('ancho_caracteres', printer.ancho_caracteres) or printer.ancho_caracteres)
            printer.cortar_papel = data.get('cortar_papel') == 'on'
            printer.feed_lines = int(data.get('feed_lines', printer.feed_lines) or printer.feed_lines)
            db.session.commit()
            flash('Impresora actualizada', 'success')
            return redirect(url_for('printers.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {e}', 'danger')
    return render_template('printers/update.html', printer=printer)


@printers_bp.route('/delete/<int:printer_id>', methods=['POST'])
def delete(printer_id: int):
    printer = Printer.query.get_or_404(printer_id)
    try:
        printer.estado = 0
        db.session.commit()
        flash('Impresora desactivada', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desactivar: {e}', 'danger')
    return redirect(url_for('printers.index'))


@printers_bp.route('/activate/<int:printer_id>', methods=['POST'])
def activate(printer_id: int):
    printer = Printer.query.get_or_404(printer_id)
    try:
        printer.estado = 1
        db.session.commit()
        flash('Impresora activada', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al activar: {e}', 'danger')
    return redirect(url_for('printers.index', estado='activos'))
