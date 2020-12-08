import glob
import os

def main():


    try:
        os.mkdir('../xud_dbs/')
    except:pass

    pairs = []
    for f in glob.glob('../uds/UD_*'):
        #try:
        lang = ('_'.join(f.split('-')[0].split('_')[1:]))
        idx = (f.split('/')[-1])
        try:
            os.mkdir('../xud_dbs/' + idx)
        except:pass
        files = glob.glob(f + '/*conllu')
        
        for ff in files:
            #
            print ('cat ' + ff + ' | python3 build_index.py -d ../xud_dbs/' + idx + '/' + ff.split('.')[-2].split('/')[-1] +  ' --lang ' + lang)

main()
