# cython: language_level=3
# distutils: language = c++
from dep_search.DB import BaseDB
import plyvel
from dep_search cimport py_tree
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
        self.sets_count = None
        self.cache=cache
    #
    def open(self, foldername='/leveldb/'):
        #check if pickle exists
        try:
            os.mkdir(self.name)
        except:
            pass

        self.db = plyvel.DB(self.name + foldername, create_if_missing=True) 
        if self.cache:
            self.load_tags()


    def load_tags(self):
        self.tags = {}
        vals = []
        for key, value in self.db.iterator(prefix=b'tag_'):
            self.tags[key] = int(value)
            vals.append(int(value))
        try:
            self.next_free_tag_id = max(vals) + 1
        except:
            self.next_free_tag_id = 0

    #
    def close(self):
        self.db.close()

    #
    def add_to_idx(self, comments, sent):
        # get set ids
        val = self.s.set_id_list_from_conllu(sent, comments, self)
        if self.sets_count == None:
            idx = self.get_count('sets_'.encode('utf8'))
        else:
            idx = str(self.sets_count + 1)
            self.sets_count += 1

        self.db.put('sets_'.encode('utf8') + idx, str(val).encode('utf8'))
        return idx

    #
    def has_id(self, idx):
        if self.cache:
            return 'tag_'.encode('utf8') + idx.encode('utf8') in self.tags.keys()
        else:
            return self.db.get(('tag_' + idx).encode('utf8')) != None
    #
    def get_id_for(self, idx):
        if self.cache:
            return self.tags[('tag_' + idx).encode('utf8')]
        else:
            return int(self.db.get(('tag_' + idx).encode('utf8')))

    #
    def store_a_vocab_item(self, item):
        if not self.has_id(item):
            if self.next_free_tag_id == None:
                self.next_free_tag_id = int(self.get_count('tag_'))

            if self.cache:
                self.tags[('tag_' + item).encode('utf8')] = self.next_free_tag_id
            self.db.put(('tag_' + item).encode('utf8'), str(self.next_free_tag_id).encode('utf8'))
            self.next_free_tag_id += 1

    #
    def store_blob(self, blob, blob_idx):
        #print (('blob_' + str(blob_idx)).encode('utf8'))
        if isinstance(blob_idx, int):
            blob_idx = str(blob_idx).encode('utf8')
        elif isinstance(blob_idx, str):
            blob_idx = blob_idx.encode('utf8')

            

        self.db.put(('blob_'.encode('utf8') + blob_idx), blob)
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

        for key, value in self.db.iterator(prefix=pref):
            counter += 1
        return str(counter).encode('utf8')
