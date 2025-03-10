'''
socket_routes
file containing all the routes related to socket.io
'''
# Used for Diffie-Hellman Key Exchange
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from flask_socketio import join_room, emit, leave_room
from flask import request

try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room

import db

room = Room()
########################################################################################################

@socketio.on("mute_user")
def mute_user(username):
    db.mute_user(username)

@socketio.on("unmute_user")
def unmute_user(username):
    db.unmute_user(username)

@socketio.on("change_role")
def change_role(username, role):
    db.change_role(username, role)

@socketio.on("display_comments")
def display_comments(post_index):
    comments = db.get_comments(post_index)
    for comment in comments:
        emit("load_comment", {"role": comment["role"], "username": comment["username"], "comment": comment["comment"], "post_index": post_index, "comment_index": comment["comment_index"]})

@socketio.on("create_post")
def create_post(username, title, body, ano):
    if ano:
        db.add_post(username, title, body, "true")
    else:
        db.add_post(username, title, body, "false")

@socketio.on("create_comment")
def create_comment(post_index, comment, username):
    db.add_comment(post_index, comment, username)

@socketio.on("update_post")
def update_post(username, title, body, index):
    db.update_post(username, title, body, index)

@socketio.on("delete_comment")
def delete_comment(post_index, comment_index):
    db.delete_comment(post_index, comment_index)

@socketio.on("delete_post")
def delete_post(index):
    db.delete_post(index)


########################################################################################################

@socketio.on("accept_req")
def accept_req(current_username, sender_username):
    db.insert_friend(current_username, sender_username)
    emit("reload")

@socketio.on("reject_req")
def reject_req(current_username, sender_username):
    db.reject_friend_req(current_username, sender_username)

# join room event handler
# sent when the user joins a room
@socketio.on("send_req")
def send_req(sender_name, receiver_name):
    return db.insert_friend_req(sender_name, receiver_name)


online = []

# when the client connects to a socket
# this event is emitted when the io() function is called in JS
@socketio.on('connect')
def connect():
    username = request.cookies.get("username")
    online.append(username)
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    # socket automatically leaves a room on client disconnect
    # so on client connect, the room needs to be rejoined
    join_room(int(room_id))
    emit("incoming", (f"{username} has connected", "green"), to=int(room_id))

# event when client disconnects
# quite unreliable use sparingly
@socketio.on('disconnect')
def disconnect():
    username = request.cookies.get("username")
    online.remove(username)
    room_id = request.cookies.get("room_id")
    if room_id is None or username is None:
        return
    emit("incoming", (f"{username} has disconnected", "red"), to=int(room_id))

# send message event handler
@socketio.on("send")
def send(sender, receiver, message, room_id):
    db.add_history(sender, receiver, message)
    emit("incoming", ({"message": sender+": " + message, "sender": sender}), to=room_id)

@socketio.on("send_group")
def send_group(sender, group_name, message, room_id):
    db.add_group_history(group_name, sender + ": " + message)
    emit("incoming", ({"message": sender+": " + message, "sender": group_name}), to=room_id)

@socketio.on("add_to_group")
def add_to_group(username, group_name):
    members = db.get_group_members(group_name)
    for m in members:
        if m["name"] == username:
            return "User already in group!"
    users = db.get_all_users()
    is_user = False
    for m in users:
        if m["name"] == username:
            is_user = True
    if is_user is False:
        return "User does not exist"
    db.add_group_member(group_name, username)
    return 1
    
room_pem = {}
room_names = []

@socketio.on("get_req_in_list")
def get_req_in_list(username):
    dics = db.get_friend_req(username)
    #l = []
    #for i in dics:
    #    l.append(i["name"])
    return dics

@socketio.on("receive_key")
def receive_key(public_key, room_id):
    l = room_pem[room_id]
    if l == []:
        l.append(public_key)
        room_pem[room_id] = l
    else:
        l.append(public_key)
        room_pem[room_id] = l
        emit("key_exchange_second", public_key, to=room_id, include_self=False)

@socketio.on("get_friends")
def get_friends(username):
    out = []
    friends = db.get_friend(username)
    for f in friends:
        if f["name"] in online:
            out.append({"name": f["name"], "status": "online", "role": f["role"]})
        else:
            out.append({"name": f["name"], "status": "offline", "role": f["role"]})
    return out


@socketio.on("join_group")
def join_group(username, group_name):
    room_id = room.get_room_id(group_name)
    if room_id is not None:
        room.join_room(username, group_name)
        join_room(room_id)
        history = db.get_group_history(group_name)
        emit("incoming", ("------Joined Chat------", "green"))
        for m in history:
            emit("display_history", m)

        return room_id
    
    room_id = room.create_room(group_name, "group")
    join_room(room_id)

    room_pem[room_id] = []
    room_names.append(sorted([group_name, "group"]))

    history = db.get_group_history(group_name)
    emit("incoming", ("------Joined Chat------", "green"))
    for m in history:
        emit("display_history", m)

    return room_id

@socketio.on("join")
def join(sender_name, receiver_name):
    
    receiver = db.get_user(receiver_name)
    if receiver is None:
        return "Unknown receiver!"
    
    sender = db.get_user(sender_name)
    if sender is None:
        return "Unknown sender!"

    friends = db.get_friend(sender_name)
    friends_list = []
    for i in friends:
        friends_list.append(i["name"])
    if receiver_name not in friends_list: 
        return "Not friends!"

    room_id = room.get_room_id(receiver_name)

    # if the user is already inside of a room 
    if room_id is not None:
        
        room.join_room(sender_name, room_id)
        join_room(room_id)
        history = db.get_messages(sender_name, receiver_name)
        for m in history:
            emit("display_history", m)

        return room_id

    # if the user isn't inside of any room, 
    # perhaps this user has recently left a room
    # or is simply a new user looking to chat with someone
    room_id = room.create_room(sender_name, receiver_name)
    join_room(room_id)
    room_pem[room_id] = []
    room_names.append(sorted([sender_name, receiver_name]))

    history = db.get_messages(sender_name, receiver_name)
    for m in history:
        emit("display_history", m)

    return room_id
    room_pem[room_id] = []
    room_names.append(sorted([sender_name, receiver_name]))

    history = db.get_messages(sender_name, receiver_name)
    for m in history:
        emit("display_history", m)

    return room_id
    room_pem[room_id] = []
    room_names.append(sorted([sender_name, receiver_name]))

    history = db.get_messages(sender_name, receiver_name)
    for m in history:
        emit("display_history", m)

    return room_id
    room_pem[room_id] = []
    room_names.append(sorted([sender_name, receiver_name]))

    history = db.get_messages(sender_name, receiver_name)
    for m in history:
        emit("display_history", m)

    return room_id
    room_pem[room_id] = []
    room_names.append(sorted([sender_name, receiver_name]))

    history = db.get_messages(sender_name, receiver_name)
    for m in history:
        emit("display_history", m)

    return room_id

@socketio.on("remove")
def remove(username1, username2):
    db.remove(username1, username2)

# leave room event handler
@socketio.on("leave")
def leave(username, room_id):
    leave_room(room_id)
    room.leave_room(username)
