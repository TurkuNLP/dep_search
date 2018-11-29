#include "lmdb.h"
#include <iostream>
#include <stdint.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sstream>
#include "tree_lmdb.h"
#include <stdlib.h>
#include <iomanip>
#include "fetch_lmdb.h"


LMDB_Fetch::LMDB_Fetch(){

    tree = new Tree();
    tree_ids=NULL;
    tree_ids_count=0;
}


/* Initializes the search */
// Returns zero and sets .finished=True if not a single key hit found
// Returns zero and sets .finished=False if found
// Returns nonzero on error
int LMDB_Fetch::begin_search(int len_sets, int len_arrays, uint32_t *lsets, uint32_t *larrays, uint32_t rarest) {

    MDB_val key,val;
    uint32_t k=rarest;
    int err;
    tree_id_pointer = 0;

    key.mv_size=sizeof(k);
    key.mv_data=&k;
    val.mv_size=0;
    val.mv_data=NULL;

    finished=false;
    query_started=false;
    this->rarest = rarest;
    this->sets = lsets; //new uint32_t[len_sets];
    this->arrays= larrays; //new uint32_t[len_arrays];
    this->len_sets=len_sets;
    this->len_arrays=len_arrays;

    // for (int i=0; i<len_sets; i++) {
    // 	sets[i]=lsets[i];
    // }
    // for (int i=0; i<len_arrays; i++) {
    // 	arrays[i]=larrays[i];
    // }

    //std::cerr << "Begin search" << std::endl;
    for (int i=0; i<this->len_sets; i++) {
	//std::cerr << "  set " << this->sets[i] << std::endl;
    }
    for (int i=0; i<this->len_arrays; i++) {
	//std::cerr << "  array " << this->arrays[i] << std::endl;
    }
    //std::cerr << "Rarest " << this->rarest << std::endl;
    
    /*
    err=mdb_cursor_get(k2t_cursor,&key,&val,MDB_SET);
    if (!err) {
	return err; //0
    }
    else if (err==MDB_NOTFOUND) {
	// Not a single instance in the db!
	//std::cerr << "Initial get failed" << std::endl;
	finished=true;
	return 0;
    }
    else {
	report("Cursor_get failed",err);
	return err;
    }*/
}

// Positions the k2t cursor on the next tree for the "rarest" key
// returns 0 and sets .finished=False if found
// returns 0 and sets .finished=True if not found
// returns nonzero on error
int LMDB_Fetch::move_to_next_tree() {
    MDB_val key,val;
    uint32_t k=rarest;
    int err;

    if (finished) {
	return 0;
    }
    
    err=mdb_cursor_get(k2t_cursor,&key,&val,MDB_NEXT_DUP);
    if (!err) {
	return 0;
    }
    else if (err==MDB_NOTFOUND) {
	std::cerr << "Next not found, done" << err << std::endl;
	finished=true;
	return 0;
    }
    else {
	report("Cursor next failed for k2t",err);
	return err;
    }
}



bool LMDB_Fetch::has_id(char *key_data, int key_size) {

    MDB_val key;
    MDB_val value;
    key.mv_size=key_size;
    key.mv_data=(void*)key_data;

    //for (int i=0;i<key_size;i++){ 
    //    std::cerr << ((char*)key_data)[i];
    //}
    //std::cerr << key_size;
    //std::cerr << "\n";

    //Get the count
    int err = mdb_get(txn, db_tk2id, &key, &value);
    if (err) {
	//report("Failed to xget(), that's bad!:",err);
	return false;
    }
    //std::cerr << "This actually worked!" << std::endl;    
    return true;
}


int LMDB_Fetch::get_id_for(char *key_data, int key_size) {

    MDB_val key;
    MDB_val value;
    key.mv_size=key_size;
    key.mv_data=(void*)key_data;

    //for (int i=0;i<key_size;i++){ 
    //    std::cerr << ((char*)key_data)[i];
    //}
    //std::cerr << key_size;
    //std::cerr << "\n";

    //Get the count
    int err = mdb_get(txn, db_tk2id, &key, &value);
    if (err) {
	//report("Failed to xget(), that's bad!:",err);
	return err;
    }
    //std::cerr << "This actually worked!" << std::endl;    
    this->tag_id = (uint32_t*)value.mv_data;
}


