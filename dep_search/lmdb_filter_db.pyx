# cython: language_level=3
# distutils: language = c++
import sys
import requests
import re
from io import StringIO
import time
from multiprocessing import Process, Queue
import traceback
import sys
import pysolr
import requests
import json
from dep_search cimport py_tree
import lmdb
import os

ID,FORM,LEMMA,UPOS,XPOS,FEATS,HEAD,DEPREL,DEPS,MISC=range(10)
field_re=re.compile(r"^(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)
class Query():

    def __init__(self,extra_terms, compulsory_items,or_groups, solr, case, q_obj, extra_params={}, langs=[]):


        #print (compulsory_items)

        self.q_obj = q_obj
        self.extra_params = extra_params
        self.case = case
        self.or_groups = or_groups
        self.extra_terms = extra_terms #extra solr terms
        self.compulsory_items = compulsory_items
        self.dir = solr
        self.tree_id_queue = Queue()
        self.finished = {}
        self.started = False
        self.processes = {}
        #Init lmdb                                                           1099511627776
        self.env = lmdb.open(self.dir + '/lmdb_filter/', max_dbs=1, map_size=1099511627776)
        self.db = self.env.open_db()
        #self.txn = self.env.begin()


	#Start the main loop thread
        if len(langs) < 1 or langs == ['']:
            self.processes['main'] = Process(target=self.main_loop)
            self.processes['main'].start()
        else:
            for l in langs:
                self.processes[l] = Process(target=self.main_loop_lang, args=(l,))
                self.processes[l].start()
        self.started = True


    def get_url(self, idx):
        with self.env.begin() as txn:
            return txn.get('tag_'.encode('utf8') + str(idx).encode('utf8') + '_url'.encode('utf8'), default=b'').decode('utf8')

    def get_queue(self):
        return self.tree_id_queue

    def kill_threads(self):
        for p in self.processes.keys():
            self.processes[p].terminate()

    def get_queue_by_lang(self, lang):

        #This needs to start a "main loop", which will feed 
        self.processes[lang] = Process(target=self.main_loop)
        self.processes[lang].start()

        return self.lang_qs[lang]

    def main_loop_lang(self, lang):
        self.started=True
        self.finished[lang]=False
        #self.lang_qs[lang] = Queue()

        if lang != '':
            for idx in self.ids_gen(extra_tags=['lang_' + lang]):
                #Feed it to the queue
                self.tree_id_queue.put(idx)
        else:
            for idx in self.ids_gen():
                #Feed it to the queue
                self.tree_id_queue.put(idx)

        self.finished[lang]=True
        self.tree_id_queue.put(-1)


    def main_loop(self):
        self.started=True
        self.finished['main'] = False
        for idx in self.ids_gen():
            #Feed it to the queue
            self.tree_id_queue.put(idx)
        self.finished['main']=True
        self.tree_id_queue.put(-1)

    def kill(self):
        self.process.terminate()

    def is_finished(self):

        if not self.started: return False

        for p in self.finished:
            if not p:
                return False
        return True

    def ids_gen(self, extra_tags=[]):

        #This guy yields ints, which are the blob ids we want

        #Check the list of required ints
        #If none, just give all ids :DD


        #Later we need to deal with ors as well
        comps = self.compulsory_items[:]# + extra_tags

        if len(extra_tags) > 0:
            comps = extra_tags

        #So, compulsory items
        counts = []
        hits = 0

        if len(comps) < 1:
            comps.append('dep_a_anyrel')

        for rec in comps:
            counts.append((int(self.get_count(rec)), rec))
        #import pdb;pdb.set_trace()
        counts.sort()
        rarest_pref=counts[0][1].encode('utf8')
        with self.env.begin() as txn:
            cursor = txn.cursor()
            #print (cursor.set_key(rarest_pref))
            cx = 0
            for key, val in cursor:
                if not key.startswith(rarest_pref): continue
                #print (key, val)
                matches = 0
                for c in counts:

                    found = False
                    #try:
                    if txn.get(c[1].encode('utf8') + '_'.encode('utf8') + key.split(b'_')[-1], default=None) != None:
                        found = True
                    #except:
                    else:
                        found = False
            
                    if not found:
                        break
                    else:
                        matches += 1

                if matches == len(counts):
                    #print ('!!!!', int(idx[0].split('_'.encode('utf8'))[-1]))
                    yield int(key.split(b'_')[-1])#int(idx[0].split('_'.encode('utf8'))[-1])
                    #print ('!!', int(key.split(b'_')[-1]))
                    hits += 1
                #cx += 1

    def get_lang(self, idx):
        with self.env.begin() as txn:
            return txn.get('tag_'.encode('utf8') + str(idx).encode('utf8') + '_lang'.encode('utf8'), default=None).decode('utf8')


    def get_count(self, pref):
        counter = 0

        if isinstance(pref, str):
            pref = pref.encode('utf8')
        with self.env.begin() as txn:    
            cursor = txn.cursor()
            if not cursor.set_range(pref):
                return b'0'

            for key, value in cursor:
                if key.startswith(pref):
                    counter += 1
            return str(counter).encode('utf8')




class IDX(object):

    def __init__(self,args):
        self.args=args # List of documents to be pushed into solr at the next convenient occasion
        self.lang = args.lang
        self.url = None

        self.s=py_tree.Py_Tree()
        self.name = args.dir
        self.blob = None
        self.open()
        self.transaction_count = 0
        self.puts = []

    def open(self):
        #check if pickle exists
        try:
            os.mkdir(self.name)
        except:
            pass

        self.env = lmdb.open(self.name + '/lmdb_filter/', max_dbs=1, map_size=self.args.map_size, writemap=self.args.write_map)
        self.db = self.env.open_db()
        #self.txn = self.env.begin(write=True)


    def set_idx_to_db_idx(self, list_idx):

        db_list = set()
        for idx in list_idx:

            if idx.endswith('_lc'):continue

            if idx.startswith('l_'):
                db_list.add('lemma_s_' + idx[2:])
                db_list.add('lemma_s_' + idx[2:].lower() + '_lc')
            elif idx.startswith('f_'):
                db_list.add('token_s_' + idx[2:])
                db_list.add('token_s_' + idx[2:].lower() + '_lc')
            elif idx.startswith('p_'):
                db_list.add('tag_s_' + idx[2:])
            elif idx.startswith('g_'):
                db_list.add('gov_a_' + idx[2:])
            elif idx.startswith('d_'):
                db_list.add('dep_a_' + idx[2:])
            else:
                db_list.add('tag_s_' + idx)

        db_list.add('dep_a_anyrel')
        return list(db_list)


    def commit(self,force=False):
        self.write_stuff()
        #self.txn.commit()
        #self.txn = self.env.begin(write=True)
        self.env.close()
        
    def new_doc(self,url,lang):

        #do something with these
        self.url=url
        self.lang=lang

    def add_to_idx_with_id(self, comments, sent, idx):
        # get set ids
        val = self.set_idx_to_db_idx(self.s.set_list_from_conllu(sent, comments))
        #import pdb;pdb.set_trace()
        #print (val)
        #idx = int(self.get_count('dep_a_anyrel'.encode('utf8')))
        for v in set(val):
            self.puts.append(((v + '_' + str(idx)).encode('utf8'), b'1'))

        #self.txn.commit()
        #self.txn = self.env.begin(write=True)
        #self.txn.put('tag_'.encode('utf8') + str(idx).encode('utf8') + '_url', self.lang.encode('utf8'))
        #self.txn.put('tag_'.encode('utf8'), b'1')
        self.puts.append(('tag_'.encode('utf8') + str(idx).encode('utf8') + '_lang'.encode('utf8'), self.lang.encode('utf8')))
        #self.txn.commit()
        #self.txn = self.env.begin(write=True)
        self.puts.append(('lang_'.encode('utf8') + self.lang.encode('utf8') + '_'.encode('utf8') + str(idx).encode('utf8'), b'1'))
        #self.txn.commit()
        #self.txn = self.env.begin(write=True)
        #self.txn = self.env.begin(write=True)
        
        self.transaction_count = len(self.puts)
        if self.transaction_count > 500:
            self.transaction_count = 0
            self.write_stuff()        
        
        return idx


    def write_stuff(self):
        with self.env.begin(write=True) as txn:
            for k, v in self.puts:
                txn.put(k, v)
            #self.txn.commit()
            #txn = self.env.begin(write=True)
            self.puts = []


    def add_to_idx(self, comments, sent):
        # get set ids
        val = self.set_idx_to_db_idx(self.s.set_list_from_conllu(sent, comments))
        #import pdb;pdb.set_trace()
        #print (val)
        idx = int(self.get_count('dep_a_anyrel'.encode('utf8')))
        for v in set(val):
            self.puts.append(((v + '_' + str(idx)).encode('utf8'), b'1'))
            #self.txn.commit()
            #self.txn = self.env.begin(write=True)
        #self.txn.put('tag_'.encode('utf8') + str(idx).encode('utf8') + '_url', self.lang.encode('utf8'))
        #self.txn.put('tag_'.encode('utf8'), b'1')
        self.puts.append(('tag_'.encode('utf8') + str(idx).encode('utf8') + '_lang'.encode('utf8'), self.lang.encode('utf8')))
        #self.txn.commit()
        #self.txn = self.env.begin(write=True)
        self.puts.append(('lang_'.encode('utf8') + self.lang.encode('utf8') + '_'.encode('utf8') + str(idx).encode('utf8'), b'1'))
        #self.txn.commit()
        #self.txn = self.env.begin(write=True)
        #self.txn = self.env.begin(write=True)
        self.transaction_count = len(self.puts)
        if self.transaction_count > 500:
            self.transaction_count = 0
            self.write_stuff()
            #self.txn.commit()
            #self.txn = self.env.begin(write=True)
        return idx

    def get_count(self, pref):
        counter = 0

        if isinstance(pref, str):
            pref = pref.encode('utf8')
        with self.env.begin() as txn:
            cursor = txn.cursor()
            if not cursor.set_range(pref):
                return b'0'

            for key, value in cursor:
                if key.startswith(pref):
                    counter += 1
            return str(counter).encode('utf8')
