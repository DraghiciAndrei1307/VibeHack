"""
    This module will use:
    - personal web UI X
    - Ngrok / Cloudflare Tunnel (cloudflared)
    for creating a gateway to the localhost
    - Ollama to pull different models X
    - Private VM
    - Docker compose
"""
import os

import requests
from ollama import generate, chat

from flask import Flask, request, jsonify, Response, render_template, flash, redirect, url_for, g
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy import Integer, String, Text, Float, Boolean, ForeignKey, create_engine, text
from sqlalchemy import event
import ollama

from forms import LoginForm, RegisterForm, ChatForm
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = "some_private_key"
ckeditor = CKEditor(app)
Bootstrap(app)

# Configure Flask-Login

login_manager = LoginManager()
login_manager.init_app(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///database.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create the sqlalchemy engine

engine = create_engine(
    "sqlite:///database.db",
    connect_args={"check_same_thread": False}, # this allows multiple threads
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(bind=engine)

def get_db():
    if 'db' not in g:
        g.db = SessionLocal()
    return g.db

@app.teardown_appcontext
def close_db(error):
    database = g.pop('db', None)
    if database is not None:
        database.close()

# with engine.connect() as connection:
#     connection.execute(text("PRAGMA journal_mode=WAL;"))

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

# CREATE the models used for tables creation

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name: Mapped[str] = mapped_column(db.String, nullable=False)
    email: Mapped[str] = mapped_column(db.String, nullable=False)
    password: Mapped[str] = mapped_column(db.String, nullable=False)

    chats = relationship("Chat", back_populates="user")
    messages = relationship("Message", back_populates="user")

class Chat(Base):
    __tablename__ = 'chat'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    messages = relationship("Message", back_populates="chat")

    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'))
    user = relationship("User", back_populates="chats")

# one chat can have multiple messages

class Message(Base):
    __tablename__ = 'message'

    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)

    content: Mapped[Text] = mapped_column(db.Text, nullable=False)
    role: Mapped[int] = mapped_column(db.Integer, nullable=False)

    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'))
    user = relationship("User", back_populates="messages")

    chat_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('chat.id'))
    chat = relationship("Chat", back_populates="messages")

# with app.app_context():
#     db.create_all()

with app.app_context():
    Base.metadata.create_all(engine)

# Create user_loader callback

@login_manager.user_loader
def load_user(user_id):
    db_session = get_db()
    return db_session.execute(db.select(User).where(User.id == user_id)).scalar()

@app.route('/login', methods=['GET', 'POST'])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        email = form.email.data
        password = form.password.data

        db_session = get_db()

        selected_user = db_session.execute(db.select(User).where(User.email == email)).scalar()

        if not selected_user:
            flash('Email incorrect.', 'danger')
            return redirect(url_for('login'))
        else:
            if not check_password_hash(selected_user.password, password):
                flash('Invalid password.', 'danger')
                return redirect(url_for('login'))
            else:
                login_user(selected_user)
                return redirect(url_for('new_chat'))

    return render_template('login.html', form=form, logged_in=current_user.is_authenticated)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():

    form = RegisterForm()

    if form.validate_on_submit():
        salted_password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8)

        db_session = get_db()

        user = db_session.execute(db.select(User).where(User.email == form.email.data)).scalar()

        if user:
            flash('This email address is already in use.', 'danger')
            return render_template('login.html', form=form)

        new_user = User(
            name=form.name.data,
            email=form.email.data,
            password= salted_password,
        )

        db_session.add(new_user)
        db_session.commit()

        return redirect(url_for('login'))

    return render_template('register.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/', methods=['GET', 'POST'])
def home():
    logged_in = current_user.is_authenticated
    return render_template('index.html', logged_in=logged_in)

@app.route("/new-chat", methods=["GET", "POST"])
@login_required
def new_chat():

    # Create a new chat (has no messages)

    the_new_chat = Chat(
        user_id=current_user.id,
    )

    db_session = get_db()

    db_session.add(the_new_chat)
    db_session.commit()

    # Get all the chats recorded

    chats = db_session.execute(db.select(Chat)).scalars()

    # Create a ChatForm to get the messages from current user

    form = ChatForm()

    if form.validate_on_submit():
        system_prompt = "You speak and sound like Jack Sparrow. Answer with short sentences."

        # Create and add the new message to the database
        user_content = form.message.data
        user_message = Message(
            content=user_content,
            role='user',
            chat_id = the_new_chat.id, # the new message is linked to the newly created chat
            user_id = the_new_chat.user_id, # the user who created the message
        )

        db_session.add(user_message)
        db_session.commit()

        # Use the newly created message to get the response from the model

        response = ollama.chat(
            model="gemma3",
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content},
            ]
        )

        model_message = Message(
            content=response.message.content,
            role='system',
            chat_id = the_new_chat.id,
            user_id = the_new_chat.user_id, # the response is saved in the account of the user
        )

        db_session.add(model_message)
        db_session.commit()

        return redirect(url_for('chat', chat_id=the_new_chat.id, chats=chats))

    return render_template('chat.html', chat_id=the_new_chat.id, chats = chats, form=form)

@app.route("/chat/<int:chat_id>", methods=["GET", "POST"])
@login_required
def chat(chat_id):

    db_session = get_db()

    selected_chat = db_session.execute(db.select(Chat).where(Chat.id == chat_id)).scalar()

    messages = db_session.execute(db.select(Message).where(Message.chat_id == chat_id)).scalars()

    # Get all the chats recorded

    chats = db_session.execute(db.select(Chat)).scalars()

    # Create a ChatForm to get the messages from current user

    form = ChatForm()

    if form.validate_on_submit():
        system_prompt = "You speak and sound like Jack Sparrow. Answer with short sentences."

        # Create and add the new message to the database
        user_content = form.message.data
        user_message = Message(
            content=user_content,
            role='user',
            chat_id=selected_chat.id,  # the new message is linked to the newly created chat
            user_id=selected_chat.user_id,  # the user who created the message
        )

        db_session.add(user_message)
        db_session.commit()

        # Use the newly created message to get the response from the model

        response = ollama.chat(
            model="gemma3",
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_content},
            ]
        )

        model_message = Message(
            content=response.message.content,
            role = 'system',
            chat_id=selected_chat.id,
            user_id=selected_chat.user_id,  # the response is saved in the account of the user
        )

        db_session.add(model_message)
        db_session.commit()

        return redirect(url_for('chat', chat_id=chat_id, chats=chats))

    return render_template(
        'chat.html',
        flag=True,
        form = form,
        chat_id=chat_id,
        messages=messages,
        chats=chats,
        selected_chat=selected_chat
    )


if __name__ == "__main__":
    app.run(host = '0.0.0.0', port=5001, debug=True)
