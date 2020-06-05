from libcpp cimport bool
#from db_util cimport DB
from dep_search.setlib.pytset cimport PyTSet, PyTSetArray
from libc.stdlib cimport malloc
from libc.stdint cimport uint32_t, uint16_t
import sys
from collections import defaultdict
from dep_search.dict_lzw import compress, decompress

cdef extern from "tset.h" namespace "tset":
    cdef cppclass TSet:
        int tree_length
        int array_len
        TSet(int) except +
        void intersection_update(TSet *)
        void minus_update(TSet *)
        void union_update(TSet *)
        void add_item(int)
        bool has_item(int)
        void fill_ones()
        bool is_empty()
        void print_set()
        void erase()
        void set_length(int tree_length)
        void complement()
        void copy(TSet *other)

    cdef cppclass TSetArray:
        int tree_length
        int array_len
        TSetArray(int length) except +
        void intersection_update(TSetArray *other)
        void union_update(TSetArray *other)
        void minus_update(TSetArray *other)
        void erase()
        void get_set(int index, TSet *result)
        void deserialize(const void *data, int size)
        void print_array()
        void set_length(int tree_length)
        void copy(TSetArray *other)
        void filter_direction(bool direction)
        void make_lin(int window)
        void make_lin_2(int window, int begin)

        void extend_subtrees(TSetArray* other)
        void add_arch(int a, int b)
        TSet get_all_children(int id, TSet * other)

cdef extern from "tree_lmdb.h":
    cdef cppclass Tree:
        uint16_t zipped_tree_text_length
        void deserialize(void *serialized_data)
        char *zipped_tree_text
        int fill_sets(void **set_pointers, uint32_t *indices, unsigned char *set_types, unsigned char *optional, unsigned int count)


cdef extern from "query_functions.h":
    void pairing(TSet *index_set, TSet *other_set, TSetArray *mapping, bool negated)


