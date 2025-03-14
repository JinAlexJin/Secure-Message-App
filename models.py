'''
models
defines sql alchemy data models
also contains the definition for the room class used to keep track of socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison

or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, composite, mapped_column
from typing import Dict

# data models
class Base(DeclarativeBase):
    pass

# model to store user information
class User(Base):
    __tablename__ = "user"
    
    # looks complicated but basically means
    # I want a username column of type string,
    # and I want this column to be my primary key
    # then accessing john.username -> will give me some data of type string
    # in other words we've mapped the username Python object property to an SQL column of type String 
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    mute: Mapped[str] = mapped_column(String)

########################################################################    
class Friend(Base):
    __tablename__ = "friend"

    username_1: Mapped[str] = mapped_column(String, primary_key=True)
    username_2: Mapped[str] = mapped_column(String, primary_key=True)

class FriendReq(Base):
    __tablename__ = "friend_req"

    from_user: Mapped[str] = mapped_column(String, primary_key=True)
    to_user: Mapped[str] = mapped_column(String, primary_key=True)

class History(Base):
    __tablename__ = "history"

    username_1: Mapped[str] = mapped_column(String, primary_key=True)
    username_2: Mapped[str] = mapped_column(String, primary_key=True)
    index: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(String)

class GroupHistory(Base):
    __tablename__ = "group_history"

    group_name: Mapped[str] = mapped_column(String, primary_key=True)
    index: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(String)

class GroupMembers(Base):
    __tablename__ = "group_members"

    group_name: Mapped[str] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, primary_key=True)

class Post(Base):
    __tablename__ = "Post"

    username: Mapped[str] = mapped_column(String, primary_key=True)
    index: Mapped[int] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, primary_key=True)
    body: Mapped[str] = mapped_column(String, primary_key=True)
    anonymous: Mapped[str] = mapped_column(String)

class Comment(Base):
    __tablename__ = "Comment"

    post_index: Mapped[int] = mapped_column(String, primary_key=True)
    comment_index: Mapped[int] = mapped_column(String, primary_key=True)
    username: Mapped[str] = mapped_column(String, primary_key=True)
    comment: Mapped[str] = mapped_column(String, primary_key=True)




########################################################################    

# stateful counter used to generate the room id
class Counter():
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

# Room class, used to keep track of which username is in which room
class Room():
    def __init__(self):
        self.counter = Counter()
        # dictionary that maps the username to the room id
        # for example self.dict["John"] -> gives you the room id of 
        # the room where John is in
        self.dict: Dict[str, int] = {}

    def create_room(self, sender: str, receiver: str) -> int:
        room_id = self.counter.get()
        self.dict[sender] = room_id
        self.dict[receiver] = room_id
        return room_id
    
    def join_room(self,  sender: str, room_id: int) -> int:
        self.dict[sender] = room_id

    def leave_room(self, user):
        if user not in self.dict.keys():
            return
        del self.dict[user]

    # gets the room id from a user
    def get_room_id(self, user: str):
        if user not in self.dict.keys():
            return None
        return self.dict[user]
    
