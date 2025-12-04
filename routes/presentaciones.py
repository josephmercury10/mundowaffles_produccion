from flask import Blueprint,  render_template, redirect, url_for, flash, request
from src.models.Presentacion_model import Presentacion
from src.models.Caracteristica_model import Caracteristica
from utils.db import db
from forms import PresentacionForm

presentaciones_bp = Blueprint('presentaciones', __name__ , url_prefix="/presentaciones")

@presentaciones_bp.route("/")
def get_presentaciones():

    Presentaciones = Presentacion.query.all()
    #for presentacion in Presentaciones:
     #   print(presentacion.id, presentacion.caracteristica_id, presentacion.caracteristica.nombre, presentacion.created_at, presentacion.updated_at,)
        
    return render_template("presentaciones/presentaciones.html", presentaciones = Presentaciones)

@presentaciones_bp.route("/add", methods=['GET', 'POST'])
def create_presentacion():
        form = PresentacionForm()
        if form.validate_on_submit():
            caracteristica = Caracteristica.query.get(form.caracteristica_id.data)
            presentacion = Presentacion(caracteristica_id=caracteristica.id)
            db.session.add(presentacion)
            db.session.commit()
            flash('Presentacion added successfully')
            return redirect(url_for('presentaciones.get_presentaciones'))
        return render_template('presentaciones/add_presentacion.html', form=form)

@presentaciones_bp.route("/update/<id>", methods=['GET', 'POST'])
def update_presentacion(id):
        presentacion = Presentacion.query.get(id)
        form = PresentacionForm(obj=presentacion)
        if form.validate_on_submit():
            caracteristica = Caracteristica.query.get(form.caracteristica_id.data)
            presentacion.caracteristica_id = caracteristica.id
            db.session.commit()
            flash('Presentacion updated successfully')
            return redirect(url_for('presentaciones.get_presentaciones'))
        return render_template('presentaciones/update_presentacion.html', form=form)

@presentaciones_bp.route("/delete/<id>")
def delete_presentacion(id):
        presentacion = Presentacion.query.get(id)
        db.session.delete(presentacion)
        db.session.commit()
        flash('Presentacion deleted successfully')
        return redirect(url_for('presentaciones.get_presentaciones'))
