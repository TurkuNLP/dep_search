# cython: language_level=3
# distutils: language = c++
from dep_search.DB import BaseDB
import lmdb
from dep_search cimport py_tree
import os
import copy
import pickle
import struct

class DB(BaseDB):

    #
    def __init__(self, name, cache=False, map_size=10485760*5000, max_cache=50000):
        super().__init__(name)
        
        '''
        #load comp_dict
        try:
            inf = open(self.name + '/comp_dict.pickle','rb')
            self.comp_dict = pickle.load(inf)
            inf.close()
        except:
            self.comp_dict = {}
        '''
        self.s=py_tree.Py_Tree()
        self.name = name
        self.blob = None
        self.next_free_tag_id = None
        self.cache=cache
        self.cache_limit = max_cache
        self.cache_full = False
        self.puts = []
        self.transaction_count = 0
        self.map_size = map_size
        self.wlimit = 500
    #
    '''
    def write_comp_dict(self):
        outf = open(self.name + '/comp_dict.pickle','wb')
        pickle.dump(self.comp_dict, outf)
        outf.close()
    ''' 
    def open(self, foldername='/lmdb/'):
        #check if pickle exists
        try:
            os.mkdir(self.name)
        except:
            pass

        self.env = lmdb.open(self.name + foldername, max_dbs=2, map_size=self.map_size)
        #self.blob_db = self.env.open_db(b'blob')
        #self.set_db = self.env.open_db(b'sets')

        self.txn = self.env.begin(write=True)
        self.rtxn = self.env.begin()
        if self.cache:
            self.load_tags()


    def load_tags(self):
        self.tags = {}
        vals = []
        cursor = self.txn.cursor()
        for key, value in cursor:
            pref = b'tag_'
            if key.startswith(pref):
                val = int(struct.unpack('I', value)[0])
                self.tags[key] = val
                vals.append(val)
        try:
            self.next_free_tag_id = max(vals) + 1
        except:
            self.next_free_tag_id = 0

    #
    def close(self):
        self.write_stuff()
        self.env.close()

    def write_stuff(self):
        for k, v in self.puts:
            self.txn.put(k, v)
        self.txn.commit()
        self.txn = self.env.begin(write=True)
        self.puts = []

    #
    def add_to_idx(self, comments, sent):
        # get set ids
        val = self.s.set_id_list_from_conllu(sent, comments, self)
        idx = self.get_count('sets_'.encode('utf8'))
        self.txn.put('sets_'.encode('utf8') + idx, str(val).encode('utf8'))
        #self.txn.commit()
        return idx

    #
    def has_id(self, idx):
        #print (idx)

        if self.cache:
            if 'tag_'.encode('utf8') + idx.encode('utf8') in self.tags.keys():
                return True
            
        idx = idx.encode('utf8')
        #print (self.txn.get(b'tag_' + idx) != None)
        return self.txn.get(b'tag_' + idx) != None
    #

    def get_id_for(self, idx):
        if self.cache:
            try:
                return self.tags[('tag_' + idx).encode('utf8')]
            except:
                pass
        #else:
        #print (idx, int(self.txn.get(('tag_' + idx).encode('utf8'))))
        return int(struct.unpack('I', self.txn.get(('tag_' + idx).encode('utf8')))[0])
    
    def store_a_vocab_item(self, item):
        if not self.has_id(item):
            if self.next_free_tag_id == None:
                self.next_free_tag_id = int(self.get_count('tag_'))

            if self.cache and not self.cache_full:
                
                self.tags[('tag_' + item).encode('utf8')] = self.next_free_tag_id
                if len(self.tags) > self.cache_limit: self.cache_full = True
                self.puts.append((('tag_' + item).encode('utf8'), struct.pack("I", self.next_free_tag_id)))
                if len(self.puts) > self.wlimit:
                    self.write_stuff()
                    self.transaction_count = 0

            else:
                #print ('!!')
                #self.txn.put(('tag_' + item).encode('utf8'), str(self.next_free_tag_id).encode('utf8'))
                self.txn.put(('tag_' + item).encode('utf8'), struct.pack("I", self.next_free_tag_id))
                self.txn.commit()
                self.txn = self.env.begin(write=True)


            #self.db.put(('tag_' + item).encode('utf8'), str(self.next_free_tag_id).encode('utf8'))
            self.next_free_tag_id += 1


            #print ('store', item)

    #
    def store_blob(self, blob, blob_idx):
        #print (('blob_' + str(blob_idx)).encode('utf8'))
        if isinstance(blob_idx, int):
            blob_idx = str(blob_idx).encode('utf8')
        elif isinstance(blob_idx, str):
            blob_idx = blob_idx.encode('utf8')

            

        self.puts.append((('blob_'.encode('utf8') + blob_idx), blob))
        self.transaction_count += 1
        if self.transaction_count > self.wlimit:
            self.write_stuff()
            self.transaction_count = 0

        return blob_idx

    #
    def get_blob(self, idx):
        #print (self.txn.get(('blob_' + str(idx)).encode('utf8')))
        self.blob = self.rtxn.get(('blob_' + str(idx)).encode('utf8'), default=None)
        #print (self.blob)
        return self.blob

    #
    def finish_indexing(self):
        pass
        #self.write_stuff()
        #self.close()

    def get_count(self, pref):
        counter = 0

        if isinstance(pref, str):
            pref = pref.encode('utf8')
        cursor = self.txn.cursor()
        if not cursor.set_range(pref):
            return b'0'

        for key, value in cursor:
            if key.startswith(pref):
                counter += 1
        return str(counter).encode('utf8')
