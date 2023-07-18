import discord
from discord.ext import commands

from modules.server import server
from modules.checks import is_developer
from bot_config import bot_config as bcfg

import typing

class Configuration(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

    @staticmethod
    def _to_bool(t) -> typing.Union[bool, None]:
        print(t)
        try:
            return bool(int(t))
        except ValueError:
            return True if 'true' in t.lower() else False if 'false' in t.lower() else None

    @commands.hybrid_command(name='config', aliases=['cfg'])
    @commands.check_any(commands.has_permissions(manage_guild=True),is_developer())
    async def _config(self, ctx:commands.Context, key:str=None, *, val:str=None) -> None:
        """we do a little configuration"""
        sv_data = bcfg['server_data_desc']
        if not key or (key not in sv_data):
            await ctx.send(embed=discord.Embed(
                title='Bot Options',
                description='\n'.join(["- **{0}** (`{1}`): {2}".format(i,sv_data[i]['type'],sv_data[i]['desc']) for i in sv_data]) + f'\n\nRun `{bcfg["prefix"]}config [option] [value]` to configure this bot for this server',
                color=discord.Color.orange()
            ).set_footer(text=bcfg['footer']))
            return
        
        if key and not val:
            await ctx.send(embed=discord.Embed(
                title=f"Bot Configuration: {key}",
                description=f"`{sv_data[key]['type']}`: {sv_data[key]['desc']}\n\nCurrently set to: `{server.read(ctx.guild.id,key)}`"
            ).set_footer(text=bcfg['footer']))
            return

        if key and val:
            if sv_data[key]['type'] == 'bool':
                if self._to_bool(val) is None:
                    await ctx.send(f"value for `{key}` is not a boolean (true or false)!!!")
                    return
                val = self._to_bool(val)
            if sv_data[key]['type'] == 'int':
                try:
                    val = int(val)
                except ValueError:
                    await ctx.send(f"value for `{key} is not a integer (whole number)!!!")
                    return

            server.write(ctx.guild.id,key,val)
            await ctx.send(f"successfully set `{key}` to `{val}`")
           
    @_config.autocomplete('key')
    async def config_autocomplete_key(self, ctx:commands.Context, current:str) -> list[discord.app_commands.Choice]:
        data = []
        for i in bcfg['server_data_desc'].keys():
            if current in i:
                data.append(discord.app_commands.Choice(name=i,value=i))
        return data


async def setup(bot) -> None:
    await bot.add_cog(Configuration(bot))
