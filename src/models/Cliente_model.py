from datetime import datetime
from decimal import Decimal
from utils.db import db


class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    persona_id = db.Column(db.BigInteger, db.ForeignKey('personas.id'), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



    def to_dict(self):
        return {
            'id': self.id,
            'persona_id': self.persona_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }