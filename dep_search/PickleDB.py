# cython: language_level=3
# distutils: language = c++
import pickle
import os
#cimport py_tree

class BaseDB:

    def __init__(self, name):
        self.name = name

    def open(self):
        pass

    def close(self):
        pass

    def store_blob(self, blob):
        pass

    def get_blob(self, idx):
        pass

    def get_id_for(self, idx):
        pass

    def store_a_vocab_item(self, item):
        pass

    def finish_indexing(self):
        pass


class DB(BaseDB):

    def __init__(self, name):
        super().__init__(name)
        self.idx_data = {}
        self.blob_data = {}
        self.p_data = {}
        #self.s=py_tree.Py_Tree()
        self.dynamic=False

    def set_dynamic_setids(self, xx):
        self.dynamic=xx

    def open(self):
        #check if pickle exists
        if os.path.exists(self.name+'/db.pickle'):
            inf = open(self.name+'/db.pickle','rb')
            self.idx_data, self.blob_data, self.p_data = pickle.load(inf)
            inf.close()
    
    def close(self):
        outf = open(self.name + '/db.pickle','wb')
        pickle.dump([self.idx_data, self.blob_data, self.p_data], outf)
        outf.close()

    def add_to_idx(self, comments, sent):
        # get set ids
        val = self.s.set_id_list_from_conllu(sent, comments, self)
        idx = len(self.p_data)
        self.p_data[idx] = val
        return idx

    def has_id(self, idx):
        if self.dynamic: return True
        return idx in self.idx_data.keys()

    def get_id_for(self, idx):
        if self.dynamic and not idx in self.idx_data.keys():
            self.store_a_vocab_item(idx)
        return self.idx_data[idx]

    def store_a_vocab_item(self, item):
        if item not in self.idx_data.keys():
            self.idx_data[item] = len(self.idx_data)

    def store_blob(self, blob, blob_idx):
        self.blob_data[blob_idx] = blob
        return blob_idx

    def get_blob(self, idx):
        return self.blob_data[idx]

    def finish_indexing(self):
        self.close()
        pass
