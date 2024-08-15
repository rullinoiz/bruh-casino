from discord import Embed
from bot_config import bot_config as bcfg

class BruhCasinoEmbed(Embed):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.set_footer(text=bcfg["footer"])
