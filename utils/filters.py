import json

def format_price(value):
    """Formatea un número como precio sin decimales con separador de miles"""
    try:
        return "{:,.0f}".format(float(value)).replace(",", ".")
    except (ValueError, TypeError):
        return "0"

def from_json(value):
    """Parse JSON string to Python object"""
    try:
        if isinstance(value, str):
            return json.loads(value)
        return value
    except:
        return []

def register_filters(app):
    """Registra todos los filtros personalizados"""
    app.template_filter('format_price')(format_price)
    app.template_filter('from_json')(from_json)