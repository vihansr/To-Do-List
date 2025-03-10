from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SECRET_KEY'] = SECRET_KEY

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(255), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def index():
    if not current_user.is_authenticated:
        return render_template("index.html")  # Show guest homepage
    tasks = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template("index.html", todos=tasks)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"], method='pbkdf2:sha256')
        if User.query.filter_by(username=username).first():
            return "Username already exists!"
        new_user = User(username=username,
                        password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        task = request.form["task"]
        new_task = Todo(task=task, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for("index"))
    return render_template("add_task.html")

@app.route("/task_done/<int:task_id>")
@login_required
def task_done(task_id):
    task = Todo.query.get(task_id)
    task.completed = True
    db.session.commit()
    return redirect(url_for("index"))

@app.route("/clear_tasks")
@login_required
def clear_tasks():
    Todo.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
