from discord.ext.commands import Context, check, Converter
import modules.exceptions as e
from modules.user_sqlite import user
from typing import *
from modules.server import server

def is_developer(action:str=None):
    def predicate(ctx:Context) -> bool:
        if not ctx.author.id == 441422344851030046:
            raise e.AccessDenied(action or ctx.invoked_with)
        return True
    return check(predicate)

def under_construction():
    def predicate(ctx:Context) -> bool:
        if not ctx.author.id == 441422344851030046:
            raise e.UnderConstruction()
        return True
    return check(predicate)

def is_command_enabled(command:str=None):
    def predicate(ctx:Context) -> bool:
        if server.read(ctx.guild.id, f'enable_{command or ctx.command}'):
            return True
        raise e.CommandNotEnabled(command or ctx.context)
    return check(predicate)

class Money(Converter):
    async def convert(self, ctx:Context, arg:int) -> int:
        if user.read(ctx.author.id, 'money') < int(arg):
            raise e.BrokeError(int(arg), user.read(ctx.author.id, 'money'))
        elif int(arg) <= 0:
            raise e.Uhhhhhh()
        return int(arg)

class MoneyEven(Money):
    async def convert(self, ctx:Context, arg:int) -> int:
        if super.convert(ctx, arg) and (arg % 2 == 0):
            return arg
        else:
            raise e.ArgumentValueError(f'Argument for Money must be even! (received odd number {arg})')
