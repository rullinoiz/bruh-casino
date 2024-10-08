import math
import discord
from discord.app_commands import AppCommandError
from discord.ext.commands import Context, check, Converter, CommandError
import modules.exceptions as e
from modules.user import user
from modules.server import server

developer_id: int = 441422344851030046

def is_developer(action:str=None):
    def predicate(ctx: Context) -> bool:
        return is_developer_predicate(ctx, e.AccessDenied(action or ctx.invoked_with))
    return check(predicate)

def is_developer_slash_command(action:str=None):
    def predicate(ctx: discord.Interaction) -> bool:
        return is_developer_predicate(ctx, e.AccessDenied(action))
    return discord.app_commands.check(predicate)

def is_developer_predicate(ctx: Context | discord.Interaction | discord.Member | discord.User, raise_if: CommandError | AppCommandError = None) -> bool:
    if type(ctx) is Context:
        if not ctx.author.id == developer_id:
            if raise_if:
                raise raise_if
            return False
    elif type(ctx) in [discord.User, discord.Member]:
        if not ctx.id == developer_id:
            return False
    elif type(ctx) in [discord.Interaction]:
        if not ctx.user.id == developer_id:
            if raise_if:
                raise raise_if
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

def caller_has_money(money: int):
    def predicate(ctx: Context) -> bool:
        if (has := user.read(ctx.author.id, "money")) < money:
            raise e.BrokeError(money, has)
        ctx.caller_has_money = money
        return True
    return check(predicate)

class Money(Converter):
    async def convert(self, ctx: Context, arg: str) -> int:
        usermoney: int = user.read(ctx.author.id, 'money')
        try: int(arg)
        except ValueError:
            if type(arg) is str and (lower := arg.lower()):
                if 'all' in lower: return usermoney
                if 'half' in lower: return math.floor(usermoney / 2)
                raise e.ArgumentValueError('Money must be an integer, "half", or "all"!')
        if usermoney < int(arg):
            raise e.BrokeError(int(arg), user.read(ctx.author.id, 'money'))
        elif int(arg) <= 0:
            raise e.Uhhhhhh()
        return int(arg)

class MoneyEven(Money):
    async def convert(self, ctx: Context, arg: str) -> int:
        if (money := await super().convert(ctx, arg)) and (money % 2 == 0):
            return int(arg)
        else:
            raise e.ArgumentValueError(f'Argument for Money must be even! (received odd number {arg})')
