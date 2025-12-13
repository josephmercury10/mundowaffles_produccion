from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField, DateField, FileField, SelectMultipleField, DecimalField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, length, ValidationError, NumberRange
from flask_wtf.file import FileAllowed
from src.models.repartidores_model import Repartidor
import re


#creamos las clases de cada formulario

class MarcaForm(FlaskForm):
    
    nombre = StringField('Nombre:', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción:', validators=[DataRequired()])
    submit = SubmitField('Guardar')
    
class CategoriaForm(FlaskForm):
    
    nombre = StringField('Nombre:', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción:', validators=[DataRequired()])
    submit = SubmitField('Guardar')
    
class PresentacionForm(FlaskForm):
    
    nombre = StringField('Nombre:', validators=[DataRequired()])
    descripcion = TextAreaField('Descripción:', validators=[DataRequired()])
    submit = SubmitField('Guardar')
    
class DeliveryForm(FlaskForm):
    cliente = StringField('Cliente*:', validators=[DataRequired()])
    telefono = StringField('Teléfono*:', validators=[DataRequired(), length(max=15)])
    direccion = StringField('Dirección*:', validators=[DataRequired(), length(max=100)])
    repartidor = SelectField('Repartidor:', choices=[], validators=[Optional()])
    tiempo_estimado = SelectField('Tiempo Estimado:', choices=[('', 'Seleccione...'), ('30 minutos', '30 minutos'), ('45 minutos', '45 minutos'), ('1 hora', '1 hora')], validators=[Optional()])
    comentarios = TextAreaField('Comentarios:', validators=[Optional(), length(max=200)])
    costo_envio = SelectField('Costo de Envío:', choices=[('1500', '$1.500'), ('2000', '$2.000'), ('2500', '$2.500')], validators=[DataRequired()])
    submit = SubmitField('Crear')
    

class MostradorForm(FlaskForm):
    cliente = StringField('Cliente:', validators=[Optional(), length(max=80)])
    comentarios = TextAreaField('Notas:', validators=[Optional(), length(max=200)])
    submit = SubmitField('Continuar')


class ReporteVentasForm(FlaskForm):
    rango = SelectField('Rango:', choices=[
        ('hoy', 'Hoy'),
        ('semana', 'Esta semana'),
        ('mes', 'Este mes'),
        ('historico', 'Histórico'),
        ('personalizado', 'Rango personalizado')
    ], default='hoy')
    fecha_desde = DateField('Desde:', format='%Y-%m-%d', validators=[Optional()])
    fecha_hasta = DateField('Hasta:', format='%Y-%m-%d', validators=[Optional()])
    metodo_pago = SelectField('Método de pago:', choices=[('', 'Todos')], validators=[Optional()])
    canal = SelectField('Canal:', choices=[('', 'Todos'), ('mostrador', 'Mostrador'), ('delivery', 'Delivery')], validators=[Optional()])
    estado = SelectField('Estado:', choices=[('', 'Todos'), ('1', 'Activo'), ('0', 'Inactivo')], validators=[Optional()])
    submit = SubmitField('Filtrar')
    
class ProductoForm(FlaskForm):
    codigo = StringField('Código:', validators=[DataRequired(), length(min=1, max=50)])
    nombre = StringField('Nombre:', validators=[DataRequired(message="El nombre es obligatorio."), length(min=1, max=80)])
    descripcion = TextAreaField('Descripción:', validators=[Optional(strip_whitespace=True), length(max=255)])
    precio = DecimalField('Precio:', validators=[DataRequired(message="El precio es obligatorio."), NumberRange(min=0.01, message="El precio debe ser mayor a 0")])
    fechaVencimiento = DateField('Fecha de Vencimiento:', format='%Y-%m-%d', validators=[Optional()])
    imagen = FileField('Imagen:', validators=[Optional(), FileAllowed(['jpg', 'png'], 'Solo se permiten imágenes JPG y PNG.')])
    marcas = SelectField('Marca:', choices=[], validators=[DataRequired()])
    presentaciones = SelectField('Presentación:', choices=[], validators=[DataRequired()])
    categorias = SelectMultipleField('Categorías:', choices=[], validators=[DataRequired("Seleccione al menos una categoría.")])
    atributos = SelectMultipleField('Extras/Atributos:', choices=[], validators=[Optional()])
    submit = SubmitField('Guardar')
    
    
class ClienteForm(FlaskForm):
    razon_social = StringField(validators=[DataRequired()])
    direccion = StringField('Dirección:', validators=[DataRequired()])
    telefono = StringField('Teléfono:', validators=[DataRequired(), length(min=8, max=20)])
    tipo_persona = SelectField('Tipo de Persona:', choices=[('Persona natural', 'Persona natural'), ('Persona Juridica', 'Persona Juridica')], validators=[DataRequired()])
    documento_id = SelectField('Tipo de Documento:', choices=[], validators=[DataRequired()])
    numero_documento = StringField('Número de Documento:', validators=[DataRequired(), length(min=1, max=10)])
    submit = SubmitField('Guardar')
    
    def validate_numero_documento(self, field):
        tipo_doc = self.documento_id.data
        numero = field.data 

        if tipo_doc == '1':
            # Validación de RUT chileno
            if not re.match(r'^\d{7,8}-[\dkK]$', numero):
                raise ValidationError('Formato de RUT inválido. Debe ser como: 12345678-9')
            
            # Validación del dígito verificador
            rut = numero.replace('-', '')
            dv = rut[-1].upper()
            rut = rut[:-1]
            
            # Calcular dígito verificador
            suma = 0
            multiplo = 2
            for r in reversed(rut):
                suma += int(r) * multiplo
                multiplo = multiplo + 1 if multiplo < 7 else 2
            
            dv_esperado = '0123456789K'[11 - (suma % 11)]
            
            if dv != str(dv_esperado):
                raise ValidationError('RUT inválido - dígito verificador incorrecto')
            
        elif tipo_doc == '2':
            # Validación de pasaporte
            if not re.match(r'^[A-Za-z0-9]{6,12}$', numero):
                raise ValidationError('El pasaporte debe tener entre 6 y 12 caracteres alfanuméricos')


# ==========================================
# FORMULARIOS DE ATRIBUTOS/EXTRAS
# ==========================================

class AtributoForm(FlaskForm):
    """Formulario para crear/editar atributos (grupos de extras)"""
    nombre = StringField('Nombre:', validators=[DataRequired(), length(min=1, max=100)])
    descripcion = TextAreaField('Descripción:', validators=[Optional(), length(max=255)])
    tipo = SelectField('Tipo:', choices=[
        ('extra', 'Extra (agregados opcionales)'),
        ('variante', 'Variante (ej: tamaño)'),
        ('opcion', 'Opción (selección única)')
    ], validators=[DataRequired()])
    es_multiple = BooleanField('Permite selección múltiple')
    es_obligatorio = BooleanField('Es obligatorio')
    orden = IntegerField('Orden:', validators=[Optional()], default=0)
    submit = SubmitField('Guardar')


class ValorAtributoForm(FlaskForm):
    """Formulario para crear/editar valores de atributos"""
    valor = StringField('Valor:', validators=[DataRequired(), length(min=1, max=100)])
    descripcion = TextAreaField('Descripción:', validators=[Optional(), length(max=255)])
    precio_adicional = DecimalField('Precio adicional:', validators=[Optional(), NumberRange(min=0)], default=0)
    disponible = BooleanField('Disponible', default=True)
    orden = IntegerField('Orden:', validators=[Optional()], default=0)
    submit = SubmitField('Guardar')