from discord.ext import commands
from discord import Message

class BruhCasinoError(commands.CommandError):
    def __init__(self,
                 msg: str = 'Exception Raised!',
                 codestyle: bool = False) -> None:
        self.msg = msg
        self.codestyle = codestyle
        super().__init__(msg)

class EditableBruhCasinoError(BruhCasinoError):
    def __init__(self, message: Message, *args, **kwargs) -> None:
        self.message = message
        super().__init__(*args, **kwargs)