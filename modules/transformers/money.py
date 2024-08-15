import math
from discord import Interaction
from discord.app_commands.transformers import Transformer
from modules.user import user
from modules.exceptions import ArgumentValueError, BrokeError, Uhhhhhh

class Money(Transformer):
    last_cache: dict[int, int] = dict()

    # noinspection PyUnboundLocalVariable
    async def transform(self, ctx: Interaction, value: str, /) -> int:
        usermoney: int = user.read(ctx.user.id, 'money')
        try:
            int(value)
        except ValueError:
            if type(value) is str and (lower := value.lower()):
                if 'all' in lower:
                    self.last_cache[ctx.user.id] = (result := usermoney)
                elif 'half' in lower:
                    self.last_cache[ctx.user.id] = (result := math.floor(usermoney / 2))
                elif "last" in lower:
                    self.last_cache[ctx.user.id] = (result := self.last_cache.get(ctx.user.id, 50))
                else:
                    raise ArgumentValueError('Money must be an integer, "half", or "all"!')
                return result
        if usermoney < int(value):
            raise BrokeError(int(value), usermoney)
        elif int(value) <= 0:
            raise Uhhhhhh()

        return int(value)

# class MoneyEven(Money):
#     async def transform(self, ctx: Interaction, value: str, /) -> int:
#
