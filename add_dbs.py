import json
import os
dd = {}
for (root,dirs,files) in os.walk('/data/'): 
    if  'db_config.json' in files:
        print (root.split('/')[2:-1])
        parents = root.split('/')[2:-1]
        db_name = root.split('/')[-1]
        dx = dd
        for p in parents:
            #
            if p not in dx.keys():
                dx[p] = {}
            dx = dx[p]
        # = root
        path = root
        dx[db_name] = path
        print (parents)
        print (db_name)
outf = open('./api_gui/dbs.json','wt')
json.dump(dd, outf)
outf.close()


