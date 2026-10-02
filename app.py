from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'clave_secreta_restaurante'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

usuarios_db = {
    "admin": User("1", "admin", "123456")
}

@login_manager.user_loader
def load_user(user_id):
    for u in usuarios_db.values():
        if u.id == user_id:
            return u
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in usuarios_db and usuarios_db[username].password == password:
            login_user(usuarios_db[username])
            return redirect(url_for('index'))
        flash('Usuario o contraseña incorrectos')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Memoria temporal para órdenes y ventas mensuales estilo Inzag
ventas_db = []

@app.route('/api/guardar-pedido', methods=['POST'])
@login_required
def guardar_pedido():
    data = request.json
    ventas_db.append(data)
    return jsonify({"exito": True, "mensaje": "Pedido registrado correctamente"})

@app.route('/api/reporte-mes', methods=['GET'])
@login_required
def reporte_mes():
    total_recaudado = sum(item.get('total', 0) for item in ventas_db)
    total_pedidos = len(ventas_db)
    return jsonify({
        "total_recaudado": total_recaudado,
        "total_pedidos": total_pedidos,
        "ventas": ventas_db
    })

if __name__ == '__main__':
    app.run(debug=True)
