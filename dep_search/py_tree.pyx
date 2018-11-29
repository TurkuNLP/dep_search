# distutils: language = c++
# distutils: libraries = lmdb
# distutils: sources = tree_lmdb.cpp setlib/tset.cpp
#clib  setlib/setlib
import struct
import json
import zlib
#import setlib.pytset as pytset
from setlib.pytset cimport PyTSet, PyTSetArray
from libcpp cimport bool

ID,FORM,LEMMA,UPOS,XPOS,FEAT,HEAD,DEPREL,DEPS,MISC=range(10)

cdef extern from "tset.h" namespace "tset":
    cdef cppclass TSet:
        int tree_length
        TSet(int) except +
        void intersection_update(TSet *)
        void minus_update(TSet *)
        void union_update(TSet *)
        void add_item(int)
        bool has_item(int)
        void start_iteration()
        bool next_item(TSet *)
        char * get_data_as_char(int *)
        void deserialize(const void *)
        void erase()
        void set_length(int tree_length)
        void print_set()
        void copy(TSet *other)
    cdef cppclass TSetArray:
        void deserialize(const void *data, int size)
        void erase()
        void set_length(int tree_length)
        void print_array()
        void union_update(TSetArray *other)
        void intersection_update(TSetArray *other)
        void copy(TSetArray *other)




