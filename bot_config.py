import time
import subprocess

bot_config = {
    "prefix":"+",
    "footer":"© rullinoiz - {0}".format(subprocess.run(['git','log','--pretty=format:"commit: %h"','-1'], capture_output=True, text=True).stdout[1:-1]),
    "version":"40%",
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
        "levelup_announce": {
            "desc": "Whether or not to announce that a user has leveled up",
            "type": "bool"
        },
        "bruhreact": {
            "desc": "Set whether the bot reacts to any message with the word \"bruh\" in it. Best left off.",
            "type": "bool",
        },
        "speech_bubble": {
            "desc": "Set whether the bot randomly (1% chance) sends a speech bubble gif to destroy an argument",
            "type": "bool",
        },
        "i_saw_what_you_deleted": {
            "desc": "Set whether to post 'i saw what you deleted' gif when a user deletes a message",
            "type": "bool",
        },
        "lowtiergod": {
            "desc": "Set whether to reply to messages with various horrible game titles in them with lowtiergod",
            "type": "bool",
        },
        "lingering_levelup": {
            "desc": "Set whether levelup messages are deleted after some time",
            "type": "bool",
        },
        "enable_snipe": {
            "desc": "enables the +snipe command which sends the last deleted message in the server",
            "type": "bool"
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
        "levelup_announce": True,
        "bruhreact": False,
        "speech_bubble": True,
        "lingering_levelup": True,
        "i_saw_what_you_deleted": True,
        "enable_snipe": True,
        "lowtiergod": True,
    },
    "le_admin":441422344851030046
}
