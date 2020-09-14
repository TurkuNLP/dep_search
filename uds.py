import glob


def main():

    pairs = []
    for f in glob.glob('./uds/UD_*'):
        try:
            #print (f)
            #print (f.split('_')[1].split('-')[0])
            #print (glob.glob(f+'/*train.conllu')[0])
            pairs.append((f.split('_')[1].split('-')[0], glob.glob(f+'/*train.conllu')[0]))
        except:pass

    for l, f in pairs:
        #
        print ('cat ' + f + ' | python3 build_index.py -d ./ud_dbs/' + f.split('/')[-1].split('.')[0] + ' --lang ' + l)


main()