uint32_t LMDB_Fetch::get_tag_id(){

return *(this->tag_id);

}


uint32_t LMDB_Fetch::get_count(){

return *(this->count);

}

int LMDB_Fetch::get_count_for(unsigned int q_id) {

    MDB_val key;
    MDB_val value;
    key.mv_size=sizeof(uint32_t);
    key.mv_data=&q_id;

    //Get the count
    int err = mdb_get(txn, db_id2c, &key, &value);
    if (err) {
	report("Failed to get(), that's bad!:",err);
	return err;
    }    
    this->count = (uint32_t*)value.mv_data;
}




//sets tree and tree_id to the next fitting tree, returns 0 and .finished=false
//returns 0 and sets .finished=true if nothing found
//returns nonzero on error
int LMDB_Fetch::get_next_fitting_tree() {
    //this assumes that you ran begin_search() if this is the first call
    //so the k2t cursor is pointing at a tree not seen so far
    MDB_val key,tree_id_val,t_val;
    int err;
    if (query_started){
        move_to_next_tree();
    }
    else {
    query_started=true;
    }

    while (!finished) {
	err=mdb_cursor_get(k2t_cursor,&key,&tree_id_val,MDB_GET_CURRENT);


	//std::cerr << "In get_next_fitting_tree key is now " << *((uint32_t*)key.mv_data) << " and tid " << *((uint32_t*)tree_id_val.mv_data) << std::endl;
	if (err || (*((uint32_t*)key.mv_data)!=rarest)) {
	    //std::cerr << "In get_next_fitting_tree key is " << *((uint32_t*)key.mv_data) << " but rarest is set to " << rarest << std::endl;
	    report("Failed to retrieve from k2t",err);
	    return err;
	}
	//Now tree_id_val holds the tree id of the tree we want, so let's grab it
	err=mdb_cursor_get(tdata_cursor,&tree_id_val,&t_val,MDB_SET_KEY);
	if (err) {
	    report("Failed to retrieve tree from tdata",err);
	    return err;
	}
	//Now t_val points to serialized tree data
	//Does it have all we need?
	if (check_tree(t_val.mv_data)) { //YES!

	    tree_id=*((uint32_t*)tree_id_val.mv_data);
	    //the tree itself is now deserialized in tree, so that should be okay
	    return 0;
	}
	move_to_next_tree();
    }
    //Ran out of trees, ie found nothing
    return 0; //finished is false now, so that is our signal
}

	
	
/* Closes everything */
void LMDB_Fetch::close() {
    mdb_cursor_close(k2t_cursor);
    mdb_cursor_close(tdata_cursor);
    mdb_txn_abort(txn);
    mdb_env_close(mdb_env);
}

/* Opens everything needed */
int LMDB_Fetch::open(const char *name) {
    int err;
    err=mdb_env_create(&mdb_env);
    if (err) {
        report("Failed to create an environment:",err);
        return err;
    }
    err=mdb_env_set_mapsize(mdb_env,1024L*1024L*1024L*1024L); //1TB max DB size
    if (err) {
        report("Failed to set env size:",err);
        return err;
    }
    err=mdb_env_set_maxdbs(mdb_env,6); //to account for the two open databases
    if (err) {
        report("Failed to set maxdbs:",err);
        return err;
    }
    err=mdb_env_open(mdb_env,name,MDB_NOTLS|MDB_NOLOCK|MDB_NOMEMINIT,get_mode());
    if (err) {
        report("Failed to open the environment:",err);
        return err;
    }
    err=mdb_txn_begin(mdb_env,NULL,0,&txn);
    if (err) {
        report("Failed to begin a transaction:",err);
        return err;
    }
    err=mdb_dbi_open(txn,"k2t",MDB_INTEGERKEY|MDB_DUPSORT|MDB_DUPFIXED|MDB_INTEGERDUP,&db_k2t); //integer key, integer tree numbers as values
    if (err) {
        report("Failed to open k2t DBI:",err);
        return err;
    }
    err=mdb_dbi_open(txn,"tdata",MDB_INTEGERKEY,&db_tdata); //integer key, integer tree numbers as values
    if (err) {
        report("Failed to open k2t DBI:",err);
        return err;
    }

    //New stuff
    err=mdb_dbi_open(txn,"tk2id",0,&db_tk2id); //integer key, integer tree numbers as values
    if (err) {
	report("Failed to open tk2id DBI:",err);
	return err;
    }

    err=mdb_dbi_open(txn,"id2c",MDB_INTEGERKEY,&db_id2c); //integer key, integer tree numbers as values
    if (err) {
	report("Failed to open id2c DBI:",err);
	return err;
    }



    err = mdb_cursor_open(txn, db_k2t, &k2t_cursor);
    if (err){
        report("Failed to open k2t cursor", err);
    }
    err = mdb_cursor_open(txn, db_tdata, &tdata_cursor);
    if (err){
        report("Failed to open tdata cursor", err);
    }
    return 0;
}


