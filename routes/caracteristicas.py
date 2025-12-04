from flask import Blueprint,  render_template
from src.models.Caracteristica_model import Caracteristica
from utils.db import db

caracteristicas_bp = Blueprint('caracteristicas', __name__, url_prefix="/caracteristicas")

@caracteristicas_bp.route("/")
def get_caracteristicas():
    Caracteristicas = Caracteristica.query.all()
    # print(Caracteristicas)
    
    return render_template("caracteristicas/caracteristicas.html", caracteristicas=Caracteristicas)

@caracteristicas_bp.route("/update/<int:id>")
def update_caracteristica(id):
    caracteristica = Caracteristica.query.get(id)
    if caracteristica:
        caracteristica.estado = 0 if caracteristica.estado == 1 else 1
        db.session.commit()
    return "Característica actualizada"