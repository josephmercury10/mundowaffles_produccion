from utils.db import db
from app import app
from src.models.Printer_model import Printer
import json

with app.app_context():
    # Crear una impresora real con printhost_url
    nueva_impresora = Printer(
        nombre="Impresora Test con URL",
        driver_name="EPSON TM-T88V Receipt5",
        printhost_url="http://192.168.1.100:8765",
        tipo=json.dumps(["ticket"]),
        perfil=json.dumps(["general"]),
        ancho_caracteres=42,
        cortar_papel=True,
        feed_lines=3,
        estado=1
    )
    
    db.session.add(nueva_impresora)
    db.session.commit()
    
    print(f"✅ Impresora creada con ID: {nueva_impresora.id}")
    print(f"   Nombre: {nueva_impresora.nombre}")
    print(f"   Driver: {nueva_impresora.driver_name}")
    print(f"   PrintHost URL: {nueva_impresora.printhost_url}")
    
    # Verificar que se guardó
    impresora_guardada = Printer.query.get(nueva_impresora.id)
    print(f"\n✅ Verificación desde BD:")
    print(f"   PrintHost URL: {impresora_guardada.printhost_url}")
