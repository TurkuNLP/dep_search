import glob
import glob

from collections import defaultdict
from collections import Counter

def yield_kwics(f, n):

    inf = open(f,'rt')
    res = set()
    td = dict()

    for l in inf:
        #
        if l.startswith('# hittoken:'):
            res.add(int(l.split('\t')[1]))
        
        if '\t' in l:
            try:
                td[int(l.split('\t')[0])] = l.split('\t')
            except:
                pass

        #print (td)
        if l == '\n':

            for r in list(res):
                xx=[]
                for x in range(r-n, r+n):
                    try:
                        xx.append(td[x][1])
                    except:
                        xx.append('_')
                yield '\t'.join(xx) + '\n'

            res = set() 
            td = dict()
    inf.close()


def calc_dep_freqs(curr_tree, freqs):

    hit_idx = []
    tree = {}
    kids = defaultdict(list)

    #dependent_words
    #dependent_lemmas

    #right_words
    #right_lemmas

    #parent_words
    #parent_lemmas

    #deptypes_as_dependent
    #deptypes_as_parent

    #hit_words

    for xx in ["dependent_words","dependent_lemmas","right_words","right_lemmas","parent_words","parent_lemmas","deptypes_as_dependent","deptypes_as_parent","hit_words","hit_lemmas", "left_words","left_lemmas"]:
        if not xx in freqs.keys():
            #
            freqs[xx] = []


    #make tree into a dict & get idx
    for l in curr_tree:
        if l.startswith('# hittoken:'):
            hit_idx.append(l.split('\t')[1])
        if not l.startswith('#') and '\t' in l:
            #
            idx = l.split('\t')[0]
            tree[idx] = l.split('\t')
            
            kids[l.split('\t')[6]].append(idx)

    #
    for idx in hit_idx:
        #hit word
        xx = tree[idx]

        freqs['hit_words'].append(xx[1])
        freqs['hit_lemmas'].append(xx[2])
        freqs['deptypes_as_dependent'].append(xx[7])

        #parent_words
        if xx[6]!='0':
            freqs['parent_words'].append(tree[xx[6]][1])
            freqs['parent_lemmas'].append(tree[xx[6]][2])

        #dependent_words
        for k in kids[idx]:
            freqs['dependent_words'].append(tree[k][1])
            freqs['dependent_lemmas'].append(tree[k][2])
       
            freqs['deptypes_as_parent'].append(tree[k][7])


        if int(idx) > 1:
            xx = tree[str(int(idx)-1)]
            freqs['left_words'].append(xx[1])
            freqs['left_lemmas'].append(xx[2])
        
        if int(idx) < len(tree.keys()):

            xx = tree[str(int(idx)+1)]
            freqs['right_words'].append(xx[1])
            freqs['right_lemmas'].append(xx[2])
        
    return freqs

def calc_freqs(f, freqs):


    docs = set()
    lemmas = set()
    wfs = set()

    #
    tokens = 0
    #
    trees = 0
    #
    hits = 0

    #dependent_words
    #dependent_lemmas

    #right_words
    #right_lemmas

    #parent_words
    #parent_lemmas

    #deptypes_as_dependent
    #deptypes_as_parent


    
    #open file
    inf = open(f,'rt')
    curr_tree = []

    for l in inf:

        if l.startswith('# hittoken:'):
            hits += 1
            lemmas.add(l.split('\t')[3])
            wfs.add(l.split('\t')[1])

        if l.startswith('# doc:'):
            docs.add(l)
            
        curr_tree.append(l)
        if l == '\n':
            #
            freqs = calc_dep_freqs(curr_tree, freqs)
            curr_tree = []

        if not l.startswith('#') and '\t' in l:
            tokens += 1

        if l.startswith('\n'):
            trees += 1

    if 'tokens' not in freqs.keys():
        #
        freqs['tokens'] = 0

    if 'trees' not in freqs.keys():
        #
        freqs['trees'] = 0

    if 'hits' not in freqs.keys():
        #
        freqs['hits'] = 0

    if 'docs' not in freqs.keys():
        #
        freqs['docs'] = set()

    if 'lemmas' not in freqs.keys():
        #
        freqs['lemmas'] = set()

    if 'wfs' not in freqs.keys():
        #
        freqs['wfs'] = set()

    freqs['tokens'] += tokens
    freqs['trees'] += trees
    freqs['hits'] += hits
    freqs['docs'].update(docs)
    freqs['lemmas'].update(lemmas)
    freqs['wfs'].update(wfs)

    return freqs

def get_freqs(f):

    files = glob.glob(f)
    files.sort()

    freqs = dict()

    for f in files:
        freqs = calc_freqs(f, freqs)

    xx = {}
    for kk in ["dependent_words","dependent_lemmas","right_words","right_lemmas","parent_words","parent_lemmas","deptypes_as_dependent","deptypes_as_parent","hit_words","hit_lemmas", "left_words","left_lemmas"]:
        #Counter
        xx[kk + '_most_common'] = Counter(freqs[kk]).most_common(10)
        #All
        xx[kk + '_count'] = len(freqs[kk])

    return [{'hits': freqs['hits'], 'trees': freqs['trees'], 'all_tokens': freqs['tokens'], 'docs': len(freqs['docs']), 'uniq_lemmas': len(freqs['lemmas']), 'uniq_wordforms': len(freqs['wfs'])}, xx]