# This is query object in query.py
cdef class Search:  # base class for all searches
    cdef void **sets  #Pointers to stuff coming from the DB: array 1 and set 2 (we don't need 0)
    cdef int *set_types
    cdef set_size
    cdef int ops
    cdef bool started

    cdef bytes blob

    cdef Tree* tree

    cdef uint32_t *set_ids
    cdef unsigned char* types
    cdef unsigned char *optional

    #Declared here, overridden in the generated query code
    cdef TSet *exec_search(self):
        pass

    cdef void initialize(self):
        self.blob = None
        pass
    #End of overriden declarations
    
    def set_db(self, db):

        args = self.query_fields
        qobj = self

        just_all_set_ids = []
        optional = []
        types = []

        c_args_s = []
        s_args_s = []
        c_args_m = []
        s_args_m = []

        solr_args = []

        or_groups = defaultdict(list)

        for arg in args:
            compulsory = False
            it_is_set = True
            or_group_id = None

            if arg.startswith('!'):
                compulsory = True    
                narg = arg[1:]
            else:
                narg = arg

            if narg.startswith('org_'):
                or_group_id = int(narg.split('_')[1])
                narg = narg[6:]

            ##print >> sys.stderr, "narg:", narg
            optional.append(not compulsory)

            oarg = 0

            if narg.startswith('dep_a'):
                if db.has_id(u'd_' + narg[6:]):
                    oarg = db.get_id_for(u'd_' + narg[6:])
                it_is_set = False

            if narg.startswith('gov_a'):
                if db.has_id(u'g_' + narg[6:]):
                    oarg = db.get_id_for(u'g_' + narg[6:])
                it_is_set = False

            if narg.startswith('lemma_s'):
                if db.has_id(u'l_' + narg[8:]):
                    oarg = db.get_id_for(u'l_' + narg[8:])
                it_is_set = True
            if narg.startswith('token_s'):
                if db.has_id(u'f_' + narg[8:]):
                    oarg = db.get_id_for(u'f_' + narg[8:])
                it_is_set = True

            #Here! Add so that if not found as tag, try tokens
            if narg.startswith('tag_s'):
                it_is_set = True
                if db.has_id(u'' + narg[6:]):
                #if narg[6:] in set_dict.keys():
                    oarg = db.get_id_for(u'' + narg[6:])
                    solr_args.append(arg)
                    if or_group_id != None:
                        or_groups[or_group_id].append(arg[6:])
                else:
                    if db.has_id(u'p_' + narg[6:]):
                    #if 'p_' + narg[6:] in set_dict.keys():
                        oarg = db.get_id_for(u'p_' + narg[6:])
                        solr_args.append(arg)
                        if or_group_id != None:
                            or_groups[or_group_id].append(arg[6:])

                    else:
                        try:
                            if compulsory:
                                solr_args.append('!token_s_' + narg[6:])
                            else:
                                solr_args.append('token_s_' + narg[6:])
                                if or_group_id != None:
                                    or_groups[or_group_id].append('token_s_' + narg[6:])##



                            if db.has_id(u'f_' + narg[6:]):
                                #oarg = db.get_id_for(u'f_' + narg[6:])
                                oarg = db.get_id_for(u'f_' + narg[6:])

                        except:
                            pass#import pdb;pdb.set_trace()
            else:
                if not arg.startswith('org_'):
                    solr_args.append(arg)
                else:
                    solr_args.append(arg[6:])
                    if or_group_id != None:
                        or_groups[or_group_id].append(arg[6:])


            types.append(not it_is_set)

            ##print compulsory
            ##print it_is_set
            just_all_set_ids.append(oarg)
            if compulsory:
                if it_is_set:
                    c_args_s.append(oarg)
                else:
                    c_args_m.append(oarg)
            else:
                if it_is_set:
                    s_args_s.append(oarg)
                else:
                    s_args_m.append(oarg)


        for item in qobj.org_has_all:
            #
            or_groups[item].append('dep_a_anyrel')


        together = c_args_s + c_args_m

        counts = []# [set_count[x] for x in together]
        min_c = 0#min(counts)
        rarest = 0#together[0]#counts.index(min_c)]
        ##print >> sys.stderr, 'optional:', optional
        ##print >> sys.stderr, 'types:', types
        solr_or_groups = []

        self.set_db_options(just_all_set_ids, types, optional)
        #return rarest, c_args_s, s_args_s, c_args_m, s_args_m, just_all_set_ids, types, optional, solr_args, or_groups


    def map_set_id(self, db):

        args = self.query_fields
        qobj = self

        just_all_set_ids = []
        optional = []
        types = []

        c_args_s = []
        s_args_s = []
        c_args_m = []
        s_args_m = []

        solr_args = []

        or_groups = defaultdict(list)

        for arg in args:
            compulsory = False
            it_is_set = True
            or_group_id = None

            if arg.startswith('!'):
                compulsory = True
                narg = arg[1:]
            else:
                narg = arg

            if narg.startswith('org_'):
                or_group_id = int(narg.split('_')[1])
                narg = narg[6:]

            ##print >> sys.stderr, "narg:", narg
            optional.append(not compulsory)

            oarg = 0

            if narg.startswith('dep_a'):
                if db.has_id(u'd_' + narg[6:]):
                    oarg = db.get_id_for(u'd_' + narg[6:])
                it_is_set = False

            if narg.startswith('gov_a'):
                if db.has_id(u'g_' + narg[6:]):
                    oarg = db.get_id_for(u'g_' + narg[6:])
                it_is_set = False

            if narg.startswith('lemma_s'):
                if db.has_id(u'l_' + narg[8:]):
                    oarg = db.get_id_for(u'l_' + narg[8:])
                it_is_set = True
            if narg.startswith('token_s'):
                if db.has_id(u'f_' + narg[8:]):
                    oarg = db.get_id_for(u'f_' + narg[8:])
                it_is_set = True

            #Here! Add so that if not found as tag, try tokens
            if narg.startswith('tag_s'):
                it_is_set = True
                if db.has_id(u'' + narg[6:]):
                #if narg[6:] in set_dict.keys():
                    oarg = db.get_id_for(u'' + narg[6:])
                    solr_args.append(arg)
                    if or_group_id != None:
                        or_groups[or_group_id].append(arg[6:])
                else:
                    if db.has_id(u'p_' + narg[6:]):
                    #if 'p_' + narg[6:] in set_dict.keys():
                        oarg = db.get_id_for(u'p_' + narg[6:])
                        solr_args.append(arg)
                        if or_group_id != None:
                            or_groups[or_group_id].append(arg[6:])

                    else:
                        try:
                            if compulsory:
                                solr_args.append('!token_s_' + narg[6:])
                            else:
                                solr_args.append('token_s_' + narg[6:])
                                if or_group_id != None:
                                    or_groups[or_group_id].append('token_s_' + narg[6:])


                            if db.has_id(u'f_' + narg[6:]):
                                #oarg = db.get_id_for(u'f_' + narg[6:])
                                oarg = db.get_id_for(u'f_' + narg[6:])

                        except:
                            pass#import pdb;pdb.set_trace()
            else:
                if not arg.startswith('org_'):
                    solr_args.append(arg)
                else:
                    solr_args.append(arg[6:])
                    if or_group_id != None:
                        or_groups[or_group_id].append(arg[6:])


            types.append(not it_is_set)

            ##print compulsory
            ##print it_is_set
            just_all_set_ids.append(oarg)
            if compulsory:
                if it_is_set:
                    c_args_s.append(oarg)
                else:
                    c_args_m.append(oarg)
            else:
                if it_is_set:
                    s_args_s.append(oarg)
                else:
                    s_args_m.append(oarg)


        for item in qobj.org_has_all:
            #
            or_groups[item].append('dep_a_anyrel')


        together = c_args_s + c_args_m

        counts = []# [set_count[x] for x in together]
        min_c = 0#min(counts)
        rarest = 0#together[0]#counts.index(min_c)]
        ##print >> sys.stderr, 'optional:', optional
        ##print >> sys.stderr, 'types:', types
        solr_or_groups = []
        return rarest, c_args_s, s_args_s, c_args_m, s_args_m, just_all_set_ids, types, optional, solr_args, or_groups

    cpdef fill_from_blob(self, char *blob):


        #print ('fill',blob)
        #self.blob = blob
        #deserialize
        self.tree.deserialize(<void*>blob)
        #self.tree.fill_sets(self.sets, self.set_ids, <unsigned char *>self.types, self.optional, self.set_size)

        #void **set_pointers, uint32_t *indices, unsigned char *types, unsigned char *optional, int size
        #Tree::fill_sets(void **set_pointers, uint32_t *indices, unsigned char *set_types, unsigned char *optional, unsigned int count)
        return self.tree.fill_sets(self.sets, self.set_ids, <unsigned char *>self.types, self.optional, self.set_size)

    def set_db_options(self, p_set_ids, p_types, p_optional):

        cdef uint32_t *set_ids = <uint32_t *>malloc(len(p_set_ids) * sizeof(uint32_t))
        for i, s in enumerate(p_set_ids):
            set_ids[i] = s
        self.set_ids = set_ids

        cdef unsigned char *types = <unsigned char *>malloc(len(p_set_ids) * sizeof(unsigned char))
        self.types = types
        ##print >> sys.stderr, "<types>"
        for i, s in enumerate(p_types):
            if s:
                types[i] = <char>2
                ##print >> sys.stderr, i, s, 2
            else:
                types[i] = <char>1
                ##print >> sys.stderr, i, s, 1
        ##print >> sys.stderr, "</types>"

        cdef unsigned char *optional = <unsigned char *>malloc(len(p_optional) * sizeof(unsigned char))
        for i, s in enumerate(p_optional):
            if s:
                optional[i] = <char>1
            else:
                optional[i] = <char>0
        self.optional = optional

        self.set_size = len(p_set_ids)
        self.started = False

    def set_tree_id(self, uint32_t tree_id, db):
        blob = db.get_blob(tree_id)
        has_sets = self.fill_from_blob(<char*>blob)

    def check_tree_id(self, uint32_t tree_id, db):

        #db.set_tree_to_id(tree_id)
        #db.fill_sets(self.sets, self.set_ids, <unsigned char *>self.types, self.optional, self.set_size)
        blob = db.get_blob(tree_id)

        #print ('!!!', self.blob)
        has_sets = self.fill_from_blob(<char*>blob)

        if has_sets==1:
            return set()
        self.initialize()
        result=self.exec_search()
        #print (result)
        result_set = set()
        #result.print_set()
        #Really + 1 ?  xxx check
        for x in range(result.tree_length + 1):
            if result.has_item(x):
                result_set.add(x)

        return result_set

    '''
    def old_check_tree_id(self, uint32_t tree_id, DB db):

        #db.set_tree_to_id(tree_id)
        has_sets = db.fill_sets(self.sets, self.set_ids, <unsigned char *>self.types, self.optional, self.set_size)
        if has_sets==1:
            return set()

        self.initialize()
        result=self.exec_search()
        result_set = set()

        #Really + 1 ?  xxx check
        for x in range(result.tree_length + 1):
            if result.has_item(x):
                result_set.add(x)

        return result_set
    '''

    cpdef check_blob(self, char *blob):
        has_sets = self.fill_from_blob(blob)

        if has_sets==1:
            return set()

        self.initialize()
        result=self.exec_search()
        result_set = set()

        #Really + 1 ?  xxx check
        for x in range(result.tree_length + 1):
            if result.has_item(x):
                result_set.add(x)

        return result_set        

    '''
    def next_result(self, DB db):
        cdef int size=len(self.query_fields)
        cdef PyTSet py_result=PyTSet(0)
        cdef TSet *result
        cdef int graph_id
        cdef int rows=0
        cdef uint32_t * tree_id

        if True:#self.started:

            err=db.get_next_fitting_tree()
            if err or db.finished():
                #print >> sys.stderr, "No next result err=",err," db finished=", db.finished()
                return -1

        else:
            self.started = True

        db.fill_sets(self.sets, self.set_ids, <unsigned char *>self.types, self.optional, self.set_size)
        self.initialize()
        result=self.exec_search()

        result_set = set()

        #Really + 1 ?  xxx check
        for x in range(result.tree_length + 1):
            if result.has_item(x):
                result_set.add(x)

        return result_set
    '''

    def get_tree_comms(self, comp_dict):
        #print ()
        cdef char * tree_text_data=self.tree.zipped_tree_text

        #print ('zzz',self.blob)
        #print (self.tree.zipped_tree_text_length)
        #print (tree_text_data)


        result = [l for l in decompress(tree_text_data[:self.tree.zipped_tree_text_length], comp_dict).decode('utf8').split(u'\n') if l.startswith(u'#')]
        return '\n'.join(result)


    def get_tree_text(self, comp_dict):
        cdef char * tree_text_data=self.tree.zipped_tree_text

        #print ('ebens', self.blob)
        #print (self.tree.zipped_tree_text_length)
        #print (tree_text_data)

        result = [l for l in decompress(tree_text_data[:self.tree.zipped_tree_text_length], comp_dict).decode('utf8').split(u'\n') if not l.startswith(u'#')]
        return '\n'.join(result)




