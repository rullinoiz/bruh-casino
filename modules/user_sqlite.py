import sqlite3 as sq
#from bot_config import bot_config
from discord import Member
from typing import Union

class user:
    s = sq.connect(r'user.db')
    c = s.cursor()

    def ensure_existence(userid:Union[int, Member], add_new:bool=False) -> bool:
        userid = userid if type(userid) != Member else userid.id
        if user.c.execute('select id from user where id = ?;',(userid,)).fetchone() == None:
            if add_new:
                user.c.execute('insert into user(id) values(?);',(userid,))
                user.s.commit()
            return False
        return True

    def write(userid:Union[int, Member], stat:str, content) -> None:
        userid = userid if type(userid) != Member else userid.id
        t = user.ensure_existence(userid, True)
        user.c.execute(f'update user set {stat} = ? where id = ?;',(content,userid))
        user.s.commit()

    def read(userid:Union[int, Member], stat:str) -> int:
        userid = userid if type(userid) != Member else userid.id
        t = user.ensure_existence(userid, True)
        return user.c.execute(f'select {stat} from user where id = ?;',(userid,)).fetchone()[0]

    def add(userid:Union[int, Member], stat:str, value:int) -> None:
        userid = userid if type(userid) != Member else userid.id
        t = user.ensure_existence(userid, True)
        user.c.execute(f'update user set {stat} = {stat} {("+" if value > 0 else "-")} ? where id = ?;',(abs(value),userid))
        user.s.commit()

    def has_role(member:Member, roleid:int) -> bool:
        for i in member.roles:
            if str(i.id) == str(roleid):
                return True
        
        return False
