import glob
import glob

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


def calc_freqs(f, freqs):


    docs = set()
    lemmas = set()

    #
    tokens = 0
    #
    trees = 0
    #
    hits = 0
    
    #open file
    inf = open(f,'rt')
    for l in inf:
        if l.startswith('# hittoken:'):
            hits += 1
            lemmas.add(l.split('\t')[3])

        if l.startswith('# doc:'):
            docs.add(l)
            


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

    freqs['tokens'] += tokens
    freqs['trees'] += trees
    freqs['hits'] += hits
    freqs['docs'].update(docs)
    freqs['lemmas'].update(lemmas)

    return freqs


def get_freqs(f):

    files = glob.glob(f)
    files.sort()

    freqs = dict()

    for f in files:
        freqs = calc_freqs(f, freqs)

    return [{'hits': freqs['hits'], 'trees': freqs['trees'], 'all_tokens': freqs['tokens'], 'docs': len(freqs['docs']), 'all_lemmas': len(freqs['lemmas'])}]


