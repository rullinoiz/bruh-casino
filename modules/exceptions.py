from discord.ext.commands import CommandError, Command
from discord import Message
from modules.BruhCasinoError import BruhCasinoError, EditableBruhCasinoError

class AccessDenied(BruhCasinoError):
    def __init__(self, action:str=None) -> None:
        self.action = action
        super().__init__('You do not have sufficient permissions to {0}'.format('perform this action.' if not action else f'"{action}".'))

class ArgumentError(BruhCasinoError):
    def __init__(self, cmd: Command) -> None:
        self.command = cmd
        super().__init__(f'Usage: `{cmd.name} ' + ' '.join([f'[{self.totype(k.annotation.__name__)}: {v}]' for v, k in cmd.clean_params.items()]) + '`')

    @staticmethod
    def totype(t: str) -> str:
        types = {
            'int': 'number',
            'str': 'string',
            'Money': 'number',
            'MoneyEven': 'even number'
        }
        return types.get(t, t)

class ArgumentValueError(BruhCasinoError):
    def __init__(self, msg:str='Invalid value for argument') -> None:
        super().__init__(msg)

class BrokeError(BruhCasinoError):
    def __init__(self, asked:int, has:int) -> None:
        self.asked = asked
        self.has = has
        super().__init__(f'you are broke as shit (command supplied with {asked}, user has {has})')

class MultipleInstanceError(BruhCasinoError):
    def __init__(self, cmd: Command) -> None:
        self.command = cmd
        super().__init__(f'Only 1 instance of a command can be running at a time! ({cmd.name})')

class RateError(BruhCasinoError):
    def __init__(self) -> None:
        super().__init__('You have been rate limited! Try again later.')

class UnderConstruction(BruhCasinoError):
    def __init__(self) -> None:
        super().__init__('not yet my dude')

class Uhhhhhh(BruhCasinoError):
    def __init__(self) -> None:
        super().__init__('errrm..., you cant do that')

class TooMuchData(BruhCasinoError):
    def __init__(self) -> None:
        super().__init__('Command received too much data, could not continue!')

class CommandTimeoutError(EditableBruhCasinoError):
    def __init__(self,
                 time: int = 20,
                 msg: Message = None) -> None:
        self.time = time
        super().__init__(msg, f'Sorry, you failed to respond in {time} seconds so I gave up')

class CommandNotEnabled(BruhCasinoError):
    def __init__(self, command:str) -> None:
        self.command = command
        super().__init__(f'The command "{command}" is not enabled for this server.')
