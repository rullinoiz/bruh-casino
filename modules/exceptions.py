from discord.ext.commands import CommandError, Command

class AccessDenied(CommandError):
    def __init__(self, action:str=None, codestyle:bool=False) -> None:
        self.action = action
        self.codestyle = codestyle
        super().__init__('You do not have sufficient permissions to {0}'.format('perform this action.' if not action else f'"{action}".'))

class ArgumentError(CommandError):
    def __init__(self, cmd:Command, codestyle:bool=False) -> None:
        self.command = cmd
        self.codestyle = codestyle

        super().__init__(f'Usage: `{cmd.name} ' + ' '.join([f'[{self.totype(k.annotation.__name__)}: {v}]' for v, k in cmd.clean_params.items()]) + '`')

    @staticmethod
    def totype(t: str) -> str:
        types = {
            'int': 'number',
            'str': 'string',
            'Money': 'number',
            'MoneyEven': 'even number'
        }
        return t if t not in types.keys() else types[t]

class ArgumentValueError(CommandError):
    def __init__(self, msg:str='Invalid value for argument') -> None:
        self.msg = msg
        super().__init__(msg)

class BrokeError(CommandError):
    def __init__(self, asked:int, has:int, codestyle:bool=False) -> None:
        self.asked = asked
        self.has = has
        self.codestyle = codestyle
        super().__init__(f'you are broke as shit (command supplied with {asked}, user has {has})')

class MultipleInstanceError(CommandError):
    def __init__(self, cmd:Command, codestyle:bool=False) -> None:
        self.command = cmd
        self.codestyle = codestyle
        super().__init__(f'Only 1 instance of a command can be running at a time! ({cmd.name})')

class RateError(CommandError):
    def __init__(self, msg:str='You have been rate limited! Try again later.', codestyle:bool=False) -> None:
        self.msg = msg 
        self.codestyle = codestyle
        super().__init__(msg)

class UnderConstruction(CommandError):
    def __init__(self, msg:str='not yet my dude', codestyle:bool=False) -> None:
        self.msg = msg
        self.codestyle = codestyle
        super().__init__(msg)

class Uhhhhhh(CommandError):
    def __init__(self, msg:str='errrm..., you cant do that', codestyle:bool=False) -> None:
        self.msg = msg
        self.codestyle = codestyle
        super().__init__(msg)

class TooMuchData(CommandError):
    def __init__(self, msg:str='Command received too much data, could not continue!', codestyle:bool=False) -> None:
        self.msg = msg
        self.codestyle = codestyle
        super().__init__(msg)

class CommandTimeoutError(CommandError):
    def __init__(self, time:int=20, codestyle:bool=False) -> None:
        self.time = time
        self.codestyle = codestyle
        super().__init__(f'Sorry, you failed to respond in {time} seconds so I gave up')