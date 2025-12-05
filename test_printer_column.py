from utils.db import db
from app import app
from src.models.Printer_model import Printer

with app.app_context():
    # Verificar columnas
    columnas = [c.name for c in Printer.__table__.columns]
    print("Columnas del modelo Printer:")
    for col in columnas:
        print(f"  - {col}")
    
    # Verificar si printhost_url está presente
    if 'printhost_url' in columnas:
        print("\n✅ La columna 'printhost_url' está presente en el modelo")
    else:
        print("\n❌ La columna 'printhost_url' NO está presente en el modelo")
    
    # Intentar crear una impresora de prueba
    try:
        test_printer = Printer(
            nombre="Test",
            driver_name="Test Driver",
            printhost_url="http://test:8765",
            tipo='["ticket"]',
            perfil='["general"]',
        )
        db.session.add(test_printer)
        db.session.flush()
        
        print(f"\n✅ Impresora de prueba creada con printhost_url='{test_printer.printhost_url}'")
        
        db.session.rollback()
    except Exception as e:
        print(f"\n❌ Error al crear impresora de prueba: {e}")
        db.session.rollback()
