import os
import time

#Thanks monkut, https://stackoverflow.com/questions/1392413/calculating-a-directorys-size-using-python
def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def main():


    import glob
    #/media/mjluot/d160e2fa-825c-42c4-9ccb-96ee3be30058/deps/xxxz/restart (copy)/test_data/ud/ud-treebanks-v2.3/UD_Afrikaans-AfriBooms/af_afribooms-ud-dev.conllu
    #./test_data/ud/ud-treebanks-v2.3/UD_Afrikaans-AfriBooms/af_afribooms-ud-train.conllu
    xlangs = []
    xconfs = []
    conllus = []
    for f in glob.glob('./test_data/ud/ud-treebanks-v2.3/UD_*/*-ud-train.conllu')[:3]:
        #
        xlangs.append(f.split('/')[-1].split('-')[0].split('_')[0])
        conllus.append(f)
        xconfs.append('-d xxx --lang ' + xlangs[-1])

    dbs = [('Blobldb','lev_filter_db'), ('Blobldb','solr_filter_db') ,('lmdb_Blobldb','lmdb_filter_db')]
    dbs = [('Blobldb','solr_filter_db'),]

    name = 'solr_ud'

    #blob_dbs = ['Blobldb', 'lmdb_Blobldb']
    for blob_db, filter_db in dbs:
        #name = 'all_ud'#_train_' + blob_db + '_' + filter_db
        for lang, conllu in zip(xlangs, conllus):
            print ('echo ' + lang + ' ' + conllu + ' ' + name)
            print ('cat ' + conllu + ' | python3 build_index.py --solr "http://localhost:8983/solr/dep_search2" --filterdb ' + filter_db + ' --blobdb ' + blob_db + ' --lang ' + lang + ' --d ' + name)


def queryt():

#    xlangs = []
#    xconfs = []
#    conllus = []
#    for f in glob.glob('./test_data/ud/ud-treebanks-v2.3/UD_*/*-ud-train.conllu')[:6]:
        #
#        xlangs.append(f.split('/')[-1].split('-')[0].split('_')[0])
#        conllus.append(f)
#        xconfs.append('-d xxx --lang ' + xlangs[-1])
    #import pdb;pdb.set_trace()
#    dbs = [('Blobldb','lev_filter_db'), ('Blobldb','solr_filter_db') ,('lmdb_Blobldb','lmdb_filter_db')]
    #
    queries = ['_ <amod _', '_ !<amod _', 'VERB < _', 'VERB !> _', '_']
    #conllus = ['./test_data/grc_perseus-ud-dev.conllu']
    #conf = [(('-d xxx --lang gr',),'-m 0 -d xxx'), (('-d xxx --lang gr',),'-m 0 -d xxx --langs gr,ar')]
    for blob_db, filter_db in dbs:
        
        for xx in range(0,3):
            if xx < 1:
                qlangs = None
            else:
                qlangs = ','.join(xlangs[:xx])

            for i, qry in enumerate(queries):
                x = time.time()
                if xx ==0:
                    os.system('python3 query.py -m 0 -d ' + 'all_ud_train_' + blob_db + '_' + filter_db + ' "' + qry + '" > ./res/' +  'all_ud_train_' + blob_db + '_' + filter_db + '_'+str(i))
                    z = time.time()
                    total = z-x
                    print ('res','qry_time',blob_db,filter_db,qry,'all_langs',total)
                else:
                    os.system('python3 query.py -m 0 -d ' + 'all_ud_train_' + blob_db + '_' + filter_db + ' --langs ' + qlangs + ' "' + qry + '" > ./res/' +  'all_ud_train_' + blob_db + '_' + filter_db + '_'+str(i))
                    z = time.time()
                    total = z-x
                    print ('res','qry_time',blob_db,filter_db,qry,qlangs,total)


def ggg():




    for idx_arg, qry_arg in conf:

        x = time.time()
        print (idx_arg)
        os.system('rm -rf xxx')
        for conllu, iarg in zip(conllus, idx_arg):

            #do indexing
            print('cat ' + conllu + ' | python3 build_index.py ' + iarg)
            os.system('cat ' + conllu + ' | python3 build_index.py ' + iarg)
        z = time.time()

        total = z-x
        print ('res','idx_time',idx_arg,conllus,total)
        print ('res','db_size',idx_arg,conllus,get_size(start_path='./xxx'))

        for qry in queries:
           #do querying
           print ('python3 query.py ' + qry_arg + ' "' + qry + '"')
           x = time.time()
           os.system('python3 query.py ' + qry_arg + ' "' + qry + '"')
           z = time.time()
           total = z-x
           print ('res','qry_time',idx_arg,qry_arg,conllu,qry,total)
           ## list the results

                ## 

           print ('python3 query_mdb.py ' + qry_arg + ' "' + qry + '"')
           x = time.time()
           os.system('python3 query_mdb.py ' + qry_arg + ' "' + qry + '"')
           z = time.time()
           total = z-x
           print ('res','qry_time','mdb',idx_arg,qry_arg,conllu,qry,total)


                
main()
