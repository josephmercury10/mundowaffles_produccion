from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from src.models.AtributoProducto_model import AtributoProducto
from src.models.ValorAtributo_model import ValorAtributo
from utils.db import db
from forms import AtributoForm, ValorAtributoForm

atributos_bp = Blueprint('atributos', __name__, url_prefix='/atributos')


# ==========================================
# CRUD DE ATRIBUTOS (Extras)
# ==========================================

@atributos_bp.route('/')
def get_atributos():
    """Lista todos los atributos/extras"""
    atributos = AtributoProducto.query.order_by(AtributoProducto.orden).all()
    return render_template('atributos/atributos.html', atributos=atributos)


@atributos_bp.route('/add', methods=['GET', 'POST'])
def create_atributo():
    """Crear nuevo atributo/extra"""
    form = AtributoForm()
    
    if form.validate_on_submit():
        try:
            atributo = AtributoProducto(
                nombre=form.nombre.data,
                descripcion=form.descripcion.data,
                tipo=form.tipo.data,
                es_multiple=form.es_multiple.data,
                es_obligatorio=form.es_obligatorio.data,
                orden=form.orden.data or 0
            )
            db.session.add(atributo)
            db.session.commit()
            flash('Atributo creado exitosamente', 'success')
            return redirect(url_for('atributos.get_atributos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear atributo: {str(e)}', 'danger')
    
    return render_template('atributos/add.html', form=form)


@atributos_bp.route('/update/<int:id>', methods=['GET', 'POST'])
def update_atributo(id):
    """Actualizar atributo existente"""
    atributo = AtributoProducto.query.get_or_404(id)
    form = AtributoForm(obj=atributo)
    
    if form.validate_on_submit():
        try:
            atributo.nombre = form.nombre.data
            atributo.descripcion = form.descripcion.data
            atributo.tipo = form.tipo.data
            atributo.es_multiple = form.es_multiple.data
            atributo.es_obligatorio = form.es_obligatorio.data
            atributo.orden = form.orden.data or 0
            
            db.session.commit()
            flash('Atributo actualizado exitosamente', 'success')
            return redirect(url_for('atributos.get_atributos'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    return render_template('atributos/update.html', form=form, atributo=atributo)


@atributos_bp.route('/delete/<int:id>', methods=['POST'])
def delete_atributo(id):
    """Cambiar estado del atributo (soft delete)"""
    try:
        atributo = AtributoProducto.query.get_or_404(id)
        atributo.estado = 0 if atributo.estado else 1
        db.session.commit()
        
        mensaje = "Atributo restaurado" if atributo.estado else "Atributo eliminado"
        flash(mensaje, 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar la solicitud', 'danger')
    
    return redirect(url_for('atributos.get_atributos'))


# ==========================================
# CRUD DE VALORES DE ATRIBUTO
# ==========================================

@atributos_bp.route('/<int:atributo_id>/valores')
def get_valores(atributo_id):
    """Lista valores de un atributo específico"""
    atributo = AtributoProducto.query.get_or_404(atributo_id)
    valores = ValorAtributo.query.filter_by(atributo_id=atributo_id).order_by(ValorAtributo.orden).all()
    return render_template('atributos/valores.html', atributo=atributo, valores=valores)


@atributos_bp.route('/<int:atributo_id>/valores/add', methods=['GET', 'POST'])
def create_valor(atributo_id):
    """Crear nuevo valor para un atributo"""
    atributo = AtributoProducto.query.get_or_404(atributo_id)
    form = ValorAtributoForm()
    
    if form.validate_on_submit():
        try:
            valor = ValorAtributo(
                atributo_id=atributo_id,
                valor=form.valor.data,
                descripcion=form.descripcion.data,
                precio_adicional=form.precio_adicional.data or 0,
                disponible=form.disponible.data,
                orden=form.orden.data or 0
            )
            db.session.add(valor)
            db.session.commit()
            flash('Valor creado exitosamente', 'success')
            return redirect(url_for('atributos.get_valores', atributo_id=atributo_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear valor: {str(e)}', 'danger')
    
    return render_template('atributos/valor_add.html', form=form, atributo=atributo)


@atributos_bp.route('/<int:atributo_id>/valores/update/<int:valor_id>', methods=['GET', 'POST'])
def update_valor(atributo_id, valor_id):
    """Actualizar valor existente"""
    atributo = AtributoProducto.query.get_or_404(atributo_id)
    valor = ValorAtributo.query.get_or_404(valor_id)
    form = ValorAtributoForm(obj=valor)
    
    if form.validate_on_submit():
        try:
            valor.valor = form.valor.data
            valor.descripcion = form.descripcion.data
            valor.precio_adicional = form.precio_adicional.data or 0
            valor.disponible = form.disponible.data
            valor.orden = form.orden.data or 0
            
            db.session.commit()
            flash('Valor actualizado exitosamente', 'success')
            return redirect(url_for('atributos.get_valores', atributo_id=atributo_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar: {str(e)}', 'danger')
    
    return render_template('atributos/valor_update.html', form=form, atributo=atributo, valor=valor)


@atributos_bp.route('/<int:atributo_id>/valores/delete/<int:valor_id>', methods=['POST'])
def delete_valor(atributo_id, valor_id):
    """Cambiar estado del valor (soft delete)"""
    try:
        valor = ValorAtributo.query.get_or_404(valor_id)
        valor.estado = 0 if valor.estado else 1
        db.session.commit()
        
        mensaje = "Valor restaurado" if valor.estado else "Valor eliminado"
        flash(mensaje, 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar la solicitud', 'danger')
    
    return redirect(url_for('atributos.get_valores', atributo_id=atributo_id))


# ==========================================
# API ENDPOINTS PARA AJAX
# ==========================================

@atributos_bp.route('/api/producto/<int:producto_id>/extras')
def api_get_extras_producto(producto_id):
    """API: Obtiene los extras disponibles para un producto"""
    from src.models.Producto_model import Producto
    
    producto = Producto.query.get_or_404(producto_id)
    extras = producto.get_extras()
    
    return jsonify({
        'producto_id': producto_id,
        'tiene_extras': len(extras) > 0,
        'extras': extras
    })


@atributos_bp.route('/api/atributos/activos')
def api_get_atributos_activos():
    """API: Obtiene todos los atributos activos"""
    atributos = AtributoProducto.query.filter_by(estado=1).order_by(AtributoProducto.orden).all()
    return jsonify([a.to_dict() for a in atributos])
