import json as j
from bot_config import bot_config

class server:
    def write(id:int,stat:str,content) -> None:
        """
        Parameters
        ----------
        id : INT
            The ID of the server you want to write to.
        stat : STR
            The stat you want to write to.
        content : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        temp = open(bot_config['serverpath'],"r")
        data = j.loads(str(temp.read()))
        temp.close()
        if not str(id) in data:
            data[str(id)] = bot_config['default_template_server']
        elif str(id) in data:
            data[str(id)][stat] = content
        
        temp = open(bot_config['serverpath'],"w")
        temp.write(str(j.dumps(data)))
        temp.close()

    def read(id:int,stat:str):
        """
        Parameters
        ----------
        id : INT
            The ID of the server you want to read from.
        stat : STR
            The stat you want to read from the server.

        Returns
        -------
        STR/INT
            Read stats.

        """
        temp = open(bot_config['serverpath'],"r")
        data = j.loads(str(temp.read()))
        temp.close()
        if not str(id) in data:
            data[str(id)] = bot_config['default_template_server']
            temp = open(bot_config['serverpath'],"w")
            temp.write(str(j.dumps(data)))
            temp.close()
        elif str(id) in data:
            if not stat in data[str(id)]:
                if not stat in bot_config['default_template_server']:
                    data[str(id)][stat] = 0
                    temp = open(bot_config['serverpath'],"w")
                    temp.write(str(j.dumps(data)))
                    temp.close()
                elif stat in bot_config['default_template_server']:
                    data[str(id)][stat] = bot_config['default_template_server'][stat]
                    temp = open(bot_config['serverpath'],"w")
                    temp.write(str(j.dumps(data)))
                    temp.close()
                    
        return data[str(id)][stat]

    def add(id:int,stat:str,value:int) -> None:
        """
        Parameters
        ----------
        id : INT
            The ID of the server you want to write to.
        stat : STR
            The stat you want to add to.
        value : INT
            How much to add to the stat.

        Returns
        -------
        None.

        """
        server.write(id,stat,server.read(id,stat) + value)