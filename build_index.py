from dep_search import *
import importlib
import pysolr
import gzip
import sys
#import cPickle as pickle
import sqlite3
import codecs
from datetime import datetime
#from tree import Tree
import json
import re
import struct
import os
import zlib
import itertools
#import py_tree_lmdb
#import py_store_lmdb
import binascii 
#import solr_filter_db
#import db_util
#import DB
#import Blobldb 
import time
import pickle
import copy

import zstandard


ID,FORM,LEMMA,UPOS,XPOS,FEATS,HEAD,DEPREL,DEPS,MISC=range(10)

symbs=re.compile(r"[^A-Za-z0-9_]",re.U)


def s_streamer(begin_data, inp):
    for x in begin_data.rstrip(u'\n').split(u'\n'):
        #if len(x) > 0:
        yield x + u'\n'
    #yield begin_data.split(u'\n')[-1]
    for x in inp:
        yield x

def streamer(inp, amount=200):

    if isinstance(inp,str):
        f=open(inp,u"rt")
        sample = ''
        cc = 0
        for l in f:
            sample += l
            cc += 1
            if cc > amount: break
            
        f.seek(0)
        return sample, f
    else:
        f=inp
        sample = ''
        cc = 0
        for l in f:
            sample += l
            cc += 1
            if cc > amount: break
        return sample, s_streamer(sample, f)        
    

def mean(numbers):
    return float(sum(numbers)) / max(len(numbers), 1)

def read_conll(inp,maxsent=0,skipfirst=0):
    """ Read conll format file and yield one sentence at a time as a list of lists of columns. If inp is a string it will be interpreted as fi
lename, otherwise as open file for reading in unicode"""
    if isinstance(inp,str):
        f=open(inp,u"rt")
    else:
        f=inp#codecs.getreader("utf-8")(inp) # read inp directly
    count_yielded=0
    count=0
    sent=[]
    comments=[]
    for line in f:
        line=line.strip()
        if not line:
            if sent:
                count+=1
                if count>skipfirst:
                    count_yielded+=1
                    yield sent, comments
                if maxsent!=0 and count_yielded>=maxsent:
                    break
                sent=[]
                comments=[]
        elif line.startswith(u"#"):
            if sent:
                raise ValueError("Missing newline after sentence")
            comments.append(line)
            continue
        else:
            sent.append(line.split(u"\t"))
    else:
        if sent:
            yield sent, comments

    if isinstance(inp,(str, bytes)):
        f.close() #Close it if you opened it

def serialize_as_tset_array(tree_len,sets):
    """
    tree_len -> length of the tree to be serialized
    sets: array of tree_len sets, each set holding the indices of the elements
    """
    indices=[]
    for set_idx,s in enumerate(sets):
        for item in s:
            indices.append(struct.pack("@HH",set_idx,item))
    #print "IDXs", len(indices)
    res=("".join(indices))
    return res

doc_url_re=re.compile(r'^###C:<doc id=.+url="(.*?)"')
def get_doc_url(comments):
    for c in comments:
        match=doc_url_re.match(c)
        if match:
            return c
    else:
        return None





def write_db_json(args):
    try:
        os.mkdir(args.dir)
    except:
        pass

    if os.path.exists(args.dir+'/langs'):
        outf = open(args.dir+'/langs', 'at')
    else:
        outf = open(args.dir+'/langs', 'wt')

    outf.write(args.lang + '\n')
    outf.close()

    outf = open(args.dir+'/db_config.json', 'wt')
    json.dump(vars(args), outf, indent = 4)
    outf.close()

def getCurrentMemoryUsage():
    ''' Memory usage in kB '''

    with open('/proc/self/status') as f:
        memusage = f.read().split('VmRSS:')[1].split('\n')[0][:-3]

    return int(memusage.strip())


