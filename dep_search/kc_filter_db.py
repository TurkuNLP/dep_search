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
from dep_search import py_tree
from kyotocabinet import *

ID,FORM,LEMMA,UPOS,XPOS,FEATS,HEAD,DEPREL,DEPS,MISC=range(10)
field_re=re.compile(r"^(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)
class Query():

    def __init__(self,extra_terms, compulsory_items,or_groups, solr, case, q_obj, extra_params={}, langs=[]):


        print (compulsory_items)

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

        #Init db
        self.db = DB(self.dir + '/leveldb/', create_if_missing=True) 
        self.db.open(self.dir + '/blobs.kc', DB.OWRITER | DB.OCREATE)

	#Start the main loop thread
        if len(langs) < 1:
            self.processes['main'] = Process(target=self.main_loop)
            self.processes['main'].start()
        else:
            for l in langs:
                print (l)
                self.processes[l] = Process(target=self.main_loop_lang, args=(l,))
                self.processes[l].start()
        self.started = True

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

        for idx in self.ids_gen(extra_tags=['lang_' + lang]):
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
        #print (counts)

        rarest_queue = self.db.iterator(prefix=counts[0][1].encode('utf8'))

        for idx in rarest_queue:
            matches = 0
            for c in counts[1:]:

                found = False
                try:
                    self.db.get(c[1].encode('utf8') + '_'.encode('utf8') + idx)
                    found = True
                except:
                    found = False
        
                if not found:
                    break
                else:
                    matches += 1

            if matches == len(counts[1:]):
                #print ('!!!!', int(idx[0].split('_'.encode('utf8'))[-1]))
                yield int(idx[0].split('_'.encode('utf8'))[-1])
                hits += 1

    def get_lang(self, idx):
        return self.db.get('tag_'.encode('utf8') + str(idx).encode('utf8') + '_lang'.encode('utf8'))


    def get_count(self, pref):
        counter = 0
        if isinstance(pref, str):
            pref = pref.encode('utf8')

        for key in self.db:
            if key.startswith(pref):
                counter +=1
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

    def open(self):
        #check if pickle exists
        try:
            os.mkdir(self.name)
        except:
            pass

        self.db = DB(self.name + '/leveldb/', create_if_missing=True) 
        self.db.open(self.name + '/filter.kc', DB.OWRITER | DB.OCREATE)


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
        self.db.close()
        
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
        for v in val:
            self.db.set((v + '_' + str(idx)).encode('utf8'), b'1')
        
        #self.db.set('tag_'.encode('utf8') + str(idx).encode('utf8') + '_url', self.lang.encode('utf8'))
        self.db.set('tag_'.encode('utf8') + str(idx).encode('utf8') + '_lang'.encode('utf8'), self.lang.encode('utf8'))
        self.db.set('lang_'.encode('utf8') + self.lang.encode('utf8') + '_'.encode('utf8') + str(idx).encode('utf8'), b'1')
        return idx



    def add_to_idx(self, comments, sent):
        # get set ids
        val = self.set_idx_to_db_idx(self.s.set_list_from_conllu(sent, comments))
        #import pdb;pdb.set_trace()
        #print (val)
        idx = int(self.get_count('dep_a_anyrel'.encode('utf8')))
        for v in val:
            self.db.set((v + '_' + str(idx)).encode('utf8'), b'1')
        
        #self.db.set('tag_'.encode('utf8') + str(idx).encode('utf8') + '_url', self.lang.encode('utf8'))
        self.db.set('tag_'.encode('utf8') + str(idx).encode('utf8') + '_lang'.encode('utf8'), self.lang.encode('utf8'))
        self.db.set('lang_'.encode('utf8') + self.lang.encode('utf8') + '_'.encode('utf8') + str(idx).encode('utf8'), b'1')
        return idx

    def get_count(self, pref):
        counter = 0
        if isinstance(pref, str):
            pref = pref.encode('utf8')

        for key in self.db:
            if key.startswith(pref):
                counter +=1
        return str(counter).encode('utf8')
