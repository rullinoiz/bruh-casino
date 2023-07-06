from discord.ext.commands import Context, check, Converter
import modules.exceptions as e
from modules.user_sqlite import user
from typing import *


def is_developer(action:str=None):
    def predicate(ctx:Context) -> bool:
        if not ctx.author.id == 441422344851030046:
            raise e.AccessDenied(ctx.invoked_with if not action else action)
        return True
    return check(predicate)

def under_construction():
    def predicate(ctx:Context) -> bool:
        if not ctx.author.id == 441422344851030046:
            raise e.UnderConstruction()
        return True
    return check(predicate)

class Money(Converter):
    async def convert(self, ctx:Context, arg:int) -> int:
        if user.read(ctx.author.id, 'money') < int(arg):
            raise e.BrokeError(int(arg), user.read(ctx.author.id, 'money'))
        elif int(arg) < 0:
            raise e.Uhhhhhh()
        return int(arg)
