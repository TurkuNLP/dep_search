import sys
import requests
import re
from io import StringIO
import time
from multiprocessing import Process, Queue
import traceback
import sys
import pysolr
import requests
import json

ID,FORM,LEMMA,UPOS,XPOS,FEATS,HEAD,DEPREL,DEPS,MISC=range(10)
field_re=re.compile(r"^(gov|dep|token|lemma|tag)_(a|s)_(.*)$",re.U)
class Query():

    def __init__(self,extra_terms, compulsory_items,or_groups, solr, case, q_obj, extra_params={}, langs=[]):

        self.langs = langs
        self.q_obj = q_obj
        self.extra_params = extra_params
        self.case = case
        self.or_groups = or_groups
        self.extra_terms = extra_terms #extra solr terms
        self.compulsory_items = compulsory_items
        self.solr = solr
        self.tree_id_queue = Queue()
        self.finished = False
        self.xfinished = {}
        self.started = False
        self.processes = {}

	#Start the main loop thread
        if len(langs) < 1:
            self.processes['main'] = Process(target=self.main_loop)
            self.processes['main'].start()
        else:
            for l in langs:
                print (l)
                self.processes[l] = Process(target=self.main_loop_lang, args=(l,))
                self.processes[l].start()
        self.started = True
    def get_queue(self):
        return self.tree_id_queue

    #XXX
    def get_lang(self, idx):
        params = {u"q":"id:"+str(idx),u"wt":u"json",u"rows":1,u"fl":u"lang",u"sort":u"id asc"}
        r = requests.get(self.solr+"/select",params=params,stream=True)
        jr = json.loads(r.text)['response']['docs'][0]['lang']
        #{'responseHeader': {'status': 0, 'QTime': 0, 'params': {'q': 'id:1069', 'fl': 'lang', 'sort': 'id asc', 'rows': '1', 'wt': 'json'}}, 'response': {'numFound': 1, 'start': 0, 'docs': [{'lang': 'pl'}]}}

        return jr
        #return json.loads(requests.get(self.solr+"/select",params=params, stream=True))['response']['lang']


    def main_loop_lang(self, lang):
        self.started=True
        self.xfinished[lang]=False
        #self.lang_qs[lang] = Queue()

        if lang != '':
            for idx in self.ids_from_solr_gen_lang(lang):
                #Feed it to the queue
                #print (lang, idx)
                self.tree_id_queue.put(idx)
        else:
            for idx in self.ids_from_solr_gen():
                #Feed it to the queue
                self.tree_id_queue.put(idx)

        self.xfinished[lang]=True
        self.tree_id_queue.put(-1)



    def main_loop(self):
        self.started=True
        for idx in self.ids_from_solr_gen():
            #Feed it to the queue
            self.tree_id_queue.put(idx)
        self.finished=True
        self.tree_id_queue.put(-1)

    def is_finished(self):
        return self.finished

    def kill(self):
        self.process.terminate()


    def get_solr_query(self,skip_source=False):
        """If skip_source is set to True, then extra terms are filtered to remove source"""

        terms=[]
        for et in self.extra_terms:
            if not et.strip():
                continue
            if skip_source and et.startswith("+source"):
                continue
            terms.append(et)
        for c in self.compulsory_items:

            match=field_re.match(c)
            assert match, ("Not a known field description", c)
            if match.group(1) in (u"gov",u"dep"):
                if match.group(3)==u"anyrel":
                    if self.q_obj.has_pdeprel:
                        terms.append(u'relations:*')
                    else: 
                        terms.append(u'words:*')

                else:
                   terms.append(u'relations:"%s"'%match.group(3))
            elif match.group(1)==u"tag":
                terms.append(u'feats:"%s"'%match.group(3))
            elif match.group(1)==u"lemma":
                terms.append(u'lemmas:"%s"'%match.group(3))
            elif match.group(1)==u"token":
                if not self.case:
                    terms.append(u'words:"%s"'%match.group(3))
                else:
                    terms.append(u'words_lcase:"%s"'%match.group(3))

        or_terms = []
        for group in self.or_groups.values():
            g_terms = []
            for item in group:

                if item.endswith('_lc'): continue
                if self.case: item = item.lower()

                match=field_re.match(item)
                assert match, ("Not a known field description", item)
                if match.group(1) in (u"gov",u"dep"):
                    if match.group(3)==u"anyrel":
                        if self.q_obj.has_pdeprel:
                            g_terms.append(u'relations:*')
                        else: 
                            g_terms.append(u'words:*')

                       #g_terms.append(u'relations:*')
                    else:
                       g_terms.append(u'relations:"%s"'%match.group(3))
                elif match.group(1)==u"tag":
                    g_terms.append(u'feats:"%s"'%match.group(3))
                elif match.group(1)==u"lemma":
                    g_terms.append(u'lemmas:"%s"'%match.group(3))
                elif match.group(1)==u"token":

                    if not self.case:
                        g_terms.append(u'words:"%s"'%match.group(3))
                    else:
                        g_terms.append(u'words_lcase:"%s"'%match.group(3))

            or_terms.append(u'(' + u' OR '.join(g_terms)  + u')')

        qry=u" AND ".join(terms)
        if len(terms) > 0 and len(or_terms) > 0:
            qry += u' AND '
        if len(or_terms) > 0:
            qry += u' AND '.join(or_terms)

        if len(qry) < 1: qry += '+words:*'

            
        return qry

    def kill_threads(self):
        for p in self.processes.keys():
            self.processes[p].terminate()


    def ids_from_solr_gen_lang(self, lang):

        try:

            qry= self.get_solr_query()

            #if len(self.langs)>0:
            qry = '(' + qry + ') AND ( lang:' + lang + ')'
            #print (qry)
            #print >> sys.stderr, "Solr qry", qry.encode('utf8')
            #### XXX TODO How many rows?
            beg=time.time()
            params = {u"q":qry,u"wt":u"csv",u"rows":2147483647,u"fl":u"id",u"sort":u"id asc"}
            if type(self.extra_params) == dict:
                params.update(self.extra_params)
            r=requests.get(self.solr+"/select",params=params, stream=True)
            r_iter = r.iter_lines()

            #row_count=r.text.count(u"\n")-1 #how many lines? minus one header line
            #cdef uint32_t *id_array=<uint32_t *>malloc(row_count*sizeof(uint32_t))
            #r_txt=StringIO.StringIO(r.text)
            col_name=r_iter.__next__() #column name
            #print (col_name)
            assert col_name==b"id", repr(col_name)
            hits = 0
            for idx,id in enumerate(r_iter):
                #assert idx<row_count, (idx,row_count)
                hits +=1
                yield int(id)
                #print (id)
                
        except:
            import traceback; traceback.print_exc()
        #yield -1





    def ids_from_solr_gen(self):

        try:

            qry= self.get_solr_query()

            if len(self.langs)>0:
                qry = '(' + qry + ') AND (' + ' OR '.join(['lang:' + l for l in self.langs]) + ')'

            #print >> sys.stderr, "Solr qry", qry.encode('utf8')
            #### XXX TODO How many rows?
            beg=time.time()
            params = {u"q":qry,u"wt":u"csv",u"rows":2147483647,u"fl":u"id",u"sort":u"id asc"}
            if type(self.extra_params) == dict:
                params.update(self.extra_params)
            r=requests.get(self.solr+"/select",params=params, stream=True)
            r_iter = r.iter_lines()

            #row_count=r.text.count(u"\n")-1 #how many lines? minus one header line
            #cdef uint32_t *id_array=<uint32_t *>malloc(row_count*sizeof(uint32_t))
            #r_txt=StringIO.StringIO(r.text)
            col_name=r_iter.__next__() #column name
            #print (col_name)
            assert col_name==b"id", repr(col_name)
            hits = 0
            for idx,id in enumerate(r_iter):
                #assert idx<row_count, (idx,row_count)
                hits +=1
                yield int(id)
                #print (id)
                
        except:
            import traceback; traceback.print_exc()
        yield -1

        #print >> sys.stderr, "Hits from solr:", hits, " in", time.time()-beg, "seconds"

