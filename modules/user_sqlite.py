import sqlite3 as sq
#from bot_config import bot_config
from discord import Member
from typing import Union,Any,Iterable

class user:
    s = sq.connect(r'user.db')
    c = s.cursor()

    @classmethod
    def ensure_existence(cls, userid:Union[int, Member], add_new:bool=False) -> bool:
        userid:int = userid if type(userid) != Member else userid.id
        if cls.c.execute('select id from user where id = ?;',(userid,)).fetchone() is None:
            if add_new:
                user.c.execute('insert into user(id) values(?);',(userid,))
                user.s.commit()
            return False
        return True

    @classmethod
    def write(cls, userid:Union[int, Member], stat:str, content:Any) -> None:
        userid:int = userid if type(userid) != Member else userid.id
        t = cls.ensure_existence(userid, True)
        cls.c.execute(f'update user set {stat} = ? where id = ?;',(content,userid))
        cls.s.commit()

    @classmethod
    def read(cls, userid:Union[int, Member], stat:str) -> int:
        userid: int = userid if type(userid) != Member else userid.id
        t = cls.ensure_existence(userid, True)
        return cls.c.execute(f'select {stat} from user where id = ?;',(userid,)).fetchone()[0]

    @classmethod
    def add(cls, userid:Union[int, Member], stat:Union[str, Iterable[str]], value:Union[int, Iterable[int]]) -> None:
        userid:int = userid if type(userid) != Member else userid.id
        t = cls.ensure_existence(userid, True)
        if type(stat) is str:
            cls.c.execute(f'update user set {stat} = {stat} {("+" if value > 0 else "-")} ? where id = ?;', (abs(value), userid))
            cls.s.commit()
        elif type(stat) is tuple:
            if len(stat) != len(value): raise ValueError('stat and variable are of different length')
            command = f'update user set {", ".join(stat[x] + " = " + stat[x] + (" + " if value[x] > 0 else " - ") + str(value[x]) for x in range(0,len(stat)))} where id = {userid}'
            cls.c.execute(command)
            cls.s.commit()

    @classmethod
    def subtract(cls, userid:Union[int, Member], stat:str, value:int) -> None:
        userid: int = userid if type(userid) != Member else userid.id
        t = cls.ensure_existence(userid, True)
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
