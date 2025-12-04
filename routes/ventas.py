from flask import Blueprint,  render_template, redirect, url_for, flash, request
from utils.db import db

ventas_bp = Blueprint('ventas', __name__, url_prefix='/ventas')

@ventas_bp.route("/")
def index():
    return render_template("ventas/index.html")
