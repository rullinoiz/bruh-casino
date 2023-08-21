import discord
from discord.ext.commands import Context, check, Converter, CommandError
import modules.exceptions as e
from modules.user_sqlite import user
from typing import *
from modules.server import server

developer_id: int = 441422344851030046

def is_developer(action:str=None):
    def predicate(ctx:Context) -> bool:
        return is_developer_predicate(ctx, e.AccessDenied(action or ctx.invoked_with))
    return check(predicate)

def is_developer_predicate(ctx: Union[Context, discord.User], raise_if: CommandError = None) -> bool:
    if type(ctx) is Context:
        if not ctx.author.id == developer_id:
            if raise_if:
                raise raise_if
            return False
    elif type(ctx) in [discord.User, discord.Member]:
        if not ctx.id == developer_id:
            return False
    return True

def under_construction():
    return check(
        lambda ctx: is_developer_predicate(ctx, raise_if=e.UnderConstruction())
    )

def is_command_enabled(command:str=None):
    def predicate(ctx:Context) -> bool:
        if server.read(ctx.guild.id, f'enable_{command or ctx.command}'):
            return True
        raise e.CommandNotEnabled(command or ctx.context)
    return check(predicate)

class Money(Converter[int]):
    async def convert(self, ctx: Context, arg: str) -> int:
        if user.read(ctx.author.id, 'money') < int(arg):
            raise e.BrokeError(int(arg), user.read(ctx.author.id, 'money'))
        elif int(arg) <= 0:
            raise e.Uhhhhhh()
        return int(arg)

class MoneyEven(Money):
    async def convert(self, ctx: Context, arg: str) -> int:
        if super().convert(ctx, arg) and (arg % 2 == 0):
            return int(arg)
        else:
            raise e.ArgumentValueError(f'Argument for Money must be even! (received odd number {arg})')
