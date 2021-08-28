import json
def view_databdase(databasepath):
    with open(databasepath,"r",encoding="utf-8",) as data:
        data_dict=json.loads(data.read())
        for i in data_dict.keys():
            print("title", i, "\n", "content", data_dict[i])
            print()
            print()