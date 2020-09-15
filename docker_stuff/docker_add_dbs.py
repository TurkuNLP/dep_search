import glob
import json
from collections import defaultdict
import os.path


def get_flat_dbs():

    dbs = {}
    folders = glob.glob('/var/dbs/*')
    for f in folders:
        print (f)
        dbs[f.rstrip('/').split('/')[-1]] = f


    flat_dict = {}

    xpx = []
    dd = defaultdict(dict)
    for k in dbs.keys():
        init_path = dbs[k]
        if not init_path.endswith('/'):
            init_path += '/'
        dx = dd
        root = k
            
        if os.path.exists(os.path.join(init_path, "db_config.json")):
            dd[root] = init_path
        else:
            dd[root] = {}
            for dirname, dirnames, filenames in os.walk(init_path):
                for subdirname in dirnames:
                    if os.path.isdir(os.path.join(dirname, subdirname)):
                        #print(os.path.join(dirname, subdirname))
                        dx = dd
                        for xx in os.path.join(dirname, subdirname).split('/')[len(init_path.split('/'))-2:-1]:
                            dx = dx[xx]
                        if os.path.exists(os.path.join(dirname, subdirname, "db_config.json")):
                            dx[os.path.join(dirname, subdirname).split('/')[-1]] = os.path.join(dirname, subdirname)
                            flat_dict[os.path.join(dirname, subdirname).split('/')[-1]] = os.path.join(dirname, subdirname)
                        else:
                            if not isinstance(os.path.join(dirname, subdirname).split('/')[-1], str):
                                dx[os.path.join(dirname, subdirname).split('/')[-1]] = {}

        xxm = {}


    return flat_dict

def gdsb():

    dbs = {}
    folders = glob.glob('/var/dbs/*')
    for f in folders:
        dbs[f.rstrip('/').split('/')[-1]] = f

    xpx = []
    dd = defaultdict(dict)
    for k in dbs.keys():
        init_path = dbs[k]
        if not init_path.endswith('/'):
            init_path += '/'
        dx = dd
        root = k
        if os.path.exists(os.path.join(init_path, "db_config.json")):
            dd[root] = init_path
        else:
            #dd[root] = {}
            print ('i', init_path)
            for dirname, dirnames, filenames in os.walk(init_path, followlinks=True):
                for subdirname in dirnames:
                    if os.path.isdir(os.path.join(dirname, subdirname)):
                        #print(os.path.join(dirname, subdirname))
                        dx = dd
                        for xx in os.path.join(dirname, subdirname).split('/')[len(init_path.split('/'))-2:-1]:
                            dx = dx[xx]
                        if os.path.exists(os.path.join(dirname, subdirname, "db_config.json")):
                            dx[os.path.join(dirname, subdirname).split('/')[-1]] = os.path.join(dirname, subdirname)
                        else:
                            if not isinstance(os.path.join(dirname, subdirname).split('/')[-1], str):
                                dx[os.path.join(dirname, subdirname).split('/')[-1]] = {}

        xxm = {}
    return dd 

folders = glob.glob('/var/dbs/*')
dx = {}
print ('!!', folders)
for d in folders:
    print (d)
    dx[d.split('/')[-2]] = d
outf = open('./api_gui/dbs.json','wt')
json.dump(dx, outf)
outf.close()
print (gdsb())
dd = gdsb()

#corpus groups
piece = '''-
  name: {}
  corpora: {}

'''
corpus_grp_str = ''
for k in dd.keys():
    corpus_grp_str += piece.format(k, ' '.join(dd[k].keys()))

outf = open('./api_gui/webapi/corpus_groups.yaml','wt')
outf.write(corpus_grp_str)
outf.close()
 
#dbs
piece = '''{}:
  name: {}
  paths: {}

'''
dd = get_flat_dbs()
db_str = ''
for k in dd.keys():
    db_str += piece.format(k, k, dd[k])

outf = open('./api_gui/webapi/corpora.yaml','wt')
outf.write(db_str)
outf.close()
