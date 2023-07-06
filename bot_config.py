import discord
import hashlib as hsh
import time

bot_config = {
    "prefix":"+",
    "footer":"© rullinoiz - {0}".format(hsh.md5(str(time.time()).encode("utf-8")).hexdigest()),
    "version":"10%",
    "datapath":"userdata.txt",
    "serverpath":"serverdata.txt",
    "botlogs":"botlogs.txt",
    "dailymoney":500,
    "expincrement":50,
    "expstart":100,
    "server_data_desc":{
        "levelmsg": {
            "desc": "Set the level up message. Comes with variables {user} and {level}.",
            "type": "str",
        },
        "bruhreact": {
            "desc": "Set whether the bot reacts to any message with the word \"bruh\" in it. Best left off.",
            "type": "bool",
        }
    },
    "default_template":{
        "money": 1000,
        "moneylost": 0,
        "moneygained": 0,
        "wins": 0,
        "loss": 0,
        "exp": 0,
        "lvl": 0,
        "bruh": 0,
        "calc": 10,
        "dateused": time.time(),
        "daily": 0,
        "lastmsg": time.time()
    },
    "default_template_server":{
        "levelmsg": "funny man {user} just got to level {level}",
        "bruhreact": False,
    },
    "le_admin":441422344851030046

}