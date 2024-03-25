import discord.ext.commands
from modules.user_sqlite import user
from modules.userstat import UserStat
from typing import Union, Sequence

class user_instance(object):
    __slots__ = ('id',)

    def __init__(self, ctx: Union[discord.ext.commands.Context, int]) -> None:
        self.id: int = ctx if isinstance(ctx, int) else ctx.author.id

    def __getitem__(self, stat: str) -> int:
        return user.read(self.id, stat)

    def __setitem__(self, stat:str, value: Union[int, str, float]) -> None:
        return user.write(self.id, stat, value)

    def __getattr__(self, attr:str) -> UserStat:
        return UserStat(self.id, attr)

    # def __setattr__(self, attr: str, value) -> None:
    #     if attr == 'id':
    #         super().__setattr__(attr, value)
    #         return
    #     return user.write(self.id, attr, value)

    def ensure_existence(self, add_new: bool=False) -> bool:
        return user.ensure_existence(self.id, add_new)

    def add(self, stat: Union[str, Sequence[str]], value: Union[int, Sequence[int]]) -> None:
        return user.add(self.id, stat, value)

    def read(self, stat: Union[str, Sequence[str]]) -> int:
        return user.read(self.id, stat)

    def write(self, stat: Union[str, Sequence[str]], value: Union[int, Sequence[int]]) -> None:
        user.write(self.id, stat, value)

    def won(self, amount: int) -> None:
        return user.add(self.id, ('money','moneygained','wins'), (amount,amount,1))

    def lost(self, amount: int) -> None:
        return user.add(self.id, ('money','moneylost','loss'), (-amount,amount,1))

    def subtract(self, stat:Union[str, Sequence[str]], value:Union[int, Sequence[int]]) -> None:
        return user.subtract(self.id, stat, value)
