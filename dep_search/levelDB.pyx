# cython: language_level=3
# distutils: language = c++

from DB import BaseDB
import plyvel
from dep_search cimport py_tree


class LevelDB(BaseDB):

    #
    def __init__(self, name):
        super().__init__(name)
        self.s=py_tree.Py_Tree()
        self.name = name
        self.blob = None

    #
    def open(self):
        #check if pickle exists
        self.db = plyvel.DB(self.name + '/leveldb/', create_if_missing=True) 

    #
    def close(self):
        self.db.close()

    #
    def add_to_idx(self, comments, sent):
        # get set ids
        val = self.s.set_id_list_from_conllu(sent, comments, self)
        idx = self.get_count('sets_')
        self.db.put('sets_' + idx, str(val))
        return idx

    #
    def has_id(self, idx):
        try:
            self.db.get('tag_' + idx)
            return True
        except:
            return False
    #
    def get_id_for(self, idx):
        return self.db.get('tag_' + idx)

    #
    def store_a_vocab_item(self, item):
        if not self.has_id(item):
            self.db.put(item, self.get_count('tag_'))

    #
    def store_blob(self, blob, blob_idx):
        self.db.put('blob_' + blob_idx, blob)
        return blob_idx

    #
    def get_blob(self, idx):
        self.blob = self.db.get('blob_' + idx)
        return self.blob

    #
    def finish_indexing(self):
        self.close()

    def get_count(self, pref):
        counter = 0
        for key, value in self.db.iterator(prefix=pref):
            counter += 1
        return counter
