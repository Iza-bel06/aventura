from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_restaurante'

# Configuración de la Base de Datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurante.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- MODELOS DE LA BASE DE DATOS ---
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

usuarios_db = {
    "admin": User("1", "admin", "123456")
}

class Mesa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    estado = db.Column(db.String(20), default='Libre') # Libre, Ocupado
    salon = db.Column(db.String(50), default='Salón Principal')

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    precio = db.Column(db.Float, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)

class Pedido(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mesa_id = db.Column(db.Integer, db.ForeignKey('mesa.id'), nullable=False)
    total = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(20), default='Pendiente') # Pendiente, Pagado

# Inicializar Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    for user in usuarios_db.values():
        if user.id == user_id:
            return user
    return None

# --- RUTAS DE LA APLICACIÓN Y DASHBOARD ---
@app.route('/')
@login_required
def index():
    total_ordenes = Pedido.query.filter_by(estado='Pendiente').count()
    mesas_activas = Mesa.query.filter_by(estado='Ocupado').count()
    recaudacion_total = db.session.query(db.func.sum(Pedido.total)).filter_by(estado='Pagado').scalar() or 0.0
    
    mesas = Mesa.query.all()
    productos = Producto.query.all()
    
    # Diccionario para consultar pedidos pendientes por mesa en la vista
    pedidos_activos = {p.mesa_id: p for p in Pedido.query.filter_by(estado='Pendiente').all()}
    
    return render_template('index.html', 
                           total_ordenes=total_ordenes,
                           mesas_activas=mesas_activas,
                           recaudacion_total=recaudacion_total,
                           mesas=mesas,
                           productos=productos,
                           pedidos_activos=pedidos_activos)

@app.route('/agregar-mesa', methods=['POST'])
@login_required
def agregar_mesa():
    numero = request.form.get('numero')
    salon = request.form.get('salon', 'Salón Principal')
    if numero:
        nueva_mesa = Mesa(numero=numero, salon=salon, estado='Libre')
        db.session.add(nueva_mesa)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/agregar-producto', methods=['POST'])
@login_required
def agregar_producto():
    nombre = request.form.get('nombre')
    precio = float(request.form.get('precio', 0))
    categoria = request.form.get('categoria', 'Platos')
    if nombre and precio > 0:
        nuevo_prod = Producto(nombre=nombre, precio=precio, categoria=categoria)
        db.session.add(nuevo_prod)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/crear-pedido/<int:mesa_id>', methods=['POST'])
@login_required
def crear_pedido(mesa_id):
    total = float(request.form.get('total', 0))
    if total > 0:
        # Crear la orden pendiente
        nuevo_pedido = Pedido(mesa_id=mesa_id, total=total, estado='Pendiente')
        db.session.add(nuevo_pedido)
        
        # Cambiar estado de la mesa a Ocupado
        mesa = Mesa.query.get(mesa_id)
        if mesa:
            mesa.estado = 'Ocupado'
            
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/pagar-pedido/<int:mesa_id>', methods=['POST'])
@login_required
def pagar_pedido(mesa_id):
    # Buscar el pedido pendiente de esta mesa
    pedido = Pedido.query.filter_by(mesa_id=mesa_id, estado='Pendiente').first()
    if pedido:
        pedido.estado = 'Pagado'
        
        # Liberar la mesa
        mesa = Mesa.query.get(mesa_id)
        if mesa:
            mesa.estado = 'Libre'
            
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = usuarios_db.get(username)
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
