import discord.ext.commands
from modules.user_sqlite import user
from modules.userstat import UserStat
from typing import Union, Iterable

class user_instance:
    def __init__(self, ctx:discord.ext.commands.Context) -> None:
        self.id: int = ctx.author.id

    def __getitem__(self, stat:str) -> int:
        return user.read(self, stat)

    def __setitem__(self, stat:str, value: Union[int, str, float]) -> None:
        return user.write(self, stat, value)

    def __getattr__(self, attr:str) -> UserStat:
        return UserStat(self.id, attr)

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