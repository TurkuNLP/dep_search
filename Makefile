TARGETS=cythonpackages

.PHONY: setlib

all: setlib $(TARGETS)

setlib:
	$(MAKE) -C dep_search/setlib

cythonpackages: dep_search/solr_blob_db.pyx dep_search/Blobldb.pyx dep_search/DB.pyx dep_search/kc_Blobldb.pyx dep_search/levelDB.pyx dep_search/lmdb_Blobldb.pyx dep_search/py_tree.pyx
	cythonize -i dep_search/py_tree.pyx dep_search/DB.pyx dep_search/Blobldb.pyx dep_search/solr_blob_db.pyx dep_search/kc_Blobldb.pyx dep_search/levelDB.pyx dep_search/lmdb_Blobldb.pyx 

clean:
	rm -f ./dep_search/*.so
	$(MAKE) -C setlib clean



