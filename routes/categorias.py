from flask import Blueprint,  render_template, redirect, url_for, flash, request
from src.models.Categoria_model import Categoria
from src.models.Caracteristica_model import Caracteristica
from utils.db import db
from forms import CategoriaForm

categorias_bp = Blueprint('categorias', __name__ , url_prefix="/categorias")

@categorias_bp.route("/")
def get_categorias():
    
    Categorias = Categoria.query.all()
    for categoria in Categorias:
        print(categoria.id, categoria.caracteristica_id, categoria.caracteristica.nombre, categoria.created_at, categoria.updated_at,)
    return render_template("categorias/categorias.html", categorias = Categorias)

@categorias_bp.route("/add", methods=["GET", "POST"])
def create_categoria():
    categoriaForm = CategoriaForm()
    #validamos el formulario:
    if categoriaForm.validate_on_submit():
        categoria = Caracteristica.query.filter_by(nombre=categoriaForm.nombre.data).first()
        if categoria is None:
            nueva_caracteristica = Caracteristica(nombre=categoriaForm.nombre.data, descripcion=categoriaForm.descripcion.data)
            try:
                # Guardamos la característica
                db.session.add(nueva_caracteristica)
                db.session.flush()  # Esto asigna el ID a nueva_caracteristica
            
                # Creamos la categoria asociada
                nueva_categoria = Categoria(caracteristica_id=nueva_caracteristica.id)
            
                # Guardamos la categoria
                db.session.add(nueva_categoria)
                db.session.commit()
                
            
                return redirect(url_for('categorias.get_categorias')), flash('Categoria creada exitosamente', 'success')
            
            except Exception as e:
                db.session.rollback()
                print(f"Error: {str(e)}")
                
                return flash('Error al crear la categoria', 'danger')
        else:
            flash('La categoria ya existe', 'warning')
    
    
    return render_template("categorias/add.html", form = categoriaForm)

@categorias_bp.route("/update/<int:id>", methods=["GET", "POST"])
def update_categoria(id):
    form = CategoriaForm()
    categoria_to_update = Categoria.query.get_or_404(id)
    caracteristica_to_update = categoria_to_update.caracteristica
    
    if request.method == "GET":
        form.nombre.data = caracteristica_to_update.nombre
        form.descripcion.data = caracteristica_to_update.descripcion
        return render_template("categorias/update.html", form=form)

    if request.method == "POST":
        if form.validate_on_submit():
            try:
                caracteristica_to_update.nombre = form.nombre.data
                caracteristica_to_update.descripcion = form.descripcion.data
                db.session.commit()
                return redirect(url_for('categorias.get_categorias')), flash('Categoria actualizada exitosamente', 'success')
            except Exception as e:
                db.session.rollback()
                print(f"Error: {str(e)}")
                return flash('Error al actualizar la categoria', 'danger')  
        

@categorias_bp.route("/delete/<int:id>", methods=["POST"])
def delete_categoria(id):
    try:
        categoria = Categoria.query.get_or_404(id)
        caracteristica = categoria.caracteristica
        
        caracteristica.estado = 0 if caracteristica.estado else 1
        db.session.commit()
        
        mensaje = "categoria restaurada" if caracteristica.estado else "Categoria eliminada"
        flash(mensaje, 'success')
    except:
        db.session.rollback()
        flash('Error al procesar la solicitud', 'danger')
        
    return redirect(url_for('categorias.get_categorias'))

