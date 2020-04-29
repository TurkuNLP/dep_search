# cython: language_level=3
# distutils: language = c++
from DB import BaseDB
import lmdb
cimport py_tree
import os
import copy

class DB(BaseDB):

    #
    def __init__(self, name, cache=False):
        super().__init__(name)
        self.s=py_tree.Py_Tree()
        self.name = name
        self.blob = None
        self.next_free_tag_id = None
        self.cache=cache
    #
    def open(self, foldername='/lmdb/'):
        #check if pickle exists
        try:
            os.mkdir(self.name)
        except:
            pass

        self.env = lmdb.open(self.name + foldername, max_dbs=2, map_size=10485760*1000)
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
                self.tags[key] = int(value)
                vals.append(int(value))
        try:
            self.next_free_tag_id = max(vals) + 1
        except:
            self.next_free_tag_id = 0

    #
    def close(self):
        self.env.close()

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
            return 'tag_'.encode('utf8') + idx.encode('utf8') in self.tags.keys()
        else:
            idx = idx.encode('utf8')
            #print (self.txn.get(b'tag_' + idx) != None)
            return self.txn.get(b'tag_' + idx) != None
    #

    def get_id_for(self, idx):
        if self.cache:
            return self.tags[('tag_' + idx).encode('utf8')]
        else:
            #print (idx, int(self.txn.get(('tag_' + idx).encode('utf8'))))
            return int(self.txn.get(('tag_' + idx).encode('utf8')))
    
    def store_a_vocab_item(self, item):
        if not self.has_id(item):
            if self.next_free_tag_id == None:
                self.next_free_tag_id = int(self.get_count('tag_'))

            if self.cache:
                self.tags[('tag_' + item).encode('utf8')] = self.next_free_tag_id

            self.txn.put(('tag_' + item).encode('utf8'), str(self.next_free_tag_id).encode('utf8'))
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

            

        self.txn.put(('blob_'.encode('utf8') + blob_idx), blob)
        self.txn.commit()
        self.txn = self.env.begin(write=True)

        return blob_idx

    #
    def get_blob(self, idx):
        #print (self.txn.get(('blob_' + str(idx)).encode('utf8')))
        self.blob = self.rtxn.get(('blob_' + str(idx)).encode('utf8'), default=None)
        #print (self.blob)
        return self.blob

    #
    def finish_indexing(self):
        self.close()

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
