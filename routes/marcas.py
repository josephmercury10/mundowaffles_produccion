from flask import Blueprint,  render_template, redirect, url_for, flash, request
from src.models.Marca_model import Marca
from src.models.Caracteristica_model import Caracteristica
from utils.db import db
from forms import MarcaForm

marcas_bp = Blueprint('marcas', __name__ , url_prefix="/marcas") 



@marcas_bp.route("/")
def get_marcas():

    Marcas = Marca.query.all()
    return render_template("marcas/marcas.html", marcas = Marcas)


@marcas_bp.route("/add", methods=["GET", "POST"])

def create_marca():
        
    marcaForm = MarcaForm()
    #validamos el formulario:
    if marcaForm.validate_on_submit():
        marca = Caracteristica.query.filter_by(nombre=marcaForm.nombre.data).first()
        if marca is None:
            nueva_caracteristica = Caracteristica(nombre=marcaForm.nombre.data, descripcion=marcaForm.descripcion.data)
            try:
                # Guardamos la característica
                db.session.add(nueva_caracteristica)
                db.session.flush()  # Esto asigna el ID a nueva_caracteristica
            
                # Creamos la marca asociada
                nueva_marca = Marca(caracteristica_id=nueva_caracteristica.id)
            
                # Guardamos la marca
                db.session.add(nueva_marca)
                db.session.commit()
                
            
                return redirect(url_for('marcas.get_marcas')), flash('Marca creadas exitosamente', 'success')
            
            except Exception as e:
                db.session.rollback()
                print(f"Error: {str(e)}")
                
                return flash('Error al crear la marca', 'danger')
        else:
            flash('La marca ya existe', 'warning')

    return render_template("marcas/marcas_add.html", form = marcaForm)


@marcas_bp.route("/update/<int:id>", methods=["GET", "POST"])
def update_marca(id):
    form = MarcaForm()
    marca_to_update = Marca.query.get_or_404(id)
    caracteristica_to_update = marca_to_update.caracteristica
    
    if request.method == "GET":
        # Prellenamos el formulario con los datos actuales
        form.nombre.data = marca_to_update.caracteristica.nombre
        form.descripcion.data = marca_to_update.caracteristica.descripcion
        return render_template("marcas/marca_update.html", form=form)
    
    
    if request.method == "POST":
        try:
            # Actualizamos los datos de la característica
            caracteristica_to_update.nombre = form.nombre.data
            caracteristica_to_update.descripcion = form.descripcion.data
        
            # Guardamos los cambios
            db.session.commit()
            return redirect(url_for('marcas.get_marcas'))
        
        except Exception as e:
            db.session.rollback()
            print(f"Error: {str(e)}")
            flash('Error al actualizar la marca', 'danger')
            return redirect(url_for('marcas.update_marca', id=id))
        
    else:
         return render_template("marcas/marca_update.html")
     

@marcas_bp.route("/delete/<int:id>", methods=["POST"])
def delete_marca(id):
    try:
        marca = Marca.query.get_or_404(id)
        caracteristica = marca.caracteristica
        
        # Cambiar el estado
        caracteristica.estado = 0 if caracteristica.estado else 1
        db.session.commit()
        
        mensaje = "Marca restaurada" if caracteristica.estado else "Marca eliminada"
        flash(mensaje, 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar la solicitud', 'danger')
        
    return redirect(url_for('marcas.get_marcas'))