class IDX(object):

    def __init__(self,args):
        self.documents=[] # List of documents to be pushed into solr at the next convenient occasion
        self.batch_size=10000
        self.tree_count=0
        self.solr_url=args.solr
        self.current_id=0
        self.url=u"unknown"
        self.lang=args.lang
        self.source=args.source
        self.query_for_id()

    def query_for_id(self):
        s=pysolr.Solr(self.solr_url,timeout=600)
        r=requests.get(self.solr_url+"/select",data={u"q":u"*:*",u"stats.field":"id",u"stats":u"true",u"wt":u"json",u"rows":0})
        response=json.loads(r.text)
        max_id=response["stats"]["stats_fields"]["id"]["max"]
        if max_id is None:
            self.current_id=0
        else:
            self.current_id=int(max_id)
        #print ("Solr setting id to",self.current_id, file=sys.stderr)
        
    def commit(self,force=False):
        if force or len(self.documents)>=self.batch_size:
            try:
                s=pysolr.Solr(self.solr_url,timeout=600)
                self.tree_count+=len(self.documents) #sum(len(d[u"_childDocuments_"]) for d in self.documents)
                print (self.tree_count, "trees in Solr")#, file=sys.stderr)
                #print (self.documents)
                #print (s.add(self.documents))
                self.documents=[]
                s.commit()
            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()
                if len(self.documents)>10*self.batch_size:
                    print ("Too many documents uncommitted", len(self.documents))#, file=sys.stderr)
                    sys.exit(-1)

    def next_id(self):
        self.current_id+=1
        return self.current_id
        
    def new_doc(self,url,lang):
        self.url=url
        self.lang=lang
        #self.documents.append({u"id":self.next_id(),u"url":url,u"lang":lang,u"_childDocuments_":[]})
        
    def add_to_idx(self, comments, conllu):
        """ 
        id - integer id
        conllu - list of lists as usual
        """
        
        feats=set()
        words=[]
        lemmas=[]
        relations=set()

        for cols in conllu:
            feats.add(cols[UPOS])
            if cols[FEATS]!=u"_":
                feats|=set(cols[FEATS].split(u"|"))
            words.append(cols[FORM])
            lemmas.append(cols[LEMMA])
            if cols[DEPREL]!=u"root":
                relations.add(cols[DEPREL])
            if cols[DEPS]!=u"_":
                for g_dtype in cols[DEPS].split(u"|"):
                    g,dtype=g_dtype.split(u":",1)
                    if dtype!=u"root":
                        relations.add(dtype)
        d={}
        d[u"id"]=self.next_id()
        d[u"words"]=u" ".join(words)
        d[u"lemmas"]=u" ".join(lemmas)
        if feats:
            d[u"feats"]=list(feats)
        if relations:
            d[u"relations"]=list(relations)
        d[u"url"]=self.url
        d[u"lang"]=self.lang
        d[u"source"]=self.source

        self.documents.append(d)
        self.commit(force=True)
        
        return d[u"id"]