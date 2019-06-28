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

def kwic_gen(f,n=5):

    files = glob.glob(f)
    files.sort()
    for f in files:
        for x in yield_kwics(f,n):
            yield x

