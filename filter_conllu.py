#!/usr/bin/env python
import sys
import os
import ast
import importlib
import json
import re
import zlib
import argparse
import glob
from collections import defaultdict
import copy
from tempfile import gettempdir
from contextlib import contextmanager
import io

from dep_search import py_tree
from dep_search.query import load, get_query_mod

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


def query_from_db(q_obj, args, db, inp_f):

    #init the dbs
    q_obj.set_db(db)
    s=py_tree.Py_Tree()
    #import pdb;pdb.set_trace()


    #This is a first try and an example without filter db
    idx = 1
    counter = 0
    max_hits = args.max

    for sent, comments in read_conll(inp_f):
        try:

            # get next blob
            blob, form =s.serialize_from_conllu(sent,comments,db)
            # res_set = check blob
            #print (sent)
            #print (blob)
            if len(sent) < 2: continue
            # if end of stdin, just stop
           

            res_set = q_obj.check_blob(blob)
            idx += 1
            
            if len(res_set) > 0:
                #tree
                #import pdb;pdb.set_trace()
                hit = q_obj.get_tree_text()
                tree_comms = q_obj.get_tree_comms()
                tree_lines=hit.split("\n")

                if counter >= max_hits and max_hits > 0:
                    break
                its_a_hit = False

                for r in res_set:
                    print ("# db_tree_id:",idx)
                    print ("# visual-style\t" + str(r + 1) + "\tbgColor:lightgreen")
                    try:
                        print ("# hittoken:\t"+tree_lines[r])
                        its_a_hit = True
                    except:
                        pass

                if its_a_hit:

                    '''
                    if args.context>0:
                        hit_url=get_url(tree_comms)
                        texts=[]
                        # get +/- context sentences from db
                        for i in range(idx-args.context,idx+args.context+1):
                            if i==idx:
                                data=hit
                            else:
                                err = db.xset_tree_to_id(i)
                                if err != 0: continue
                                data = db.get_tree_text()
                                data_comment = db.get_tree_comms()

                                if data is None or get_url(data_comment)!=hit_url:
                                    continue
                            text=u" ".join(t.split(u"\t",2)[1] for t in data.split(u"\n"))
                            if i<idx:
                                texts.append(u"# context-before: "+text)
                            elif i==idx:
                                texts.append(u"# context-hit: "+text)
                            else:
                                texts.append(u"# context-after: "+text)
                    
                        print (u"\n".join(text for text in texts)).encode(u"utf-8")
                    '''

                    print (tree_comms)
                    print (hit)
                    print ()
                    counter += 1


        except IndexError as e:
            print(e)
            pass
            if idx > 0: break

    return counter

def main(argv):
    global query_obj

    #XXX: Will fix!
    global solr_url

    parser = argparse.ArgumentParser(description='Execute a query against the db')
    parser.add_argument('-m', '--max', type=int, default=0, help='Max number of results to return. 0 for all. Default: %(default)d.')
    parser.add_argument('-o', '--output', default=None, help='Name of file to write to. Default: STDOUT.')
    parser.add_argument('search', nargs="?", default="parsubj",help='The name of the search to run (without .pyx), or a query expression. Default: %(default)s.')
    parser.add_argument('-i', '--case', required=False, action='store_true',default=False, help='Case insensitive search.')
    parser.add_argument('-f', '--file',default=None,help="Input file")

    args = parser.parse_args(argv[1:])

    inp_f = sys.stdin
    if args.file is not None:
        inp_f = open(args.file,'rt')    

    if args.output is not None:
        sys.stdout = open(args.output, 'w')

    if os.path.exists(args.search+".pyx"):
        print >> sys.stderr, "Loading "+args.search+".pyx"
        mod=load(args.search)
    else:
        from dep_search import pseudocode_ob_3 as pseudocode_ob
        import hashlib
        m = hashlib.md5()
        m.update(args.search.encode('utf8') + str(args.case).encode('utf8'))
        try:
            os.mkdir(query_folder)
        except:
            pass

        from dep_search import PickleDB
        db = PickleDB.DB('')
        db.dynamic=True
        db.open()
        json_filename = '' 

    mod = get_query_mod(
        False,
        args.search,
        args.case,
        db,
        '-')
    query_obj = mod.GeneratedSearch()

    total_hits=0
    total_hits+=query_from_db(query_obj, args, db, inp_f)
    print ("Total number of hits:",total_hits,file=sys.stderr)


    '''
    total_hits=0
    total_hits+=query_from_db(query_obj, args, db, inp_f)
    print ("Total number of hits:",total_hits,file=sys.stderr)

    if not args.keep_query:
        try:
            pass
            os.remove(query_folder + temp_file_name)
            os.remove(query_folder + temp_file_name[:-4] + '.cpp')
            os.remove(query_folder + temp_file_name[:-4] + '.so')
        except:
            pass
    '''

if __name__=="__main__":
    sys.exit(main(sys.argv))
