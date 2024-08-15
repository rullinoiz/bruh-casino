import sqlite3 as sq
from bot_config import bot_config as bcfg
from modules.user.user_sqlite import user
from modules.user.userstat import UserStat
from typing import Union, Sequence
from bc_common.static_init import static_init
from discord.ext.commands import Context
from discord import Interaction

@static_init
class user_instance(object):
    @classmethod
    def __static__(cls) -> None:
        c = sq.connect(bcfg.get("datapath")).cursor()
        cls.columns = [x[0] for x in c.execute("select name from pragma_table_info(\"user\");").fetchall()]
        cls.__slots__ = cls.columns + ["user"]
        c.close()

    def __init__(self, ctx: Interaction | Context | int) -> None:
        t = type(ctx)
        if t is Interaction:
            self.user: int = ctx.user.id
        elif t is Context:
            self.user: int = ctx.author.id
        elif t is int:
            self.user: int = ctx

    def __getitem__(self, stat: str) -> int:
        return user.read(super().__getattribute__("user"), stat)

    def __setitem__(self, stat:str, value: Union[int, str, float]) -> None:
        return user.write(super().__getattribute__("user"), stat, value)

    def __getattribute__(self, attr:str) -> UserStat:
        if attr in super().__getattribute__("columns"):
            return UserStat(super().__getattribute__("user"), attr)
        return super().__getattribute__(attr)

    def __setattr__(self, attr: Union[str, int], value) -> None:
        if value is None: return
        if attr in super().__getattribute__("columns"):
            user.write(super().__getattribute__("user"), attr, value)
            return
        super().__setattr__(attr, value)

    def ensure_existence(self, add_new: bool=False) -> bool:
        return user.ensure_existence(super().__getattribute__("user"), add_new)

    def add(self, stat: Union[str, Sequence[str]], value: Union[int, Sequence[int]]) -> None:
        return user.add(super().__getattribute__("user"), stat, value)

    def read(self, stat: Union[str, Sequence[str]]) -> int:
        return user.read(super().__getattribute__("user"), stat)

    def write(self, stat: Union[str, Sequence[str]], value: Union[int, Sequence[int]]) -> None:
        user.write(super().__getattribute__("user"), stat, value)

    def won(self, amount: int) -> None:
        return user.add(super().__getattribute__("user"), ('money','moneygained','wins'), (amount,amount,1))

    def lost(self, amount: int) -> None:
        return user.add(super().__getattribute__("user"), ('money','moneylost','loss'), (-amount,amount,1))

    def subtract(self, stat:Union[str, Sequence[str]], value:Union[int, Sequence[int]]) -> None:
        return user.subtract(super().__getattribute__("user"), stat, value)
