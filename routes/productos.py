from flask import Blueprint,  render_template, redirect, url_for, flash, request
from src.models.Producto_model import Producto
from src.models.Producto_model import CategoriaProducto
from src.models.Caracteristica_model import Caracteristica
from src.models.Marca_model import Marca
from src.models.Presentacion_model import Presentacion
from src.models.Categoria_model import Categoria

from utils.db import db
from forms import ProductoForm

productos_bp = Blueprint('productos', __name__ , url_prefix='/productos')

@productos_bp.route('/')
def get_productos():
    
    productos = Producto.query.all()

    return render_template('productos/productos.html', productos=productos)


@productos_bp.route('/add', methods=['GET', 'POST'])
def create_producto():
    form = ProductoForm()
    form.marcas.choices = [(str(marca.id), marca.caracteristica.nombre) 
                          for marca in Marca.query
                          .join(Marca.caracteristica)
                          .filter(Caracteristica.estado == 1)
                          .all()]
    
    form.presentaciones.choices = [(str(p.id), p.caracteristica.nombre)
                                    for p in Presentacion.query
                                    .join(Presentacion.caracteristica)
                                    .filter(Caracteristica.estado == 1)
                                    .all()]
    
    form.categorias.choices = [(str(c.id), c.caracteristica.nombre)
                                for c in Categoria.query
                                .join(Categoria.caracteristica)
                                .filter(Caracteristica.estado == 1)
                                .all()]

    if request.method == 'POST':
        # Aquí iría la lógica para manejar el formulario y crear un nuevo producto
        if form.validate_on_submit():
            # Procesar y guardar el nuevo producto
            
            productoID = Producto.query.filter_by(codigo=form.codigo.data).first()
            if productoID is None:
                
                try:
                    nuevo_producto = Producto(
                        codigo=form.codigo.data,
                        nombre=form.nombre.data,
                        descripcion=form.descripcion.data,
                        precio=form.precio.data,
                        fecha_vencimiento=form.fechaVencimiento.data,
                        img_path=form.imagen.data.filename if form.imagen.data else None,
                        marca_id=form.marcas.data,
                        presentacione_id=form.presentaciones.data
                    )                        
                    db.session.add(nuevo_producto)
                    db.session.flush()

                    for categoria_id in form.categorias.data:
                        # Crear una nueva entrada en la tabla pivote
                        categoria_producto = CategoriaProducto(
                            producto_id=nuevo_producto.id,
                            categoria_id=int(categoria_id)
                        )
                        db.session.add(categoria_producto)
                        
                    db.session.commit()
                    flash('Producto creado exitosamente', 'success')
                    return redirect(url_for('productos.get_productos'))
                except Exception as e:
                    db.session.rollback()
                    print(f"Error: {str(e)}")

            return redirect(url_for('productos.get_productos'))
        else:
            print('Error en el formulario. Por favor, revisa los datos ingresados.')

    return render_template('productos/create.html', form=form)


@productos_bp.route('/update/<int:id>', methods=['GET', 'POST'])
def update_producto(id):
    producto = Producto.query.get_or_404(id)
    form = ProductoForm(obj=producto)

    form.marcas.choices = [(str(marca.id), marca.caracteristica.nombre)
                          for marca in Marca.query
                          .join(Marca.caracteristica)
                          .filter(Caracteristica.estado == 1)
                          .all()]

    form.presentaciones.choices = [(str(p.id), p.caracteristica.nombre)
                                    for p in Presentacion.query
                                    .join(Presentacion.caracteristica)
                                    .filter(Caracteristica.estado == 1)
                                    .all()]

    form.categorias.choices = [(str(c.id), c.caracteristica.nombre)
                                for c in Categoria.query
                                .join(Categoria.caracteristica)
                                .filter(Caracteristica.estado == 1)
                                .all()]
    
    # Establecer los valores seleccionados previamente
    if request.method == 'GET':
        form.marcas.data = str(producto.marca_id)
        form.presentaciones.data = str(producto.presentacione_id)
        
        # Obtener IDs de categorías existentes
        categorias_actuales = db.session.query(CategoriaProducto.categoria_id)\
            .filter(CategoriaProducto.producto_id == producto.id)\
            .all()
        form.categorias.data = [str(cat_id[0]) for cat_id in categorias_actuales]

    if request.method == 'POST':
        if form.validate_on_submit():
            producto.codigo = form.codigo.data
            producto.nombre = form.nombre.data
            producto.descripcion = form.descripcion.data
            producto.precio = form.precio.data
            producto.fecha_vencimiento = form.fechaVencimiento.data
            producto.img_path = form.imagen.data.filename if form.imagen.data else None
            producto.marca_id = form.marcas.data
            producto.presentacione_id = form.presentaciones.data

            # Actualizar las categorías
            # Eliminar las categorías existentes
            CategoriaProducto.query.filter_by(producto_id=producto.id).delete()
            
            # Agregar las nuevas categorías
            for categoria_id in form.categorias.data:
                categoria_producto = CategoriaProducto(
                    producto_id=producto.id,
                    categoria_id=int(categoria_id)
                )
                db.session.add(categoria_producto)

            db.session.commit()
            flash('Producto actualizado exitosamente', 'success')
            return redirect(url_for('productos.get_productos'))

    return render_template('productos/update.html', form=form, producto=producto)

@productos_bp.route('/delete/<int:id>', methods=['POST'])
def delete_producto(id):
    try:
        producto = Producto.query.get_or_404(id)

        # Cambiar el estado
        producto.estado = 0 if producto.estado else 1
        db.session.commit()

        mensaje = "Producto restaurado" if producto.estado else "Producto eliminado"
        flash(mensaje, 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar la solicitud', 'danger')

    return redirect(url_for('productos.get_productos'))
