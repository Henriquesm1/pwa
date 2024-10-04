from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)

# Configuração do MySQL e chaves
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Brinks%40123@localhost/pwa_banco'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

# Inicializa banco de dados e criptografia de senhas
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)

# Inicializa SocketIO
socketio = SocketIO(app)

# Modelo do usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'validador' ou 'acionador'

# Rota para a página inicial
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Rota para login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        usuario = Usuario.query.filter_by(email=email).first()
        if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
            session['user_id'] = usuario.id
            session['role'] = usuario.role
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Credenciais inválidas')
    return render_template('login.html')

# Rota para logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Rota do painel após login
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    role = session.get('role')
    if role == 'validador':
        return render_template('validador.html')
    else:
        return render_template('acionador.html')

# Função para lidar com mensagens enviadas no chat via WebSocket
@socketio.on('message')
def handle_message(data):
    # Envia a mensagem para todos os usuários conectados
    send(data, broadcast=True)

# Função principal de execução
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
