import json as j

datapath = "userdata.txt"

class user:
    def write(userid,stat,content):
        try:
            temp = open(datapath,"r")
            data = j.loads(str(temp.read()))
            data[str(userid)][stat] = content
            temp.close()
        except:
            temp = open(datapath,"r")
            data = j.loads(str(temp.read()))
            data[str(userid)] = default_template
            data[str(userid)][stat] = content
            temp.close()

        temp = open(datapath,"w")
        temp.write(str(j.dumps(data)))
        temp.close()

    def read(userid,stat):
        try:
            temp = open(datapath,"r")
            data = j.loads(str(temp.read()))
            temp.close()
            return data[str(userid)][stat]
        except:
            temp = open(datapath,"r")
            data = j.loads(str(temp.read()))
            temp.close()
            data[str(userid)] = default_template
            temp = open(datapath,"w")
            temp.write(str(j.dumps(data)))
            temp.close()
            return data[str(userid)][stat]

    def add(userid,stat,value):
        user.write(userid,stat,user.read(userid,stat) + value)

temp = open(datapath,"r")
data = j.loads(str(temp.read()))
temp.close()

for i in data:
    user.write(str(i),"money",100000)
    user.write(str(i),"moneygained",0)
    user.write(str(i),"moneylost",0)



