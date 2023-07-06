import json as j
from bot_config import bot_config

from discord import Member as dmember

class user:
    def write(userid:int,stat:str,content) -> None:
        """
        Parameters
        ----------
        userid : INT
            The ID of the user you want to write to.
        stat : STR
            The stat you want to write to.
        content : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        temp = open(bot_config['datapath'],"r")
        data = j.loads(str(temp.read()))
        temp.close()
        if not str(userid) in data:
            data[str(userid)] = bot_config['default_template']
        elif str(userid) in data:
            data[str(userid)][stat] = content
        
        temp = open(bot_config['datapath'],"w")
        temp.write(str(j.dumps(data)))
        temp.close()

    def read(userid:int,stat:str):
        """
        Parameters
        ----------
        userid : INT
            The ID of the user you want to read from.
        stat : STR
            The stat you want to read from the user.

        Returns
        -------
        STR/INT
            Read stats.

        """
        temp = open(bot_config['datapath'],"r")
        data = j.loads(str(temp.read()))
        temp.close()
        if not str(userid) in data:
            data[str(userid)] = bot_config['default_template']
            temp = open(bot_config['datapath'],"w")
            temp.write(str(j.dumps(data)))
            temp.close()
        elif str(userid) in data:
            if not stat in data[str(userid)]:
                if not stat in bot_config['default_template']:
                    data[str(userid)][stat] = 0
                    temp = open(bot_config['datapath'],"w")
                    temp.write(str(j.dumps(data)))
                    temp.close()
                elif stat in bot_config['default_template']:
                    data[str(userid)][stat] = bot_config['default_template'][stat]
                    temp = open(bot_config['datapath'],"w")
                    temp.write(str(j.dumps(data)))
                    temp.close()
                    
        return data[str(userid)][stat]

    def add(userid:int,stat:str,value:int) -> None:
        """
        Parameters
        ----------
        userid : INT
            The ID of the user you want to write to.
        stat : STR
            The stat you want to add to.
        value : INT
            How much to add to the stat.

        Returns
        -------
        None.

        """
        user.write(userid,stat,user.read(userid,stat) + value)
    
    def has_role(member:dmember,roleid:int) -> bool:
        """
        Parameters
        ----------
        member : discord.Member
            The member you want to check.
        roleid : INT
            The ID of the role you want to check for.

        Returns
        -------
        BOOL

        """
        hasrole = False
        for i in member.roles:
            if str(i.id) == str(roleid):
                hasrole = True
                
        return hasrole