int LMDB_Fetch::set_tree_to_next_id(){

    //get tree data
    //tree data is void pointer
    if (tree_ids_count < 1){
        finished = true;
        return 0;
    }



    MDB_val key,tree_id_val,t_val;
    tree_id_val.mv_data = tree_ids + tree_id_pointer;
    tree_id_val.mv_size = sizeof(uint32_t);

    //Now tree_id_val holds the tree id of the tree we want, so let's grab it to t_val
    int err=mdb_cursor_get(tdata_cursor,&tree_id_val,&t_val,MDB_SET_KEY);
    if (err){

    report("Failed to retrieve tree from tdata",err);
    return err;

    }
    tree->deserialize(t_val.mv_data);

    tree_id_pointer++;
    if (tree_id_pointer > tree_ids_count){

        finished=true;
    }

    return 0;
}


int LMDB_Fetch::set_tree_to_id(uint32_t tree_id){

    //get tree data
    //tree data is void pointer

    MDB_val key,tree_id_val,t_val;
    tree_id_val.mv_data = &tree_id;
    tree_id_val.mv_size = sizeof(uint32_t);

    //Now tree_id_val holds the tree id of the tree we want, so let's grab it to t_val
    int err=mdb_cursor_get(tdata_cursor,&tree_id_val,&t_val,MDB_SET_KEY);
    if (err){

    report("Failed to retrieve tree from tdata",err);
    return err;

    }
    tree->deserialize(t_val.mv_data);
    return 0;
}



int LMDB_Fetch::get_glob(uint32_t tree_id){

    //get tree data
    //tree data is void pointer

    MDB_val key,tree_id_val,t_val;
    tree_id_val.mv_data = &tree_id;
    tree_id_val.mv_size = sizeof(uint32_t);

    //Now tree_id_val holds the tree id of the tree we want, so let's grab it to t_val
    int err=mdb_cursor_get(tdata_cursor,&tree_id_val,&t_val,MDB_SET_KEY);
    if (err){

    report("Failed to retrieve tree from tdata",err);
    return err;

    }
    return <char*>t_val.mv_data;
}



bool LMDB_Fetch::set_tree_to_id_and_check(uint32_t tree_id){

    //get tree data
    //tree data is void pointer

    MDB_val key,tree_id_val,t_val;
    tree_id_val.mv_data = &tree_id;
    tree_id_val.mv_size = sizeof(uint32_t);

    //Now tree_id_val holds the tree id of the tree we want, so let's grab it to t_val
    int err=mdb_cursor_get(tdata_cursor,&tree_id_val,&t_val,MDB_SET_KEY);
    if (err){
    report("Failed to retrieve tree from tdata",err);
    return false;
    }
    tree->deserialize(t_val.mv_data);
    return check_tree(t_val.mv_data);
}


//Given a pointer to tree data, check that it has all the required sets
bool LMDB_Fetch::check_tree(void *tree_data) {
    tree->deserialize(tree_data);
    // std::cerr << "Checking...";
    for(int i=0; i<len_sets;i++){
	// std::cerr << "checking set " << sets[i] << std::endl;
        if (binary_search(sets[i], tree->set_indices, tree->set_indices+tree->set_count) == 0){
	    // std::cerr << "... failed on set " << sets[i] << std::endl;
            return false;
        }
    }
    for(int i=0; i<len_arrays;i++){
        if (binary_search(arrays[i], tree->map_indices, tree->map_indices+tree->map_count) == 0){
	    // std::cerr << "... failed on array " << arrays[i] << std::endl;
            return false;
        }
    }
    return true;
}


