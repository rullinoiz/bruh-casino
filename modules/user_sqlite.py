import sqlite3 as sq

from discord.abc import User
from discord import Member
from typing import Union, Any, Sequence

from bot_config import bot_config as bcfg

class user(object):
    s: sq.Connection = sq.connect(bcfg.get("datapath"))
    c: sq.Cursor = s.cursor()

    @classmethod
    def ensure_existence(cls, userid:Union[int, User, Member], add_new:bool=False) -> bool:
        userid: int = userid if type(userid) is int else userid.id
        if cls.c.execute('select id from user where id = ?;',(userid,)).fetchone() is None:
            if add_new:
                cls.c.execute('insert into user(id) values(?);',(userid,))
                cls.s.commit()
            return False
        return True

    @classmethod
    def write(cls, userid:Union[int, User, Member], stat:str, content:Any) -> None:
        userid:int = getattr(userid, 'id', userid)
        cls.ensure_existence(userid, True)
        cls.c.execute(f'update user set {stat} = ? where id = ?;',(content,userid))
        cls.s.commit()

    @classmethod
    def write_from_stat(cls, stat, content: Any) -> None:
        return cls.write(stat.id, stat.stat, content)

    @classmethod
    def read(cls, userid: Union[int, User, Member], stat: Union[str, Sequence[str]]) -> int:
        userid: int = getattr(userid, 'id', userid)
        cls.ensure_existence(userid, True)
        if type(y := stat) is tuple: stat = ','.join(stat)
        t = cls.c.execute(f'select {stat} from user where id = ?;',(userid,))
        x = t.fetchone()
        return x[0] if type(y) is not tuple else x

    @classmethod
    def read_from_stat(cls, stat) -> int:
        return cls.read(stat.id, stat.stat)

    @classmethod
    def add(cls, userid:Union[int, User, Member], stat:Union[str, Sequence[str]], value:Union[int, Sequence[int]]) -> None:
        userid:int = getattr(userid, 'id', userid)
        cls.ensure_existence(userid, True)
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
        userid: int = getattr(userid, 'id', userid)
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