if __name__=="__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train')
    parser.add_argument('-d', '--dir', required=True, help='Directory name to save the index. Will be wiped and recreated.')
    parser.add_argument('--skip-first', type=int, default=0, help='How many sentences to skip before starting the indexing? 0 for none. default: %(default)d')
    parser.add_argument('--max', type=int, default=0, help='How many sentences to read from stdin? 0 for all. default: %(default)d')
    parser.add_argument('--wipe', default=False, action="store_true", help='Wipe the target directory before building the index.')
    parser.add_argument('--solr', default="http://localhost:8983/solr/dep_search",help='Solr url. default: %(default)s')
    parser.add_argument('--lang', default="unknown", help='Language. default: %(default)s')
    parser.add_argument('--source', default="unknown", help='Source (like UDv2, fi_pbank). default: %(default)s')

    parser.add_argument('--blobdb', default="lmdb_Blobldb", help='Blob database module. default: %(default)s')
    parser.add_argument('--filterdb', default="lmdb_filter_db", help='Filter database module. default: %(default)s')

    parser.add_argument('--write_map', default=False, action="store_true", help='Write_map for lmdb, increases indexing performance at possible cost for db stability.')
    parser.add_argument('--map_size', type=int, default=15000000000, help='Maximum single lmdb database file size. default: %(default)s')
    parser.add_argument('--cut_database_by_trees', type=int, default=0, help='If this value is not 0, it will cut the database into multiple databases. This value is the maximum trees per database. default: %(default)s')

    args = parser.parse_args(sys.argv[1:])
    
    base_dir = args.dir
    if args.cut_database_by_trees > 0:
        args.dir += '_part_0'
       
    write_db_json(args)

