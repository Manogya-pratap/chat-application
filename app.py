from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.Column(db.String(50), nullable=False)
    receiver = db.Column(db.String(50), nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if username:
        join_room(username)
        User.query.filter_by(username=username).update(dict(online=True))
        db.session.commit()
        emit('update_status', {'username': username, 'status': 'online'}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username:
        User.query.filter_by(username=username).update(dict(online=False))
        db.session.commit()
        emit('update_status', {'username': username, 'status': 'offline'}, broadcast=True)

@socketio.on('send_message')
def handle_message(data):
    content = data['content']
    sender = data['sender']
    receiver = data['receiver']

    message = Message(content=content, sender=sender, receiver=receiver)
    db.session.add(message)
    db.session.commit()

    emit('receive_message', {'content': content, 'sender': sender, 'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}, room=receiver)

if __name__ == '__main__':
    db.create_all()
    socketio.run(app, debug=True)
