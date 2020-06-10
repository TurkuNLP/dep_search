# dep_search

### General Notes

A python3 toolkit for dependency tree search.

### Install

cat ubuntu_18.10.needed_packages | xargs sudo apt-get install -y
./install.sh

#### Solr
Core-configuration for Solr is included as folder solr_config, and is tested with Solr 6.6.5
### Indexing
Indexing is performed with build_index.py. To index a few treebanks with default configuration, which is lmdb:
~~~~
$ cat ./test_data/ud/ud-treebanks-v2.3/UD_Polish-SZ/pl_sz-ud-train.conllu | python3 build_index.py --lang pl --d all_ud_db
$ cat ./test_data/ud/ud-treebanks-v2.3/UD_Hindi-HDTB/hi_hdtb-ud-train.conllu | python3 build_index.py  --lang hi --d all_ud_db
$ cat ./test_data/ud/ud-treebanks-v2.3/UD_Arabic-NYUAD/ar_nyuad-ud-train.conllu | python3 build_index.py  --lang ar --d all_ud_db
~~~~

The same, but using solr for finding potential hits and lmdb to fetch the results:
~~~~
$ cat ./test_data/ud/ud-treebanks-v2.3/UD_Polish-SZ/pl_sz-ud-train.conllu | python3 build_index.py --filterdb solr_filter_db --lang pl --d all_ud_db
$ cat ./test_data/ud/ud-treebanks-v2.3/UD_Hindi-HDTB/hi_hdtb-ud-train.conllu | python3 build_index.py  --filterdb solr_filter_db --lang hi --d all_ud_db
$ cat ./test_data/ud/ud-treebanks-v2.3/UD_Arabic-NYUAD/ar_nyuad-ud-train.conllu | python3 build_index.py --filterdb solr_filter_db --lang ar --d all_ud_db
~~~~


#### Available db modules:
* LMDB
     - lmdb_Blobldb, lmdb_filter_db
* Solr
    - solr_blob_db, solr_filter_db
* Pickle
    - PickleDB

### Querying

To query a database:
~~~~
python3 query.py -d all_ud_db '_ <amod _'
~~~~
To query a database with specific languages:
~~~~
python3 query.py -d all_ud_db --langs hi '_ <amod _'
python3 query.py -d all_ud_db --langs pl,hi '_ <amod _'
~~~~
To query multiple databases, one can use asterisks, or list the databases:
~~~~
python3 query.py -d all_*_db  --langs pl,hi '_ <amod _'
python3 query.py -d x_db,a_db  --langs pl,hi '_ <amod _'
~~~~
#### Query as conllu filter
To use dep_search as a conllu filter:
~~~~
$ cat ./test_data/ud/ud-treebanks-v2.3/UD_Hindi-HDTB/hi_hdtb-ud-train.conllu | python3 filter_conllu.py '_ <amod _'
~~~~

#### Query Language
Query Language is documented here:
https://bionlp.utu.fi/searchexpressions-new.html

### What works
* indexing
* querying
* filtering text

### API & GUI
Two guis and apis are included. The first one is compliant with previous dep_search api and is located at the folder: "webapi".
This api is compatible with the search gui available at: https://github.com/fginter/dep_search_serve

The other GUI and api is included in the folder: "api_gui". This one supports streaming results and multiple languages.

Both are python flask applications.
