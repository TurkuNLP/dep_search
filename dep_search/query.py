#!/usr/bin/env python
import sys
import os
import ast
import importlib
import json
import re
import zlib
import argparse
import glob
from collections import defaultdict
import copy
from tempfile import gettempdir
from contextlib import contextmanager
import io


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


field_re=re.compile(r"^(!?)(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)

def map_set_id(args, db, qobj):

    #XXX: figure out a way to check if this and that is in the db. 

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

        #print >> sys.stderr, "narg:", narg
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

        #print compulsory
        #print it_is_set
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
    #print >> sys.stderr, 'optional:', optional
    #print >> sys.stderr, 'types:', types
    solr_or_groups = []


    return rarest, c_args_s, s_args_s, c_args_m, s_args_m, just_all_set_ids, types, optional, solr_args, or_groups



def query(query_fields):

    #print >> sys.stderr, 'query fields:', query_fields
    """
    query_fields: A list of strings describing the data to fetch
          Each string names a set to retrieve

          (gov|dep)_(a|s)_deptype
          - gov -> retrieve a from-governor-to-dependent mapping/set
          - dep -> retrieve a from-dependent-to-governor mapping/set
          - a -> retrieve a mapping (i.e. used as the third argument of the pairing() function
          - s -> retrieve a set (i.e. the set of governors or dependents of given type)
          - deptype -> deptype or u"anytype"
          prefixed with "!" means that only non-empty sets are of interest

          tag_s_TAG  -> retrieve the token set for a given tag
          prefixed with "!" means that only non-empty sets are of interest

          token_s_WORD -> retrieve the token set for a given token
          lemma_s_WORD -> retrieve the token set for a given lemma
          prefixed with "!" means that only non-empty sets are of interest
    """

    joins=[(u"FROM graph",[])]
    wheres=[]
    args=[]
    selects=[u"graph.graph_id",u"graph.token_count"]
    for i,f in enumerate(query_fields):
        match=field_re.match(f)
        assert match
        req,ftype,stype,res=match.groups() #required? field-type?  set-type?  restriction
        if req==u"!":
            j_type=u""
        elif not req:
            j_type=u"LEFT "
        else:
            assert False #should never happen
        if ftype in (u"gov",u"dep"):
            joins.append((u"%sJOIN rel AS t_%d ON graph.graph_id=t_%d.graph_id and t_%d.dtype=?"%(j_type,i,i,i),[res]))
            if stype==u"s":
                selects.append(u"t_%d.token_%s_set"%(i,ftype))
            elif stype==u"a":
                selects.append(u"t_%d.token_%s_map"%(i,ftype))
        elif ftype in (u"token",u"lemma",u"tag"):
            joins.append((u"%sJOIN %s_index AS t_%d ON graph.graph_id=t_%d.graph_id and t_%d.%s=?"%(j_type,ftype,i,i,i,ftype),[res]))
            selects.append(u"t_%d.token_set"%i)
    
    joins.sort() #This is a horrible hack, but it will sort FROM JOIN ... LEFT JOIN the right way and help the QueryPlan generator
    q=u"SELECT %s"%(u", ".join(selects))
    q+=u"\n"+(u"\n".join(j[0] for j in joins))
    q+=u"\n"
    args=[]
    for j in joins:
        args.extend(j[1])
    return q,args

def get_data_from_db(db_conn,graph_id):
    results=db_conn.execute('SELECT conllu_data_compressed,conllu_comment_compressed FROM graph WHERE graph_id=?',(str(graph_id),))
    for sent,comment in results.fetchall():
        return zlib.decompress(sent).strip(),zlib.decompress(comment).strip()
    return None,None

'''
def load(pyxFile):
    """Loads a search pyx file, returns the module"""
    ###I need to hack around this, because this thing is messing stdout
    print >> sys.stderr, "Loading", pyxFile
    error=subprocess.call(["python","compile_ext.py",pyxFile], stdout=sys.stderr, stderr=sys.stderr)
    if error!=0:
        print >> sys.stderr, "Cannot compile search code, error:",error
        sys.exit(1)
    mod=importlib.import_module(pyxFile)
    return mod
'''


def import_from_location(path):
    from os.path import basename
    from importlib.util import spec_from_file_location, module_from_spec
    from importlib.machinery import EXTENSION_SUFFIXES
    base = basename(path)
    for ext in EXTENSION_SUFFIXES:
        full_path = path + ext
        if not os.path.exists(full_path):
            continue
        spec = spec_from_file_location("dep_search.queries." + base, full_path)
        mod = module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    raise Exception("No module found for {}".format(path))


@contextmanager
def stdout_redirector(to_fd):
    # The original fd stdout points to. Usually 1 on POSIX systems.
    original_stdout_fd = sys.stdout.fileno()

    def _redirect_stdout(to_fd):
        """Redirect stdout to the given file descriptor."""
        # Flush and close sys.stdout - also closes the file descriptor (fd)
        sys.stdout.close()
        # Make original_stdout_fd point to the same file as to_fd
        os.dup2(to_fd, original_stdout_fd)
        # Create a new sys.stdout that points to the redirected fd
        sys.stdout = io.TextIOWrapper(os.fdopen(original_stdout_fd, 'wb'))

    # Save a copy of the original stdout fd in saved_stdout_fd
    saved_stdout_fd = os.dup(original_stdout_fd)
    try:
        # Create a temporary file and redirect stdout to it
        _redirect_stdout(to_fd)
        # Yield to caller, then redirect stdout back to the saved fd
        yield
        _redirect_stdout(saved_stdout_fd)
        # Copy contents of temporary file to the given stream
    finally:
        os.close(saved_stdout_fd)


def load(pyxFile):
    """Loads a search pyx file, returns the module"""
    def rel(path):
        return os.path.join(THIS_DIR, path)
    from Cython.Build.Cythonize import run_distutils
    from Cython.Build.Dependencies import cythonize
    from distutils.extension import Extension
    base_dir = os.path.dirname(pyxFile)
    sources = [pyxFile, rel("query_functions.cpp")]
    if 'linux' in sys.platform:
        sources.append(rel("tree_lmdb.cpp"))
        import glob
        setlibso = glob.glob(rel('setlib/pytset.*.so'))[0] 
        extra_objects = [rel(setlibso)]
    else:
        sources.append(rel("setlib/pytset.cpp"))
    with stdout_redirector(sys.stderr.fileno()):
       ext_modules = cythonize(
           [Extension(
               "*",
               sources,
               include_dirs=[THIS_DIR, rel("setlib")],
               extra_objects=extra_objects,
           )],
           include_path=[THIS_DIR],
       )
       run_distutils((base_dir, ext_modules))
    return import_from_location(os.path.splitext(pyxFile)[0])


def get_url(comments):
    for c in comments:
        if c.startswith(u"# URL:"):
            return c.split(u":",1)[1].strip()
    return None


def query_from_db(q_obj, args, db, fdb, set_id_db):

    #init the dbs
    q_obj.set_db(set_id_db)

    #This is a first try and an example without filter db
    idx = 1
    counter = 0
    max_hits = args.max

    end_cnt = 0 


    q = fdb.tree_id_queue 
    #import pdb;pdb.set_trace()
    while True:
        try:
            #print ('???')
            idx = q.get()
            #print (idx)
            #continue

            if idx == -1:
                end_cnt += 1
                #print (fdb.is_finished())
                #print (fdb.finished)
                #print (fdb.started)
                #print (fdb.processes)
                #print ('!!!', end_cnt, len(args.langs.split(',')))
                if end_cnt == len(args.langs.split(',')):
                    break
                continue

            res_set = q_obj.check_tree_id(idx, db)
            #idx += 1
            #print (idx)
            #print (res_set)
            #import pdb;pdb.set_trace()

            if len(res_set) > 0:
                #tree
                #import pdb;pdb.set_trace()
                hit = q_obj.get_tree_text()
                tree_comms = q_obj.get_tree_comms()
                tree_lines=hit.split("\n")

                if counter >= max_hits and max_hits > 0:
                    break
                its_a_hit = False

                #try:
                print ('# lang:', fdb.get_lang(idx))
                print ('# doc:', fdb.get_url(idx))

                #except:
                #    pass
                for r in res_set:
                    print ("# db_tree_id:",idx)
                    print ("# visual-style\t" + str(r + 1) + "\tbgColor:lightgreen")
                    try:
                        print ("# hittoken:\t"+tree_lines[r])
                        its_a_hit = True
                    except:
                        pass
                if its_a_hit:

                    if args.context>0:
                        hit_url=get_url(tree_comms)
                        texts=[]
                        # get +/- context sentences from db
                        for i in range(idx-args.context,idx+args.context+1):
                            try:
                                if i==idx:
                                    data=hit
                                else:
                                    q_obj.set_tree_id(i, db)
                                    data = q_obj.get_tree_text()
                                    data_comment = q_obj.get_tree_comms()

                                    if data is None or get_url(data_comment)!=hit_url:
                                        continue
                                text=u" ".join(t.split(u"\t",2)[1] for t in data.split(u"\n"))
                                if i<idx:
                                    texts.append(u"# context-before: "+text)
                                elif i==idx:
                                    texts.append(u"# context-hit: "+text)
                                else:
                                    texts.append(u"# context-after: "+text)
                            except:
                                pass
                        try:
                            print (u"\n".join(text for text in texts)).encode(u"utf-8")
                        except:
                            pass

                    print (tree_comms)
                    print (hit)
                    print ()
                    counter += 1

                #import pdb;pdb.set_trace(
        except:
            import traceback
            traceback.print_exc()
            pass
            if idx > 0: break
    #import pdb;pdb.set_trace()

    fdb.kill_threads()
    #print ('cn', counter)
    return counter

def query_from_db_api(q_obj, args, db, fdb, set_id_db):
    def res_file(basename):
        return os.path.join(args.res_dir, basename)

    #init the dbs
    q_obj.set_db(set_id_db)

    #This is a first try and an example without filter db
    idx = 1
    counter = 0
    max_hits = args.max

    end_cnt = 0 

    curr_tree = []

    outf_name = glob.glob(res_file('*_' + args.ticket + '*.conllu'))

    langs = set()
    for f in outf_name:
        langs.add(f.split('/')[-1].split('_')[0])

    outf_files = {}
    tree_counts = {}

    for l in list(langs):

        lf = glob.glob(res_file(l + '_' + args.ticket + '*.conllu'))
        lf.sort()
        try:
            latest_idx = int(lf[-1].split('_')[-1].split('.')[0])
        except:
            latest_idx = 0

        outf_files[l] = open(res_file(l + '_' + args.ticket + '_' + str(latest_idx) + '.conllu'), 'wt')
        tree_counts[l] = latest_idx

    q = fdb.tree_id_queue 
    #import pdb;pdb.set_trace()
    while True:
        try:
            #print ('???')
            idx = q.get()
            print (idx)
            #continue

            #print ('xxx', idx)
            if idx == -1:
                end_cnt += 1
                #print (fdb.is_finished())
                #print (fdb.finished)
                #print (fdb.started)
                #print (fdb.processes)
                #print ('!!!', end_cnt, len(args.langs.split(',')))
                if end_cnt == len(args.langs.split(',')):
                    break
                continue

            res_set = q_obj.check_tree_id(idx, db)
            #idx += 1
            #print (idx)
            #print (res_set)
            #import pdb;pdb.set_trace()

            curr_tree = []
            if len(res_set) > 0:

                #tree
                #import pdb;pdb.set_trace()
                hit = q_obj.get_tree_text()
                tree_comms = q_obj.get_tree_comms()
                tree_lines=hit.split("\n")

                if counter >= max_hits and max_hits > 0:
                    break
                its_a_hit = False

                #try:
                curr_tree.append('# lang:\t'+ fdb.get_lang(idx))
                curr_lang = fdb.get_lang(idx)

                if fdb.get_lang(idx) not in langs:
                    langs.add(fdb.get_lang(idx))
                    xx = open(res_file(args.ticket + '.langs'), 'w')
                    xx.write(json.dumps(list(langs)))
                    xx.close()                
                    outf_files[curr_lang] = open(res_file(curr_lang + '_' + args.ticket + '_' + str(0) + '.conllu'), 'wt')
                    tree_counts[curr_lang] = 0


                #except:
                #    pass
                for r in res_set:
                    curr_tree.append("# db_tree_id:\t" + str(idx))
                    curr_tree.append("# visual-style\t" + str(r + 1) + "\tbgColor:lightgreen")
                    try:
                        curr_tree.append("# hittoken:\t"+tree_lines[r])
                        its_a_hit = True
                    except:
                        pass

                if its_a_hit:
                    texts = []
                    if args.context>0:
                        hit_url=get_url(tree_comms)
                        texts=[]
                        # get +/- context sentences from db
                        for i in range(idx-args.context,idx+args.context+1):
                            if i<0:continue

                            if i==idx:
                                data=hit
                            else:
                                q_obj.set_tree_id(i, db)
                                data = q_obj.get_tree_text()
                                data_comment = q_obj.get_tree_comms()
                                if data is None or get_url(data_comment)!=hit_url:
                                    continue
                            text=u" ".join(t.split(u"\t",2)[1] for t in data.split(u"\n"))
                            if i<idx:
                                texts.append(u"# context-before: "+text)
                            elif i==idx:
                                texts.append(u"# context-hit: "+text)
                            else:
                                texts.append(u"# context-after: "+text)
                        try:
                            curr_tree.append(u"\n".join(text for text in texts)).encode(u"utf-8")
                        except:
                            pass

                    curr_tree.append(tree_comms)
                    curr_tree.append(hit)

                    outf_files[curr_lang].write('\n'.join(curr_tree) + '\n\n')
                    tree_counts[curr_lang] += 1
                    if tree_counts[curr_lang]%10==0:
                        outf_files[curr_lang].close()
                        outf_files[curr_lang] = open(res_file(curr_lang + '_' + args.ticket + '_' + str(tree_counts[curr_lang])+'.conllu'), 'w')
                        #tree_cnt = 0

                    curr_tree = []
                    counter += 1

                #import pdb;pdb.set_trace(
        except:
            import traceback
            traceback.print_exc()
            pass
            if idx > 0: break
    #import pdb;pdb.set_trace()
    for f,k in outf_files.items():
        k.close()
    fdb.kill_threads()
    #print ('cn', counter)
    outf = open(res_file(args.ticket+'.done'),'w')
    outf.close()

    return counter


























    #import pdb; pdb.set_trace()
    # init all necessary dbs
    


    # if id-flow:
        #init it
        # for id:
            # q_obj.fill_sets
            # q_obj.check
            # q_obj.get_tree_text and also comms
   # else:

       # for range, I suppose, stop @ db error 

def main(argv):
    global query_obj

    #XXX: Will fix!
    global solr_url

    parser = argparse.ArgumentParser(description='Execute a query against the db')
    parser.add_argument('-m', '--max', type=int, default=500, help='Max number of results to return. 0 for all. Default: %(default)d.')
    parser.add_argument('-d', '--database', default="/mnt/ssd/sdata/pb-10M/*.db",help='Name of the database to query or a wildcard of several DBs. Default: %(default)s.')
    parser.add_argument('-o', '--output', default=None, help='Name of file to write to. Default: STDOUT.')
    #parser.add_argument('-s', '--solr', default="http://localhost:8983/solr/dep_search2", help='Solr url. Default: %(default)s')
    parser.add_argument('search', nargs="?", default="parsubj",help='The name of the search to run (without .pyx), or a query expression. Default: %(default)s.')
    parser.add_argument('--context', required=False, action="store", default=0, type=int, metavar='N', help='Print the context (+/- N sentences) as comment. Default: %(default)d.')
    parser.add_argument('--query-dir', required=False, default=None, help='Use specified directory to keep compiled queries rather than a temporary directory.')
    parser.add_argument('--keep_query', required=False, action='store_true',default=False, help='Do not delete the compiled query after completing the search.')
    parser.add_argument('-i', '--case', required=False, action='store_true',default=False, help='Case insensitive search.')
    parser.add_argument('--extra-solr-term',default=[],action="append",help="Extra restrictions on Solr, strings passed verbatim in the Solr query, you can have several of these")
    parser.add_argument('--extra-solr-params',default="",help="Extra parameters on Solr - a dictionary passed verbatim in the Solr request")
    parser.add_argument('--langs',default="",help="List of language codes to be queried")
    parser.add_argument('--res-dir',default="",help="For API use")
    parser.add_argument('--ticket',default="",help="For API use")

    args = parser.parse_args(argv[1:])

    if '*' in args.database:
        for db in glob.glob(args.database):
            xargs = copy.copy(args)
            xargs.database = db
            main_db_query(xargs)
    elif ',' in args.database:
        for db in args.d.split(','):
            xargs = copy.copy(args)
            xargs.database = db
            main_db_query(xargs)
    else:
        main_db_query(args)


def get_query_mod(query_dir, search, case, set_id_db, database):
    if query_dir:
        query_dir = query_dir
    else:
        query_dir = gettempdir()
    if "/" in search:
        existing_location = search
    else:
        existing_location = os.path.join(query_dir, search + ".pyx")
    if os.path.exists(existing_location):
        print("Loading " + existing_location, file=sys.stderr)
        mod = load(existing_location)
    else:
        from dep_search import pseudocode_ob_3 as pseudocode_ob

        import hashlib
        m = hashlib.md5()
        m.update(search.encode('utf8') + str(case).encode('utf8') + database.encode('utf8'))

        json_filename = '' 

        temp_file_name = 'qry_' + m.hexdigest() + '.pyx'
        mod_pyx_path = os.path.join(query_dir, temp_file_name)
        if not os.path.isfile(mod_pyx_path):
            f = open(mod_pyx_path, 'wt')
            try:
                pseudocode_ob.generate_and_write_search_code_from_expression(search, f, json_filename=json_filename, db=set_id_db, case=case)
            except Exception as e:
                os.remove(mod_pyx_path)
                raise e

            mod=load(mod_pyx_path)
            #os.rename(temp_file_name, query_folder + temp_file_name)
            #os.rename(temp_file_name[:-4] + '.cpp', query_folder + temp_file_name[:-4] + '.cpp')
            #os.rename(temp_file_name[:-4] + '.so', query_folder + temp_file_name[:-4] + '.so')

        else:

            mod=load(mod_pyx_path)            
            #os.rename(temp_file_name, query_folder + temp_file_name)
            #os.rename(temp_file_name[:-4] + '.cpp', query_folder + temp_file_name[:-4] + '.cpp')
            #os.rename(temp_file_name[:-4] + '.so', query_folder + temp_file_name[:-4] + '.so')
    return mod


def main_db_query(args):

    #The blob and id database
    inf = open(args.database+'/db_config.json', 'rt')
    db_args = json.load(inf)
    inf.close()

    db_class = importlib.import_module('dep_search.' + db_args['blobdb'])
    db = db_class.DB(db_args['dir'])
    db.open()

    set_id_db = db_class.DB(db_args['dir'])
    set_id_db.open(foldername = '/set_id_db/')

    solr_url = db_args['solr']

    if args.output is not None:
        sys.stdout = open(args.output, 'w')

    mod = get_query_mod(
        args.query_dir,
        args.search,
        args.case,
        set_id_db,
        args.database
    )
    query_obj = mod.GeneratedSearch()

    total_hits=0

    #Loading and opening the databases or connections

    #The blob and id database
    #inf = open(args.database+'/db_config.json', 'rt')
    #db_args = json.load(inf)
    #inf.close()

    #db_class = importlib.import_module(db_args['blobdb'])
    #db = db_class.DB(db_args['dir'])
    #db.open()

    #... and lets load the filter db for fetching the filter list
    fdb_class = importlib.import_module('dep_search.' + db_args['filterdb'])
    rarest, c_args_s, s_args_s, c_args_m, s_args_m, just_all_set_ids, types, optional, solr_args, solr_or_groups = query_obj.map_set_id(set_id_db)

    try:
        extra_params= ast.literal_eval(args.extra_solr_params)
    except:
        extra_params = {}
    
    langs=[]
    if langs == "": 
        langs=[]
    else:
        langs = [args.langs,]
    if ',' in args.langs:
        langs = args.langs.split(',')

    if not db_args['filterdb'].startswith('solr_filter_db'):
        fdb = fdb_class.Query(args.extra_solr_term, [item[1:] for item in solr_args if item.startswith('!')], solr_or_groups, db_args['dir'], args.case, query_obj, extra_params=extra_params, langs=langs)
    else:
        fdb = fdb_class.Query(args.extra_solr_term, [item[1:] for item in solr_args if item.startswith('!')], solr_or_groups, solr_url, args.case, query_obj, extra_params=extra_params, langs=langs)

    if len(args.ticket) > 1:
        total_hits+=query_from_db_api(query_obj, args, db, fdb, set_id_db)
    else:
        total_hits+=query_from_db(query_obj, args, db, fdb, set_id_db)

    print ("Total number of hits:",total_hits,file=sys.stderr)

    if not args.keep_query:
        try:
            pass
            os.remove(query_folder + temp_file_name)
            os.remove(query_folder + temp_file_name[:-4] + '.cpp')
            os.remove(query_folder + temp_file_name[:-4] + '.so')
        except:
            pass
    sys.exit()