#    gather_tbl_names(codecs.getreader("utf-8")(sys.stdin))
    os.system("mkdir -p "+args.dir)
    if args.wipe:
        print ("Wiping target", file=sys.stderr)
        cmd="rm -f %s/*.mdb %s/set_dict.pickle"%(args.dir,args.dir)
        print (cmd, file=sys.stderr)
        os.system(cmd)
        pysolr.Solr(args.solr,timeout=10000000).delete(q="*:*")

    part = 0

    dict_size = 10000

    #Load the database modules
    sys.path.append('./dep_search/')
    import py_tree
    #pkg_loader = importlib.find_loader('dep_search')
    #pkg = pkg_loader.load_module()

    set_id_db = importlib.import_module(args.blobdb)
    blob_db = importlib.import_module(args.blobdb)
    filter_db = importlib.import_module(args.filterdb)

    #blob_db = importlib.import_module(args.blobdb, package='dep_search')
    #filter_db = importlib.import_module(args.filterdb, package='dep_search')
    #if args.cut_database_by_trees > 0:
    #    args.dir = args.dir + '_part_' + str(part)
    #    part += 1


    db = blob_db.DB(args.dir, map_size=150000000000)
    db.open()
    solr_idx=filter_db.IDX(args)

    #int(args.map_size)
    if args.blobdb == 'lmdb_Blobldb':
        set_id_db = blob_db.DB(args.dir, cache=True, map_size=args.map_size, write_map=args.write_map)
    else:
        set_id_db = blob_db.DB(args.dir)
    set_id_db.open(foldername='/set_id_db/')

    sample, f = streamer(sys.stdin)

    
    src_data=read_conll(f, args.max, args.skip_first)
    set_dict={}
    lengths=0
    counter=0


    tree_id=0
    from collections import Counter
    setarr_count = Counter([])
    
    sent_limit = 256

    count_ones_own_idx = False
    self_idx = 0

    dict_ready = False
    s_db_times = []
    f_db_times = []
    b_db_times = []

    curr_url = None

    from datetime import datetime
    start_time = datetime.now()

    #load comp_dict
    try:
        inf = open(args.dir + '/comp_dict.pickle','rb')
        sample = pickle.load(inf)
        inf.close()
        comp_dict = zstandard.ZstdCompressionDict(sample.encode('utf8'))
        compressor = zstandard.ZstdCompressor(dict_data=comp_dict)
    except:
         comp_dict = zstandard.ZstdCompressionDict(sample.encode('utf8'))
         compressor = zstandard.ZstdCompressor(dict_data=comp_dict)


    args.dir = base_dir
    print ()
    print ()
    try:
        for counter,(sent,comments) in enumerate(src_data):

            if len(sent)>sent_limit:
                continue #Skip too long sentences
            if max(len(cols[FORM]) for cols in sent)>50 or max(len(cols[LEMMA]) for cols in sent)>50:
                continue
                #continue

            if args.cut_database_by_trees > 0 and (counter+1)%args.cut_database_by_trees == 0:
                #close db
                
                solr_idx.commit(force=True) #WHatever remains
                print ("Average tree length:", lengths/float(counter))
                db.close()
                db.finish_indexing()
                #open a new one
                self_idx = 0
                outf = open(args.dir + '_part_' + str(part) + '/comp_dict.pickle','wb')
                pickle.dump(sample, outf)
                outf.close()
                
                part += 1
                db = blob_db.DB(args.dir + '_part_' + str(part), map_size=150000000000)
                db.open()
                gargs = copy.deepcopy(args)
                gargs.dir = args.dir + '_part_' + str(part)
                solr_idx=filter_db.IDX(gargs)

                #int(args.map_size)
                if args.blobdb == 'lmdb_Blobldb':
                    set_id_db = blob_db.DB(args.dir + '_part_' + str(part), cache=True, map_size=args.map_size, write_map=args.write_map)
                else:
                    set_id_db = blob_db.DB(args.dir + '_part_' + str(part))
                set_id_db.open(foldername='/set_id_db/')


                if os.path.exists(args.dir + '_part_' + str(part)+'/langs'):
                    outf = open(args.dir + '_part_' + str(part)+'/langs', 'at')
                else:
                    outf = open(args.dir + '_part_' + str(part)+'/langs', 'wt')

                outf.write(args.lang + '\n')
                outf.close()

                outf = open(args.dir + '_part_' + str(part) +'/db_config.json', 'wt')
                json.dump(vars(args), outf, indent = 4)
                outf.close()                

                outf = open(args.dir + '_part_' + str(part) + '/comp_dict.pickle','wb')
                pickle.dump(sample, outf)
                outf.close()






            if (counter)%100 == 0:

                print (counter+1,',',datetime.now()-start_time, ',', getCurrentMemoryUsage()/1000.0, 'MB')
                try:
                    print (mean(f_db_times))
                    print (mean(b_db_times))
                    print (mean(s_db_times))
                except:
                    pass

                s_db_times = []
                f_db_times = []
                b_db_times = []

                #print ("At tree ", counter+1)
                sys.stdout.flush()

            s=py_tree.Py_Tree()
            s.set_comp_dict(sample.encode('utf8'))
            start = time.time()
            blob, form =s.serialize_from_conllu(sent,comments,set_id_db, compressor) #Form is the struct module format for the blob, not used anywhere really
            end = time.time()
            s_db_times.append(end-start)
            scomp_dict = {}
            
            



            s.deserialize(blob)
            lengths+=len(sent)
            counter+=1
            set_cnt = struct.unpack('=H', blob[2:4])
            arr_cnt = struct.unpack('=H', blob[4:6])
            set_indexes = struct.unpack('=' + str(set_cnt[0]) + 'I', blob[6:6+set_cnt[0]*4])
            arr_indexes = struct.unpack('=' + str(arr_cnt[0]) + 'I', blob[6+set_cnt[0]*4:6+set_cnt[0]*4+arr_cnt[0]*4])


            setarr_count.update(set_indexes + arr_indexes)
            try:
                doc_url=get_doc_url(comments)
                if doc_url is not None:
                    solr_idx.new_doc(doc_url,args.lang)
            except:
                pass
            for c in comments:
                if c.startswith('# </doc>'):
                    curr_url = None
                if c.startswith('# <doc'):
                    curr_url = c
                    solr_idx.new_doc(curr_url,args.lang)

            if not count_ones_own_idx:
                tree_id=solr_idx.add_to_idx(comments, sent)
                db.store_blob(blob, tree_id)
                count_ones_own_idx = True
                self_idx = tree_id
            else:
                self_idx += 1
                start = time.time()
                #
                solr_idx.add_to_idx_with_id(comments, sent, self_idx)
                end = time.time()
                f_db_times.append(end-start)

                start = time.time()
                #Blob
                db.store_blob(blob, self_idx)
                end = time.time()
                b_db_times.append(end-start)

        solr_idx.commit(force=True) #WHatever remains


        print ("Average tree length:", lengths/float(counter))
        
        set_id_db.close()
        set_id_db.finish_indexing()

        outf = open(args.dir + '/comp_dict.pickle','wb')
        pickle.dump(sample, outf)
        outf.close()

        
        db.close()
        db.finish_indexing()
        #http://localhost:8983/solr/dep_search2/update?commit=true
    except KeyboardInterrupt:
        set_id_db.close()
        set_id_db.finish_indexing()    
    
        db.close()
        db.finish_indexing()        


