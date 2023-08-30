import sqlite3 as sq

from discord.abc import User
from discord import Member
from typing import Union, Any, Iterable

class user:
    s: sq.Connection = sq.connect(r'user.db')
    c: sq.Cursor = s.cursor()

    @classmethod
    def ensure_existence(cls, userid:int, add_new:bool=False) -> bool:
        if cls.c.execute('select id from user where id = ?;',(userid,)).fetchone() is None:
            if add_new:
                cls.c.execute('insert into user(id) values(?);',(userid,))
                cls.s.commit()
            return False
        return True

    @classmethod
    def write(cls, userid:Union[int, User, Member], stat:str, content:Any) -> None:
        userid:int = userid if type(userid) is int else userid.id
        t = cls.ensure_existence(userid, True)
        cls.c.execute(f'update user set {stat} = ? where id = ?;',(content,userid))
        cls.s.commit()

    @classmethod
    def write_from_stat(cls, stat, content: Any) -> None:
        cls.write(stat.id, stat.stat, content)

    @classmethod
    def read(cls, userid:Union[int, User, Member], stat:Union[str, Iterable[str]]) -> int:
        userid: int = userid if type(userid) is int else userid.id
        t = cls.ensure_existence(userid, True)
        if type(stat) == tuple: stat = ','.join(stat)
        return cls.c.execute(f'select {stat} from user where id = ?;',(userid,)).fetchone()[0]

    @classmethod
    def read_from_stat(cls, stat) -> int:
        return cls.read(stat.id, stat.stat)

    @classmethod
    def add(cls, userid:Union[int, User, Member], stat:Union[str, Iterable[str]], value:Union[int, Iterable[int]]) -> None:
        userid:int = userid if type(userid) is int else userid.id
        t = cls.ensure_existence(userid, True)
        if type(stat) is str:
            cls.c.execute(f'update user set {stat} = {stat} {("+" if value > 0 else "-")} ? where id = ?;', (abs(value), userid))
            cls.s.commit()
        elif type(stat) is tuple:
            if len(stat) != len(value): raise ValueError('stat and value are of different length')
            command: str = f'update user set {", ".join(stat[x] + " = " + stat[x] + (" + " if value[x] > 0 else " - ") + str(abs(value[x])) for x in range(0,len(stat)))} where id = {userid}'
            cls.c.execute(command)
            cls.s.commit()

    @classmethod
    def add_from_stat(cls, stat, val: int) -> None:
        cls.add(stat.id, stat.stat, val)

    @classmethod
    def subtract(cls, userid:Union[int, User, Member], stat:str, value:int) -> None:
        userid: int = userid if type(userid) is int else userid.id
        cls.ensure_existence(userid, True)
        cls.c.execute(f'update user set {stat} = {stat} - ? where id = ?', (abs(value), userid))
        cls.s.commit()

    @classmethod
    def subtract_from_stat(cls, stat, val: int) -> None:
        cls.subtract(stat.id, stat.stat, val)


    @staticmethod
    def has_role(member:Member, roleid:int) -> bool:
        for i in member.roles:
            if i.id == str(roleid):
                return True
        
        return False
