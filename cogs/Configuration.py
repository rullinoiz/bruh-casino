import discord
from discord import Interaction, app_commands
from discord.ext import commands
from discord.app_commands import Choice

from bc_common import BruhCasinoEmbed
from modules.server import server
from modules.checks import is_developer
from bc_common.BruhCasinoCog import BruhCasinoCog
from bot_config import bot_config as bcfg

import typing

sv_data = bcfg["server_data_desc"]

class Configuration(BruhCasinoCog):
    config = app_commands.Group(name="config", description="we do a little configuration")

    @staticmethod
    def _to_bool(t: typing.AnyStr) -> bool | None:
        print(t)
        try:
            return bool(int(t))
        except ValueError:
            return True if 'true' in t.lower() else False if 'false' in t.lower() else None

    @config.command(name="set")
    @commands.check_any(commands.has_permissions(manage_guild=True), is_developer())
    async def _config_set(self, ctx: Interaction, key: str, val: str) -> None:
        """we do a little configuration"""
        if key not in sv_data:
            self._config_options.invoke(ctx)

        if sv_data[key]["type"] == "bool":
            if self._to_bool(val) is None:
                await ctx.response.send_message(f"value for `{key}` is not a boolean (true or false)!!!")
                return
            val = self._to_bool(val)
        if sv_data[key]["type"] == "int":
            try:
                val = int(val)
            except ValueError:
                await ctx.response.send_message(f"value for `{key}` is not an integer (whole number)!!!")
                return

        server.write(ctx.guild.id, key, val)
        await ctx.response.send_message(f"successfully set `{key}` to `{val}`")

    @config.command(name="get")
    async def _config_get(self, ctx: Interaction, key: str) -> None:
        if key not in sv_data:
            self._config_options.invoke(ctx)

        await ctx.response.send_message(embed=BruhCasinoEmbed(
            title=f"Bot Configuration: {key}",
            description=f"`{sv_data[key]['type']}`: {sv_data[key]['desc']}\n\nCurrently set to: `{server.read(ctx.guild.id, key)}`"
        ))

    @config.command(name="options")
    async def _config_options(self, ctx: Interaction) -> None:
        """we do a little checking configuration options"""
        await ctx.response.send_message(embed=BruhCasinoEmbed(
            title="Bot Configuration",
            description='\n'.join(
                ["- **{0}** (`{1}`): {2}".format(i, sv_data[i]["type"], sv_data[i]["desc"]) for i in
                 server.columns]) + f'\n\nRun `/config set [option] [value]` to configure this bot for this server',
            color=discord.Color.orange()
        ))
           
    @_config_set.autocomplete("key")
    @_config_get.autocomplete("key")
    async def config_autocomplete_key(self, _: Interaction, current: str) -> list[Choice]:
        data: list[Choice] = []
        #if current == "": return [Choice(name=p, value=p) for p in sv_data.keys()]
        for i in sv_data.keys():
            if current in i:
                data.append(Choice(name=i, value=i))
        return data



setup = Configuration.setup
