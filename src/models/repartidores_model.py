from datetime import datetime
from utils.db import db

class Repartidor(db.Model):
    __tablename__ = 'repartidores'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    id_persona = db.Column(db.BigInteger, db.ForeignKey('personas.id'), nullable=False)
    
    
    persona = db.relationship("Persona", backref="repartidor", uselist=False)