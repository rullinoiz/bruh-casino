import sqlite3 as sq
import json as j

from sqlite3 import Error

jsdb_path = r'../userdata.txt'
sqldb_path = r'../user.db'

temp = open(jsdb_path,'r')
jsdb = j.loads(str(temp.read()))
temp.close()
del temp

try:
    sqldb = sq.connect(sqldb_path)
except Error as e:
    print(e)
    exit()

sqlc = sqldb.cursor()

for id in jsdb:
    print(id)
    t = jsdb[id]
    sqlc.execute("""
        insert into user(id, money, moneygained, moneylost, wins, loss, exp, lvl, bruh, daily, lastmsg)
        values(?,?,?,?,?,?,?,?,?,?,?);""",(id,t['money'],str(t['moneygained']),str(t['moneylost']),t['wins'],t['loss'],t.get('exp',0),t.get('lvl',0),t['bruh'],t.get('daily',0),t.get('lastmsg',0)))

sqldb.commit()
