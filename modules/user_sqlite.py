import sqlite3 as sq

import discord.ext.commands
#from bot_config import bot_config
from discord.abc import User
from discord import Member
from typing import Union, Any, Iterable, overload

class user_instance: pass

class user:
    s: sq.Connection = sq.connect(r'user.db')
    c: sq.Cursor = s.cursor()

    @classmethod
    def ensure_existence(cls, userid:Union[int, User, Member, user_instance], add_new:bool=False) -> bool:
        userid:int = userid if type(userid) is int else userid.id
        if cls.c.execute('select id from user where id = ?;',(userid,)).fetchone() is None:
            if add_new:
                user.c.execute('insert into user(id) values(?);',(userid,))
                user.s.commit()
            return False
        return True

    @classmethod
    def write(cls, userid:Union[int, User, Member, user_instance], stat:str, content:Any) -> None:
        userid:int = userid if type(userid) is int else userid.id
        t = cls.ensure_existence(userid, True)
        cls.c.execute(f'update user set {stat} = ? where id = ?;',(content,userid))
        cls.s.commit()

    @classmethod
    def read(cls, userid:Union[int, User, Member, user_instance], stat:str) -> int:
        userid: int = userid if type(userid) is int else userid.id
        t = cls.ensure_existence(userid, True)
        return cls.c.execute(f'select {stat} from user where id = ?;',(userid,)).fetchone()[0]

    @classmethod
    def add(cls, userid:Union[int, User, Member, user_instance], stat:Union[str, Iterable[str]], value:Union[int, Iterable[int]]) -> None:
        userid:int = userid if type(userid) is int else userid.id
        t = cls.ensure_existence(userid, True)
        if type(stat) is str:
            cls.c.execute(f'update user set {stat} = {stat} {("+" if value > 0 else "-")} ? where id = ?;', (abs(value), userid))
            cls.s.commit()
        elif type(stat) is tuple:
            if len(stat) != len(value): raise ValueError('stat and value are of different length')
            command: str = f'update user set {", ".join(stat[x] + " = " + stat[x] + (" + " if value[x] > 0 else " - ") + str(value[x]) for x in range(0,len(stat)))} where id = {userid}'
            cls.c.execute(command)
            cls.s.commit()

    @classmethod
    def subtract(cls, userid:Union[int, User, Member, user_instance], stat:str, value:int) -> None:
        userid: int = userid if type(userid) is int else userid.id
        cls.ensure_existence(userid, True)
        cls.c.execute(f'update user set {stat} = {stat} - ? where id = ?', (abs(value), userid))
        cls.s.commit()

    # def massadd(userid:Union[int, Member], stat:tuple[str], value:tuple[int]) -> None:
    #     userid: int = userid if type(userid) != Member else userid.id
    #     user.ensure_existence(userid, True)
    #     user.c.execute(f'update user set {', '.join([f"{x} = {x} + "])} where id = {userid}')

    @staticmethod
    def has_role(member:Member, roleid:int) -> bool:
        for i in member.roles:
            if i.id == str(roleid):
                return True
        
        return False

class user_instance:
    @overload
    def __init__(self, user:Union[int, User]) -> None:
        self.id: int = user if type(user) != User else user.id

    def __init__(self, ctx:discord.ext.commands.Context) -> None:
        self.id: int = ctx.author.id

    def __getitem__(self, stat:str) -> int:
        return user.read(self, stat)

    def __setitem__(self, stat:str, value:str) -> None:
        return user.write(self, stat, value)

    def ensure_existence(self, add_new:bool=False) -> bool:
        return user.ensure_existence(self, add_new)

    def add(self, stat:Union[str, Iterable[str]], value:Union[int, Iterable[int]]) -> None:
        return user.add(self, stat, value)

    def read(self, stat:Union[str, Iterable[str]]) -> int:
        return user.read(self, stat)

    def won(self, amount:int) -> None:
        return user.add(self, ('money','moneygained','wins'), (amount,amount,1))

    def lost(self, amount:int) -> None:
        return user.add(self, ('money','moneylost','loss'), (-amount,amount,1))

    def subtract(self, stat:Union[str, Iterable[str]], value:Union[int, Iterable[int]]) -> None:
        return user.subtract(self, stat, value)
