from flask import Blueprint,  render_template, redirect, url_for, flash, request
from utils.db import db


pos_bp = Blueprint('pos', __name__ , url_prefix='/pos')

@pos_bp.route("/")
def delivery():
    
    return render_template("pos/delivery.html")
