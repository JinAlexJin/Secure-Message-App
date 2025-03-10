'''
db
database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine, select, or_, and_, update
from sqlalchemy.orm import Session
from models import *

from pathlib import Path

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# change it if you wish
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)

# initializes the database
Base.metadata.create_all(engine)

def change_role(username, role):
    with Session(engine) as session:
        stmt = (
            update(User)
            .where(User.username == username)
            .values(role=str(role))
        )
        session.execute(stmt)
        session.commit()

def unmute_user(username):
    with Session(engine) as session:
        stmt = (
            update(User)
            .where(User.username == username)
            .values(mute="false")
        )
        session.execute(stmt)
        session.commit()

def mute_user(username):
    with Session(engine) as session:
        stmt = (
            update(User)
            .where(User.username == username)
            .values(mute="true")
        )
        session.execute(stmt)
        session.commit()

def delete_comment(post_index, comment_index):
    with Session(engine) as session:
        session.query(Comment).filter(Comment.post_index == post_index, Comment.comment_index == comment_index).delete()
        session.commit()

def update_post(username, title, body, index):
    with Session(engine) as session:
        session.query(Post).filter(Post.index == index).delete()
        m = Post(
            username=username, index=index, body=body, title=title
        )
        session.add(m)
        session.commit()


def add_comment(post_index, comment, username):
    with Session(engine) as session:
        result = session.execute(select(Comment).where(Comment.post_index == post_index))
        index = 0
        first = next(result,None)
        if first is not None:
            index = 1
            for row in result:
                for i in row:
                    if i.comment_index > index:
                        index = i.comment_index
        index += 1
        m = Comment(
            username=username, post_index=post_index, comment_index=index, comment=comment
        )
        session.add(m)
        session.commit()

def add_post(username, title, body, ano):
    with Session(engine) as session:
        result = session.execute(select(Post))
        index = 0
        first = next(result,None)
        if first is not None:
            index = 1
            for row in result:
                for i in row:
                    if i.index > index:
                        index = i.index
        index += 1
        m = Post(
            username=username, index=index, body=body, title=title, anonymous=ano
        )
        session.add(m)
        session.commit()

def get_posts():
    with Session(engine) as session:
        result = session.execute(select(Post))
        out = []
        first = next(result, None)
        if first is not None:
            for i in first:
                role = get_role(i.username)
                if i.anonymous == "true":
                    out.append({"role": role, "username": "anonymous", "index": i.index, "title": i.title, "body": i.body})
                else:
                    out.append({"role": role, "username": i.username, "index": i.index, "title": i.title, "body": i.body})

            for row in result:
                for i in row:
                    role = get_role(i.username)
                    if i.anonymous == "true":
                        out.append({"role": role, "username": "anonymous", "index": i.index, "title": i.title, "body": i.body})
                    else:
                        out.append({"role": role, "username": i.username, "index": i.index, "title": i.title, "body": i.body})
        a = sorted(out, key=lambda a: a["index"], reverse=True)
        return a

def get_comments(post_index):
    with Session(engine) as session:
        result = session.execute(select(Comment).where(Comment.post_index==post_index))
        out = []
        first = next(result, None)
        if first is not None:
            for i in first:
                role = get_role(i.username)
                out.append({"role": role, "username": i.username, "comment": i.comment, "comment_index": i.comment_index})
            for row in result:
                for i in row:
                    role = get_role(i.username)
                    out.append({"role": role, "username": i.username, "comment": i.comment, "comment_index": i.comment_index})
        a = sorted(out, key=lambda a: a["comment_index"])
        return a


def add_group_member(group_name, username):
    with Session(engine) as session:
        group = GroupMembers(group_name=group_name, username=username)
        session.add(group)
        session.commit()

def add_group_history(group_name, message):
    with Session(engine) as session:
        result = session.execute(
            select(GroupHistory).where(GroupHistory.group_name == group_name)
        )
        index = 0
        first = next(result,None)
        if first is not None:
            index = 1
            for row in result:
                for i in row:
                    if i.index > index:
                        index = i.index
        index += 1
        m = GroupHistory(
            group_name=group_name, index=index, message=message
        )
        session.add(m)
        session.commit()

def get_group_history(group_name):
    with Session(engine) as session:
        result = session.execute(
            select(GroupHistory).where(
                GroupHistory.group_name == group_name
            )
        )
        out = []
        first = next(result, None)
        if first is not None:
            for i in first:
                out.append([i.index, i.message])
            for row in result:
                for i in row:
                    out.append([i.index, i.message])
        a = sorted(out, key=lambda a: a[0])
        b = []
        for i in a:
            b.append(i[1])
        return b

def get_groups(username):
    with Session(engine) as session:
        result = session.execute(
            select(GroupMembers).where(
                GroupMembers.username == username
            )
        )
        group_list = []
        for row in result:
            for group in row:
                group_list.append({"name": group.group_name})

        return group_list

def get_group_members(group_name):
    with Session(engine) as session:
        result = session.execute(
            select(GroupMembers).where(
                GroupMembers.group_name == group_name
            )
        )
        member_list = []
        for row in result:
            for member in row:
                member_list.append({"name": member.username})

        return member_list



def get_all_users():
    with Session(engine) as session:
        result = session.execute(select(User))
        member_list = []
        for row in result:
            for member in row:
                member_list.append({"name": member.username})

        return member_list






# inserts a user to the database
def insert_user(username: str, password: str):
    with Session(engine) as session:
        user = User(username=username, password=password, role="student", mute="false")
        session.add(user)
        session.commit()

# gets a user from the database
def get_user(username: str):
    with Session(engine) as session:
        return session.get(User, username)


##################################################################
def add_history(sender, receiver, message):
    with Session(engine) as session:
        result = session.execute(
            select(History).where(
                or_(
                    and_(
                        History.username_1 == sender,
                        History.username_2 == receiver
                    ),
                    and_(
                        History.username_2 == sender,
                        History.username_1 == receiver
                    )
                )
            )
        )
        index = 0
        first = next(result,None)
        if first is not None:
            index = 1
            for row in result:
                for i in row:
                    if i.index > index:
                        index = i.index
        index += 1
        m = History(username_1=sender, username_2=receiver,
                    index=index, message=message)
        session.add(m)
        session.commit()

def get_messages(sender, receiver):
    with Session(engine) as session:
        result = session.execute(
            select(History).where(
                or_(
                    and_(
                        History.username_1 == sender,
                        History.username_2 == receiver
                    ),
                    and_(
                        History.username_2 == sender,
                        History.username_1 == receiver
                    )
                )
            )
        )
        out = []
        first = next(result, None)
        n_outs = 0
        if first is not None:
            for i in first:
                out.append([i.index, (i.username_1 + ": " + i.message)])
            for row in result:
                for i in row:
                    out.append([i.index, (i.username_1 + ": " + i.message)])
        a = sorted(out, key=lambda a: a[0])
        b = []
        for i in a:
            b.append(i[1])
        return b

def delete_post(index):
    with Session(engine) as session:
        session.query(Post).filter(Post.index == index).delete()
        session.commit()


def remove(username1, username2):
    with Session(engine) as session:
        session.query(Friend).filter(Friend.username_1 == username1, Friend.username_2 == username2).delete()
        session.query(Friend).filter(Friend.username_1 == username2, Friend.username_2 == username1).delete()
        session.commit()


def reject_friend_req(current_username: str, sender_username: str):
    with Session(engine) as session:
        session.query(FriendReq).filter(FriendReq.from_user == sender_username, FriendReq.to_user == current_username).delete()
        session.commit()

def insert_friend(current_username: str, sender_username: str):
    with Session(engine) as session:
        session.query(FriendReq).filter(FriendReq.from_user == sender_username, FriendReq.to_user == current_username).delete()
        session.commit()
        friend = Friend(username_1=current_username, username_2=sender_username)
        session.add(friend)
        session.commit()


def get_friend(username: str) -> dict:
    with Session(engine) as session:
        result = session.execute(
            select(Friend).where(
                or_(
                    Friend.username_1 == username,
                    Friend.username_2 == username
                )
            )
        )
        friends_list = []
        for row in result:
            for friend in row:
                friend_name = ""
                if friend.username_1 == username:
                    friend_name = friend.username_2
                else:
                    friend_name = friend.username_1
                role = get_role(friend_name)
                friends_list.append({"name": friend_name, "role": role})

        return friends_list

def insert_friend_req(from_user: str, to_user: str):
    with Session(engine) as session:
        if from_user == to_user:
            return "Cannot add yourself!"
        has_user = session.execute(
            select(User).where(
                User.username == to_user
            )
        )
        if has_user.first() is None:
            return "User does not exist!"
        is_friend = session.execute(
            select(Friend).where(
                or_(
                    and_(
                        Friend.username_1 == from_user,
                        Friend.username_2 == to_user
                    ),
                    and_(
                        Friend.username_1 == to_user,
                        Friend.username_2 == from_user
                    )
                )
            )
        )
        if is_friend.first() is not None:
            return "Already friend!"

        req_sent = session.execute(
            select(FriendReq).where(
                FriendReq.from_user == from_user, FriendReq.to_user == to_user
            )
        )
        if req_sent.first() is not None:
            return "Request already sent!"

        req_sent = session.execute(
            select(FriendReq).where(
                FriendReq.from_user == to_user, FriendReq.to_user == from_user
            )
        )
        if req_sent.first() is not None:
            return "Request already received!"

        friend = FriendReq(from_user=from_user, to_user=to_user)
        session.add(friend)
        session.commit()
        return 1

def get_mute(username):
    with Session(engine) as session:
        result = session.execute(select(User).where(User.username == username))
        for row in result:
            for req in row:
                return req.mute

def get_role(username):
    with Session(engine) as session:
        result = session.execute(select(User).where(User.username == username))
        for row in result:
            for req in row:
                return req.role

def get_friend_req(username: str):
    with Session(engine) as session:
        result = session.execute(
            select(FriendReq).where(
                    FriendReq.to_user == username
            )
        )
        req_list = []
        for row in result:
            for req in row:
                req_list.append({"name": req.from_user})
        return req_list

def get_friend_req_out(username: str):
    with Session(engine) as session:
        result = session.execute(
            select(FriendReq).where(
                    FriendReq.from_user == username
            )
        )
        req_list = []
        for row in result:
            for req in row:
                req_list.append({"name": req.to_user})
        return req_list


##################################################################
