from flask import Blueprint,  render_template, redirect, url_for, flash, request
from src.models.Cliente_model import Cliente
from src.models.Persona_model import Persona
from src.models.Documento_model import Documento
from utils.db import db
from forms import ClienteForm

clientes_bp = Blueprint('clientes', __name__, url_prefix="/clientes")

@clientes_bp.route("/")
def get_clientes():
    clientes = Cliente.query.all()
    return render_template("clientes/clientes.html", clientes=clientes)


@clientes_bp.route("/add", methods=["GET", "POST"])
def create_cliente():
    form = ClienteForm()

    form.documento_id.choices = [(doc.id, doc.tipo_documento) for doc in Documento.query.all()]
    
    if request.method == "POST":
        if form.validate_on_submit():
            clienteID = Cliente.query.join(Persona).filter(Persona.numero_documento == form.numero_documento.data).first()
            if clienteID is None:
                try:
                    # Primero crear la persona
                    persona = Persona(
                        razon_social=form.razon_social.data,
                        direccion=form.direccion.data,
                        telefono=form.telefono.data,
                        tipo_persona=form.tipo_persona.data,
                        documento_id=form.documento_id.data,
                        numero_documento=form.numero_documento.data
                    )
                    db.session.add(persona)
                    db.session.flush()  # Obtener el ID de la persona

                    # Luego crear el cliente
                    cliente = Cliente(
                        persona_id=persona.id
                    )
                    db.session.add(cliente)
                    db.session.commit()
                    
                    flash("Cliente creado exitosamente", "success")
                    return redirect(url_for("clientes.get_clientes"))
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error al crear el cliente: {str(e)}", "danger")
            else:
                flash("El cliente ya existe", "warning")
        else:
            flash("Por favor corrige los errores en el formulario.", "danger")

    return render_template("clientes/agregar_cliente.html", form=form)


@clientes_bp.route("/update/<int:cliente_id>", methods=["GET", "POST"])
def update_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    persona = Persona.query.get_or_404(cliente.persona_id)
    form = ClienteForm(obj=persona)

    form.documento_id.choices = [(doc.id, doc.tipo_documento) for doc in Documento.query.all()]
    

    if request.method == "POST":
        if form.validate_on_submit():
            try:
                persona.razon_social = form.razon_social.data
                persona.direccion = form.direccion.data
                persona.telefono = form.telefono.data
                persona.tipo_persona = form.tipo_persona.data
                persona.documento_id = form.documento_id.data
                persona.numero_documento = form.numero_documento.data

                db.session.commit()
                flash("Cliente actualizado exitosamente", "success")
                return redirect(url_for("clientes.get_clientes"))
            except Exception as e:
                db.session.rollback()
                flash(f"Error al actualizar el cliente: {str(e)}", "danger")
        else:
            flash("Por favor corrige los errores en el formulario.", "danger")

    return render_template("clientes/update_cliente.html", form=form, cliente=cliente)


@clientes_bp.route("/delete/<int:cliente_id>", methods=["POST"])
def delete_cliente(cliente_id):
    cliente = Cliente.query.get_or_404(cliente_id)
    try:
        # Cambiar el estado
        cliente.persona.estado = 0 if cliente.persona.estado else 1
        db.session.commit()

        mensaje = "Cliente restaurado" if cliente.persona.estado else "Cliente eliminado"
        flash(mensaje, 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar el cliente: {str(e)}", "danger")
    return redirect(url_for("clientes.get_clientes"))