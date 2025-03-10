
'''
app.py contains all of the server application
this is where you'll find all of the get/post request handlers
the socket event handlers are inside of socket_routes.py
'''

from flask import Flask, render_template, request, abort, url_for, session, redirect
from flask_socketio import SocketIO
import db
import secrets
import eventlet
from eventlet import wsgi
import bcrypt
import base64

# import logging

# this turns off Flask Logging, uncomment this to turn off Logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

app = Flask(__name__)

# secret key used to sign the session cookie
app.config['SECRET_KEY'] = secrets.token_hex()
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)
socketio = SocketIO(app)

# don't remove this!!
import socket_routes

# index page
@app.route("/")
def index():
    return render_template("index.jinja")

# login page
@app.route("/login")
def login():    
    return render_template("login.jinja")

# handles a post request when the user clicks the log in button
@app.route("/login/user", methods=["POST"])
def login_user():
    if not request.is_json:
        abort(404)

    username = request.json.get("username")
    password = request.json.get("password")

    user =  db.get_user(username)
    if user is None:
        return "Error: User does not exist!"

    if not bcrypt.checkpw(bytes(password, "utf-8"), base64.b64decode(user.password)):
        return "Error: Password does not match!"

    session["user"] = username

    return url_for('home', username=request.json.get("username"))

# handles a get request to the signup page
@app.route("/signup")
def signup():
    return render_template("signup.jinja")

# handles a post request when the user clicks the signup button
@app.route("/signup/user", methods=["POST"])
def signup_user():
    if not request.is_json:
        abort(404)
    username = request.json.get("username")
    password = request.json.get("password")

    hash = base64.b64encode(bcrypt.hashpw(bytes(password, "utf-8"), bcrypt.gensalt()))

    if db.get_user(username) is None:
        db.insert_user(username, hash)
        return url_for('home', username=username)
    return "Error: User already exists!"

# handler when a "404" error happens
@app.errorhandler(404)
def page_not_found(_):
    return render_template('404.jinja'), 404

# home page, where the messaging app is
@app.route("/home")
def home():
    if request.args.get("username") is None:
        abort(404)
    username = request.args.get("username")
    friends = db.get_friend(username)
    reqs = db.get_friend_req(username)
    reqs_out = db.get_friend_req_out(username)
    gc = db.get_groups(username)
    role = db.get_role(username)
    mute = db.get_mute(username)
    return render_template(
        "home.jinja",
        username=request.args.get("username"),
        friends=friends,
        reqs=reqs,
        reqs_out=reqs_out,
        group_chats=gc,
        role=role,
        mute=mute
    )

@app.route("/forum/<username>")
def forum(username):
    posts = db.get_posts()
    role = db.get_role(username)
    mute = db.get_mute(username)
    return render_template(
        "forum.jinja",
        username=username,
        posts=posts,
        role=role,
        mute=mute
    )

@app.route('/settings')
def settings():
    return render_template('setting.jinja')





if __name__ == '__main__':
    ssl_args = {
        "certfile": "./certs/localhost.crt",
        "keyfile": "./certs/localhost.key",
    }

    listener = eventlet.listen(("localhost", 5000))

    ssl_listener = eventlet.wrap_ssl(listener, **ssl_args, server_side=True)
    wsgi.server(ssl_listener, app)