cdef class Py_Tree:

    def __cinit__(self):
        self.thisptr=new Tree()

    def __dealloc__(self):
        del self.thisptr

    def __init__(self):
        pass

    def deserialize(self, char *binary_blob):
        self.thisptr.deserialize(<void *>binary_blob)
        #print self.thisptr.zipped_tree_text_length

    def serialize_from_conllu(self, lines, comments, db_store):
        #this we need to save
        tree_data={"comments":comments,
                   "tokens":list(l[FORM] for l in lines),
                   "lemmas":list(l[LEMMA] for l in lines),
                   "misc":list(l[MISC] for l in lines)}

        #print lines
        #I know, will fix
        tree_text = '\n'.join(comments) + '\n' + u'\n'.join([u'\t'.join(l) for l in lines])
        #print tree_text
        tree_data_gz=zlib.compress(tree_text.encode('utf8'))  #json.dumps(tree_data)#json.dumps(tree_data)#zlib.compress(json.dumps(tree_data))
        
        #Sets for the UPOS and FEAT
        token_sets={} #Key: set number, Value: Python set() of integers
        arrays={} #Key: relation number, Value: Python set() of (from,to) integer pairs
        for t_idx,line in enumerate(lines):
            for tag in [u"p_"+line[UPOS],u"f_"+line[FORM],u"l_"+line[LEMMA]]+line[FEAT].split(u"|"):
                if tag[2:]!=u"_":

                    has_lc_ver = False
                    if tag.startswith('f_') and tag.lower() != tag:
                        has_lc_ver = True

                    #Add tag into the db
                    db_store.store_a_vocab_item(tag)
                    set_id = db_store.get_id_for(tag)
                    token_sets.setdefault(set_id,set()).add(t_idx)

                    if has_lc_ver:
                    
                        db_store.store_a_vocab_item(tag.lower() + '_lc')
                        set_id = db_store.get_id_for(tag.lower() + '_lc')
                        token_sets.setdefault(set_id,set()).add(t_idx)

            if line[DEPREL]!=u"_":
                for gov,dep,dtype in [(int(line[HEAD])-1,t_idx, line[DEPREL])]:
                    if gov==-1:
                        continue
                    #TODO: DEPS field

                    db_store.store_a_vocab_item(u"g_"+dtype)
                    set_id_g = db_store.get_id_for(u"g_"+dtype)
                    #set_id_g=set_dict.setdefault(u"g_"+dtype,len(set_dict))
                    arrays.setdefault(set_id_g,set()).add((gov,dep))

                    db_store.store_a_vocab_item(u"g_anyrel")
                    set_id_g = db_store.get_id_for(u"g_anyrel")
                    #set_id_g=set_dict.setdefault(u"g_anyrel",len(set_dict))
                    arrays.setdefault(set_id_g,set()).add((gov,dep))

                    db_store.store_a_vocab_item(u"d_"+dtype)
                    set_id_d = db_store.get_id_for(u"d_"+dtype)
                    #set_id_d=set_dict.setdefault(u"d_"+dtype,len(set_dict))
                    arrays.setdefault(set_id_d,set()).add((dep,gov))

                    db_store.store_a_vocab_item(u"d_anyrel")
                    set_id_d = db_store.get_id_for(u"d_anyrel")
                    #set_id_d=set_dict.setdefault(u"d_anyrel",len(set_dict))
                    arrays.setdefault(set_id_d,set()).add((dep,gov))


            #The Second layer
            if line[-2]!=u"_":
                dep = t_idx
                for xx in line[DEPS].split('|'):

                    #
                    govs = xx.split(':')[0].split('.')
                    for sgov in govs:

                        gov = int(sgov) - 1
                        dtype = ':'.join(xx.split(':')[1:])
                        if gov == -1:
                            continue

                        db_store.store_a_vocab_item(u"g_"+dtype)
                        set_id_g = db_store.get_id_for(u"g_"+dtype)
                        #set_id_g=set_dict.setdefault(u"g_"+dtype,len(set_dict))
                        arrays.setdefault(set_id_g,set()).add((gov,t_idx))

                        db_store.store_a_vocab_item(u"g_anyrel")
                        set_id_g = db_store.get_id_for(u"g_anyrel")
                        #set_id_g=set_dict.setdefault(u"g_anyrel",len(set_dict))
                        arrays.setdefault(set_id_g,set()).add((gov,t_idx))

                        db_store.store_a_vocab_item(u"d_"+dtype)
                        set_id_d = db_store.get_id_for(u"d_"+dtype)
                        #set_id_d=set_dict.setdefault(u"d_"+dtype,len(set_dict))
                        arrays.setdefault(set_id_d,set()).add((dep,gov))

                        db_store.store_a_vocab_item(u"d_anyrel")
                        set_id_d = db_store.get_id_for(u"d_anyrel")
                        #set_id_d=set_dict.setdefault(u"d_anyrel",len(set_dict))
                        arrays.setdefault(set_id_d,set()).add((dep,gov))




        #Produces the packed map data
        map_lengths=[]
        map_data=b""
        for map_num,pairs in sorted(arrays.iteritems()):
            pairs_packed=b"".join(struct.pack("=HH",*pair) for pair in sorted(pairs))
            map_lengths.append(len(pairs_packed))
            map_data+=pairs_packed

        #Produces the packed set data
        set_data=b""
        for set_num, indices in sorted(token_sets.iteritems()):

            #s=pytset.PyTSet(len(lines),indices)
            s=PyTSet(len(lines),indices)


            bs=s.tobytes(include_size=False)
