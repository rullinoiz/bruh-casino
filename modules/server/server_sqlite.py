import sqlite3 as sq
from bc_common.static_init import static_init
from bot_config import bot_config as bcfg
from typing import Union, Any, Sequence
from discord import Guild

@static_init
class server(object):
    s: sq.Connection = sq.connect(bcfg.get("serverpath"))
    c: sq.Cursor = s.cursor()

    @classmethod
    def __static__(cls) -> None:
        cls.c.execute("""
        CREATE TABLE IF NOT EXISTS "server"(
        "id" UNSIGNED INTEGER PRIMARY KEY,
        "levelmsg" TEXT DEFAULT 'funny man {user} just got to level {level}',
        "bruhreact" INTEGER DEFAULT 1,
        "speech_bubble" INTEGER DEFAULT 1,
        "lingering_levelup" INTEGER DEFAULT 1,
        "i_saw_what_you_deleted" INTEGER DEFAULT 1,
        "lowtiergod" INTEGER DEFAULT 1,
        "levelup_announce" INTEGER DEFAULT 1
        );
        """)
        cls.s.commit()
        cls.columns = [x[0] for x in cls.c.execute("SELECT name FROM pragma_table_info(\"server\")").fetchall()]
        cls.columns.remove("id")

    @classmethod
    def ensure_existence(cls, serverid: Union[int, Guild], add_new: bool = False) -> bool:
        serverid: int = getattr(serverid, "id", serverid)
        if cls.c.execute("select id from server where id = ?;", (serverid,)).fetchone() is None:
            if add_new:
                cls.c.execute("insert into server(id) values(?);", (serverid,))
                cls.s.commit()
            return False
        return True
    
    @classmethod
    def write(cls, serverid: Union[int, Guild], stat: str, value) -> None:
        userid: int = getattr(serverid, "id", serverid)
        cls.ensure_existence(userid, True)
        cls.c.execute(f"update server set {stat} = ? where id = ?;", (value, userid))
        cls.s.commit()
    
    @classmethod
    def read(cls, serverid: int | Guild, stat: str | Sequence[str]) -> Any:
        serverid: int = getattr(serverid, "id", serverid)
        cls.ensure_existence(serverid, True)
        if type(y := stat) is tuple: stat = ",".join(stat)
        t = cls.c.execute(f"select {stat} from server where id = ?;", (serverid,))
        x = t.fetchone()
        return x[0] if type(y) is not tuple else x
