from datetime import datetime

from utils.db import db


class Printer(db.Model):
    __tablename__ = 'printers'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)  # Nombre amigable en la app
    driver_name = db.Column(db.String(150), nullable=False)  # Nombre del dispositivo en Windows
    tipo = db.Column(db.Text, nullable=False)  # JSON array: ["ticket","comanda","factura","cocina"]
    perfil = db.Column(db.Text, nullable=False)  # JSON array: ["general","delivery","mostrador","cocina"]
    ancho_caracteres = db.Column(db.SmallInteger, nullable=False, default=42)
    cortar_papel = db.Column(db.Boolean, nullable=False, default=True)
    feed_lines = db.Column(db.SmallInteger, nullable=False, default=3)
    printhost_url = db.Column(db.String(200), nullable=True)  # URL/IP pública del PrintHost del cliente
    estado = db.Column(db.SmallInteger, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self) -> str:
        return f"<Printer {self.id} {self.nombre} ({self.driver_name})>"
