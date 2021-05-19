from libc.stdint cimport uint16_t, uint32_t
from libcpp cimport bool
import zstandard

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


 
cdef extern from "tree_lmdb.h":
    cdef cppclass Tree:
        uint16_t zipped_tree_text_length
        void deserialize(void *serialized_data)
        char *zipped_tree_text
        int fill_sets(void **set_pointers, uint32_t *indices, unsigned char *set_types, unsigned char *optional, unsigned int count)


cdef class Py_Tree:
    cdef Tree *thisptr
    cdef bytes comp_dict
    cdef int fill_sets(self, void **set_pointers, uint32_t *indices, unsigned char *types, unsigned char *optional, int size)
