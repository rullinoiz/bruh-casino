import sqlite3 as s
from json import loads

c = s.connect("../serverdata.db")

c.execute("""CREATE TABLE IF NOT EXISTS server(
    id UNSIGNED INTEGER PRIMARY KEY, 
    levelmsg TEXT DEFAULT "funny man {user} just got to level {level}",
    levelup_announce INTEGER DEFAULT 1,
    bruhreact INTEGER DEFAULT 1,
    speech_bubble INTEGER DEFAULT 1,
    lingering_levelup INTEGER DEFAULT 1,
    i_saw_what_you_deleted INTEGER DEFAULT 1,
    lowtiergod INTEGER DEFAULT 1,
    disabled_commands TEXT DEFAULT ""
)""")

with open("../serverdata.txt", "r") as f:
    json = loads(str(f.read()))

for i, entry in json.items():
    server: int = int(i)
    levelmsg: str = entry.get("levelmsg")
    levelup_announce: int = 1 if entry.get("levelup_announce") else 0
    bruhreact: int = 1 if entry.get("bruhreact") else 0
    speech_bubble: int = 1 if entry.get("speech_bubble") else 0
    lingering_levelup: int = 1 if entry.get("lingering_levelup") else 0
    i_saw_what_you_deleted: int = 1 if entry.get("i_saw_what_you_deleted") else 0
    lowtiergod: int = 1 if entry.get("lowtiergod") else 0
    disabled_commands: str = ",".join({x.replace("enable_", "") for x, v in entry.items() if "enable_" in x and v is False})
    print(server, levelmsg, levelup_announce, bruhreact, speech_bubble, lingering_levelup, i_saw_what_you_deleted, lowtiergod, disabled_commands)
    c.execute(f"""
        INSERT INTO server(
            id, 
            levelmsg, 
            levelup_announce, 
            bruhreact, 
            speech_bubble, 
            lingering_levelup, 
            i_saw_what_you_deleted, 
            lowtiergod, 
            disabled_commands
        ) VALUES(
            {server}, 
            "{levelmsg}", 
            "{levelup_announce}", 
            "{bruhreact}",
            "{speech_bubble}", 
            "{lingering_levelup}", 
            "{i_saw_what_you_deleted}", 
            "{lowtiergod}", 
            "{disabled_commands}"
        );
    """)
    c.commit()