#            assert len(bs)/8==len(lines)/8+1, (len(bs)/8,len(lines)/8+1)
            set_data+=bs
        #treelen  16
        #set_count 16
        #map_count 16
        #set_indices 32
        #map_indices  32
        #map_lengths 16
        #set_data  8
        #map_data 8
        #zip_len 16
        #zip_data 8

        #print "set_count",len(token_sets)
        #print "map_count",len(arrays)
        #print "set_data_len",len(set_data)
        #print "map_data_len",len(map_data)
        #print "zip_data_len",len(tree_data_gz)


        #=HHH106I38I38H1060s656sH267s

        blob="=HHH%(set_count)dI%(map_count)dI%(map_count)dH%(set_data_len)ds%(map_data_len)dsH%(zip_data_len)ds"%\
            {"set_count":len(token_sets),
             "map_count":len(arrays),
             "set_data_len":len(set_data),
             "map_data_len":len(map_data),
             "zip_data_len":len(tree_data_gz)}
        args=[len(lines),len(token_sets),len(arrays)]+\
              sorted(token_sets)+\
              sorted(arrays)+\
              map_lengths+\
              [set_data,map_data,len(tree_data_gz),tree_data_gz]

        #print '<ARGS>'
        #print args
        #print '</ARGS>'

        serialized=struct.pack(blob,*args)
        #print "serializer:", len(lines),len(token_sets),len(arrays), len(set_data), len(map_data), len(tree_data_gz), map_lengths, sorted(token_sets)
        return serialized, blob #The binary blob of the sentence

    cdef int fill_sets(self, void **set_pointers, uint32_t *indices, unsigned char *types, unsigned char *optional, int size):
        tree  = self.thisptr
        return tree.fill_sets(set_pointers, indices, types, optional, size)

    def set_id_list_from_conllu(self, lines, comments, db_store):
        #this we need to save
        tree_data={"comments":comments,
                   "tokens":list(l[FORM] for l in lines),
                   "lemmas":list(l[LEMMA] for l in lines),
                   "misc":list(l[MISC] for l in lines)}

        set_id_set = set()

        #print lines
        #I know, will fix
        tree_text = '\n'.join(comments) + '\n' + u'\n'.join([u'\t'.join(l) for l in lines])
        #print tree_text
        tree_data_gz=zlib.compress(tree_text.encode('utf8'))  #json.dumps(tree_data)#json.dumps(tree_data)#zlib.compress(json.dumps(tree_data))
        
        #Sets for the UPOS and FEAT
        token_sets={} #Key: set number, Value: Python set() of integers
        arrays={} #Key: relation number, Value: Python set() of (from,to) integer pairs
        for t_idx,line in enumerate(lines):
            for tag in [u"p_"+line[UPOS],u"f_"+line[FORM],u"l_"+line[LEMMA]]+line[FEAT].split(u"|"):
                if tag[2:]!=u"_":

                    has_lc_ver = False
                    if tag.startswith('f_') and tag.lower() != tag:
                        has_lc_ver = True

                    #Add tag into the db
                    db_store.store_a_vocab_item(tag)
                    set_id = db_store.get_id_for(tag)
                    token_sets.setdefault(set_id,set()).add(t_idx)

                    if has_lc_ver:
                    
                        #db_store.store_a_vocab_item(tag.lower() + '_lc')
                        set_id = db_store.get_id_for(tag.lower() + '_lc')
                        set_id_set.add(set_id)
                        token_sets.setdefault(set_id,set()).add(t_idx)

            if line[DEPREL]!=u"_":
                for gov,dep,dtype in [(int(line[HEAD])-1,t_idx, line[DEPREL])]:
                    if gov==-1:
                        continue
                    #TODO: DEPS field

                    #db_store.store_a_vocab_item(u"g_"+dtype)
                    set_id_g = db_store.get_id_for(u"g_"+dtype)
                    set_id_set.add(set_id_g)
                    #set_id_g=set_dict.setdefault(u"g_"+dtype,len(set_dict))
                    arrays.setdefault(set_id_g,set()).add((gov,dep))

                    #db_store.store_a_vocab_item(u"g_anyrel")
                    set_id_g = db_store.get_id_for(u"g_anyrel")
                    set_id_set.add(set_id_g)
                    #set_id_g=set_dict.setdefault(u"g_anyrel",len(set_dict))
                    arrays.setdefault(set_id_g,set()).add((gov,dep))

                    #db_store.store_a_vocab_item(u"d_"+dtype)
                    set_id_d = db_store.get_id_for(u"d_"+dtype)
                    set_id_set.add(set_id_d)
                    #set_id_d=set_dict.setdefault(u"d_"+dtype,len(set_dict))
                    arrays.setdefault(set_id_d,set()).add((dep,gov))

                    #db_store.store_a_vocab_item(u"d_anyrel")
                    set_id_d = db_store.get_id_for(u"d_anyrel")
                    set_id_set.add(set_id_d)
                    #set_id_d=set_dict.setdefault(u"d_anyrel",len(set_dict))
                    arrays.setdefault(set_id_d,set()).add((dep,gov))


            #The Second layer
            if line[-2]!=u"_":
                dep = t_idx
                for xx in line[DEPS].split('|'):

                    #
                    govs = xx.split(':')[0].split('.')
                    for sgov in govs:

                        gov = int(sgov) - 1
                        dtype = ':'.join(xx.split(':')[1:])
                        if gov == -1:
                            continue

                        #db_store.store_a_vocab_item(u"g_"+dtype)
                        set_id_g = db_store.get_id_for(u"g_"+dtype)
                        set_id_set.add(set_id_g)
                        #set_id_g=set_dict.setdefault(u"g_"+dtype,len(set_dict))
                        arrays.setdefault(set_id_g,set()).add((gov,t_idx))

                        #db_store.store_a_vocab_item(u"g_anyrel")
                        set_id_g = db_store.get_id_for(u"g_anyrel")
                        set_id_set.add(set_id_g)
                        ##set_id_g=set_dict.setdefault(u"g_anyrel",len(set_dict))
                        arrays.setdefault(set_id_g,set()).add((gov,t_idx))

                        #db_store.store_a_vocab_item(u"d_"+dtype)
                        set_id_d = db_store.get_id_for(u"d_"+dtype)
                        set_id_set.add(set_id_d)
                        #set_id_d=set_dict.setdefault(u"d_"+dtype,len(set_dict))
                        arrays.setdefault(set_id_d,set()).add((dep,gov))

                        #db_store.store_a_vocab_item(u"d_anyrel")
                        set_id_d = db_store.get_id_for(u"d_anyrel")
                        set_id_set.add(set_id_d)
                        #set_id_d=set_dict.setdefault(u"d_anyrel",len(set_dict))
                        arrays.setdefault(set_id_d,set()).add((dep,gov))

        return set_id_set

    def set_list_from_conllu(self, lines, comments):
        #this we need to save
        tree_data={"comments":comments,
                   "tokens":list(l[FORM] for l in lines),
                   "lemmas":list(l[LEMMA] for l in lines),
                   "misc":list(l[MISC] for l in lines)}

        set_id_set = set()

        #print lines
        #I know, will fix
        tree_text = '\n'.join(comments) + '\n' + u'\n'.join([u'\t'.join(l) for l in lines])
        #print tree_text
        tree_data_gz=zlib.compress(tree_text.encode('utf8'))  #json.dumps(tree_data)#json.dumps(tree_data)#zlib.compress(json.dumps(tree_data))

        #Sets for the UPOS and FEAT
        token_sets={} #Key: set number, Value: Python set() of integers
        arrays={} #Key: relation number, Value: Python set() of (from,to) integer pairs
        for t_idx,line in enumerate(lines):
            for tag in [u"p_"+line[UPOS],u"f_"+line[FORM],u"l_"+line[LEMMA]]+line[FEAT].split(u"|"):
                if tag[2:]!=u"_":

                    has_lc_ver = False
                    if tag.startswith('f_') and tag.lower() != tag:
                        has_lc_ver = True

                    #Add tag into the db
                    set_id_set.add(tag)
                    if has_lc_ver:

                        set_id_set.add(tag.lower() + '_lc')


            if line[DEPREL]!=u"_":
                for gov,dep,dtype in [(int(line[HEAD])-1,t_idx, line[DEPREL])]:
                    if gov==-1:
                        continue
                    #TODO: DEPS field

                    #db_store.store_a_vocab_item(u"g_"+dtype)
                    set_id_set.add("g_"+dtype)
                    set_id_set.add("g_anyrel")
                    set_id_set.add("d_"+dtype)
                    set_id_set.add("d_anyrel")

            #The Second layer
            if line[-2]!=u"_":
                dep = t_idx
                for xx in line[DEPS].split('|'):

                    #
                    govs = xx.split(':')[0].split('.')
                    for sgov in govs:

                        gov = int(sgov) - 1
                        dtype = ':'.join(xx.split(':')[1:])
                        if gov == -1:
                            continue

                        set_id_set.add("g_"+dtype)
                        set_id_set.add("g_anyrel")
                        set_id_set.add("d_"+dtype)
                        set_id_set.add("d_anyrel")

        return set_id_set

