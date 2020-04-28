# cython: language_level=3
# distutils: language = c++
from DB import BaseDB
import lmdb
from dep_search cimport py_tree
import os
import copy
from kyotocabinet import *

class DB(BaseDB):

    #
    def __init__(self, name):
        super().__init__(name)
        self.s=py_tree.Py_Tree()
        self.name = name
        self.blob = None
        self.next_free_tag_id = None

    #
    def open(self, foldername='/kcdb/'):
        #check if pickle exists
        try:
            os.mkdir(self.name)
        except:
            pass

        self.db = DB(self.name + foldername, create_if_missing=True) 
        self.db.open(self.name + '/blobs.kc', DB.OWRITER | DB.OCREATE)
    #
    def close(self):
        self.db.close()

    #
    def add_to_idx(self, comments, sent):
        # get set ids
        val = self.s.set_id_list_from_conllu(sent, comments, self)
        idx = self.get_count('sets_'.encode('utf8'))
        self.db.set('sets_'.encode('utf8') + idx, str(val).encode('utf8'))
        return idx

    #
    def has_id(self, idx):
        return self.db.get(('tag_' + idx).encode('utf8')) != None
    #
    def get_id_for(self, idx):
        return int(self.db.get(('tag_' + idx).encode('utf8')))

    #
    def store_a_vocab_item(self, item):
        if not self.has_id(item):
            #self.db.set(('tag_' + item).encode('utf8'), self.get_count('tag_'))
            if self.next_free_tag_id == None:
                self.next_free_tag_id = int(self.get_count('tag_'))

            self.db.set(('tag_' + item).encode('utf8'), str(self.next_free_tag_id).encode('utf8'))
            self.next_free_tag_id += 1


    #
    def store_blob(self, blob, blob_idx):
        #print (('blob_' + str(blob_idx)).encode('utf8'))
        if isinstance(blob_idx, int):
            blob_idx = str(blob_idx).encode('utf8')
        elif isinstance(blob_idx, str):
            blob_idx = blob_idx.encode('utf8')

            

        self.db.set(('blob_'.encode('utf8') + blob_idx), blob)
        return blob_idx

    #
    def get_blob(self, idx):
        #print (self.db.get(('blob_' + str(idx)).encode('utf8')))
        self.blob = self.db.get(('blob_' + str(idx)).encode('utf8'))
        return self.blob

    #
    def finish_indexing(self):
        self.close()

    def get_count(self, pref):
        counter = 0
        if isinstance(pref, str):
            pref = pref.encode('utf8')

        for key in self.db:
            if key.startswith(pref):
                counter +=1
        return str(counter).encode('utf8')

