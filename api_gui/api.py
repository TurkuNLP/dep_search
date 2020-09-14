from flask import stream_with_context, Response
import json
from flask import Flask, jsonify, Markup
import os
import time
from flask import render_template, send_from_directory
from flask import Flask, Markup
import flask
import json
from multiprocessing import Process
import subprocess
import argparse
from flask import Response
import io
import sys
import glob
from flask import jsonify
import os.path

from kwic import kwic_gen
from freqs import get_freqs 

import os
from collections import defaultdict
from os import path
from flask import Flask, request
dd = defaultdict(dict)



app = Flask(__name__)


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(THIS_DIR, "res")


def res_file(basename):
    return os.path.join(RES_DIR, basename)


def query_process(dbs, query, langs, ticket, limit=10000, case=False):


    print ('!!!', str(langs))
    limit = int(limit)
    try:


        inf = open('config.json','r')
        xx = json.load(inf)
        inf.close()

        allow_unlimited_limit = xx['allow_unlimited_limit']
        max_result_limit = xx['max_result_limit']

        if limit==0 and not allow_unlimited_limit:
            limit = max_result_limit 

        if limit > max_result_limit:
            limit = max_result_limit
    except:
        pass

    xdbs = get_flat_dbs()

    #Replace with call
    #open res file
    outf_err = open(res_file(ticket+'.err'),'w')


    xdb_string = []
    langs = langs.split(',')
    for x in dbs.split(','):
        print ('*!*',x, len(langs), langs)
        if len(langs) > 0 and len(langs[0]) > 0:
            langs_in_db = get_db_langs([x])
            if len(set(langs).intersection(set(langs_in_db))) > 0:
                print ("**")
                xdb_string.append(xdbs[x])
        else:
            print ('ebb')
            xdb_string.append(xdbs[x])
            
    db_string = ','.join(xdb_string)
    print ('!!', db_string, xdb_string)
    if len(db_string) < 1:
        db_string = xdbs[dbs]
    
    print (dbs)
    print ('!!', db_string)
    os.system('python3 res_cleaner.py &')
    langs = ','.join(langs)

    print (langs, db_string)
    if len(langs) > 0:
        if case:
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--langs', langs, '--case', query], cwd='../', stdout=subprocess.PIPE)
        else:
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--langs', langs,  query], cwd='../', stdout=subprocess.PIPE)
    else:
        if case:
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--case', query], cwd='../', stdout=subprocess.PIPE)
        else:
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4',  query], cwd='../', stdout=subprocess.PIPE)



    xoutf = open(res_file(ticket + '.json'),'wt')
    xoutf.write(json.dumps({'query':query, 'dbs':dbs, 'langs':langs, 'ticket':ticket, 'limit': limit}))
    xoutf.close()

    outf_files = {}
    from collections import defaultdict
    counts = defaultdict(int)
    step = 10
    buffer = bytes()
    langs = set()
    lang = '-'

    outfs = {}

    tree = []
    for l in p.stdout:
        try:
            l = l.decode('utf8')
        except:
            pass
        tree.append(l)

        if len(l)<1 or l.startswith('\n'):
            lang = 'unknown'
            if tree[0].startswith('# lang'):
                lang = tree[0].split(':')[-1].strip()
                if lang not in langs:
                    langs.add(lang)
                    xx = open(res_file(ticket + '.langs'), 'w')
                    xx.write(json.dumps(list(langs)))
                    xx.close()
                                
            
            if counts[lang]%10==0:
                if lang not in outfs.keys():
                    outfs[lang] = open(res_file(lang + '_' + ticket + '_' + str(round(counts[lang],-1)) + '.conllu'), 'a+t')
                else:
                    outfs[lang].close()
                    outfs[lang] = open(res_file(lang + '_' + ticket + '_' + str(round(counts[lang],-1)) + '.conllu'), 'a+t')                    
            counts[lang] += 1
            for tl in tree:
                outfs[lang].write(tl)
            tree = []

    for of in outfs.keys():
        outfs[of].close()
    
    outf = open(res_file(ticket+'.done'),'w')
    outf.close()                    
    
@app.route('/do_query/<dbs>/<query>/<m>/<langs>/')
def xxquery_process(dbs, query, m, langs):

    xdbs = get_flat_dbs()

    limit = 5000
    if len(langs) > 0:
        p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', m, '--langs', langs, query], cwd='../', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', m, query], cwd='../', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def generate():
        for oo in p.stdout:
            yield oo

    return Response(generate(), mimetype='text')



#https://stackoverflow.com/questions/34344836/will-hashtime-time-always-be-unique
def unique_id():
    return str(hash(time.time()))

@app.route('/static/<path:path>')
def send_js(path):
    print (path)
    return send_from_directory('static', path)

@app.route("/")
def mnf():
    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close()

    approot = xx['approot']

    return render_template("qx_hack.html", approot=approot)


@app.route('/get_dbs_json')
def gdsb():
    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()



    xpx = []
    dd = defaultdict(dict)
    for k in dbs.keys():
        init_path = dbs[k]#'/media/mjluot/b4ce4977-6aa1-44b2-87c1-bc149e48af35/dx/ndep_search/dep_search/PBs/'
        if not init_path.endswith('/'):
            init_path += '/'
        dx = dd
        root = k
            
        if path.exists(os.path.join(init_path, "db_config.json")):
            dd[root] = init_path
        else:
            #dd[root] = {}
            for dirname, dirnames, filenames in os.walk(init_path):
                for subdirname in dirnames:
                    if os.path.isdir(os.path.join(dirname, subdirname)):
                        #print(os.path.join(dirname, subdirname))
                        dx = dd
                        for xx in os.path.join(dirname, subdirname).split('/')[len(init_path.split('/'))-2:-1]:
                            dx = dx[xx]
                        if path.exists(os.path.join(dirname, subdirname, "db_config.json")):
                            dx[os.path.join(dirname, subdirname).split('/')[-1]] = os.path.join(dirname, subdirname)
                        else:
                            if not isinstance(os.path.join(dirname, subdirname).split('/')[-1], str):
                                dx[os.path.join(dirname, subdirname).split('/')[-1]] = {}

        xxm = {}

    return jsonify(get_node_with_kids(dd, '')) 


def get_flat_dbs():


    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()

    flat_dict = {}

    xpx = []
    dd = defaultdict(dict)
    for k in dbs.keys():
        init_path = dbs[k]
        if not init_path.endswith('/'):
            init_path += '/'
        dx = dd
        root = k
            
        if path.exists(os.path.join(init_path, "db_config.json")):
            dd[root] = init_path
        else:
            dd[root] = {}
            for dirname, dirnames, filenames in os.walk(init_path):
                for subdirname in dirnames:
                    if os.path.isdir(os.path.join(dirname, subdirname)):
                        #print(os.path.join(dirname, subdirname))
                        dx = dd
                        for xx in os.path.join(dirname, subdirname).split('/')[len(init_path.split('/'))-2:-1]:
                            dx = dx[xx]
                        if path.exists(os.path.join(dirname, subdirname, "db_config.json")):
                            dx[os.path.join(dirname, subdirname).split('/')[-1]] = os.path.join(dirname, subdirname)
                            flat_dict[os.path.join(dirname, subdirname).split('/')[-1]] = os.path.join(dirname, subdirname)
                        else:
                            if not isinstance(os.path.join(dirname, subdirname).split('/')[-1], str):
                                dx[os.path.join(dirname, subdirname).split('/')[-1]] = {}

        xxm = {}


    return flat_dict




def get_node_with_kids(dd, xid):
    import natsort
    tr = []
    for ixx, kid in enumerate(natsort.natsorted(dd.keys())):
        #is end node?
        if isinstance(dd[kid], str):
            if len(xid) > 0:
                tr.append({'id': str(kid), 'text': str(kid), 'children':[], "state": {"opened" : True}})
            else:
                tr.append({'id': str(kid), 'text': str(kid), 'children':[], "state": {"opened" : True}})
        else:
            if len(xid) > 0:
                tr.append({'id': str(kid), 'text': str(kid), 'children':get_node_with_kids(dd[kid], xid + '-' + str(ixx)), "state": {"opened" : False}})
            else:
                tr.append({'id': str(kid), 'text': str(kid), 'children':get_node_with_kids(dd[kid], xid + '-' + str(ixx)), "state": {"opened" : False}})
    return tr
    


    return json.dumps(xx)





@app.route("/get_dbs/")
def gdb():
    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()
    xx = []
    for k in dbs:
        xx.append(k)
    return json.dumps(xx)

@app.route("/get_langs/<db>")
def dbl(db):

    dbs = get_flat_dbs()
    
    inf = open(dbs[db] + '/langs', 'rt')
    
    xx = []
    for ln in inf:
        xx.append(ln.strip())

    inf.close()
    xx.sort()

    return jsonify(xx)

@app.route("/get_langs_post/", methods=['POST'])
def dbdl():

    dbs = request.form.getlist('data[]')
    return jsonify(get_db_langs(dbs))
    
def get_db_langs(dbs):
    fdbs = get_flat_dbs()
    xx = []
    for db in dbs:
        inf = open(fdbs[db] + '/langs', 'rt')
        for ln in inf:
            xx.append(ln.strip())

        inf.close()
        xx.sort()

    return xx





def file_generator_lang(ticket, lang):

    step = 10
    c = 0
    while True:
        fname = res_file(lang + '_' + ticket + '_' + str(c) + '.conllu')
        if not os.path.isfile(fname):
            break
        inf = open(fname, 'r')
        for l in inf:
            yield l
        inf.close()
        c += step
        

def file_generator(ticket):

    files = glob.glob(res_file('*'+ticket+'*.conllu'))
    files.sort()

    sent_files = set()
    while True:

        #
        for f in files:
            inf = open(f,'r')
            for l in inf:
                yield l
            inf.close()
            sent_files.add(f)

        #
        xfiles = set(glob.glob(res_file('*'+ticket+'*.conllu')))
        xx = xfiles - sent_files
        if len(xx) > 0:
            #
            files = list(xx)
        else:
            break


@app.route("/download/<ticket>")
def dl(ticket):

    content_gen = file_generator(ticket)
    response = Response(stream_with_context(content_gen))

    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + ticket + '.conllu'

    return response


@app.route("/download/<ticket>/<lang>")
def dll(ticket, lang):

    content_gen = file_generator_lang(ticket, lang)
    response = Response(stream_with_context(content_gen))

    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + lang + '_' + ticket + '.conllu'

    return response

@app.route("/kwic_download/<ticket>")
def kdl(ticket):

    content_gen = kwic_gen(res_file('*' + ticket + '*.conllu'))
    response = Response(stream_with_context(content_gen))

    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + ticket + '.tsv'

    return response


@app.route("/kwic_download/<ticket>/<lang>")
def kdll(ticket, lang):

    content_gen = kwic_gen(res_file(lang + '_' + ticket + '*.conllu'))
    response = Response(stream_with_context(content_gen))

    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + lang + '_' + ticket + '.tsv'

    return response

@app.route("/freqs/<ticket>/<lang>")
def fr(ticket, lang):

    return jsonify(get_freqs(res_file(lang + '_' + ticket + '*.conllu')))

@app.route("/freqs/<ticket>")
def ffr(ticket):

    freqs = get_freqs(res_file('*' + ticket + '*.conllu'))
    return json.dumps(freqs, indent=4, sort_keys=True)
    #return jsonify(get_freqs('./res/*' + ticket + '*.conllu'))

'''
@app.route("/start_query/<dbs>/<query>/<langs>/<limit>")
def hello_q(dbs, query, langs, limit):

    print ("YYY")
    #./start_query/pb/minä//10000/false


    ticket = unique_id()
    p = Process(target=query_process, args=(dbs,query, langs, ticket, limit))
    p.start()
    return ticket
'''

@app.route("/start_query/<dbs>/<query>/<limit>/<case>")
def hello_qc(dbs, query, limit, case):

    langs = ''

    case = case=='true'
    ticket = unique_id()
    p = Process(target=query_process, args=(dbs,query, langs, ticket, limit, case))
    p.start()
    return ticket

@app.route("/start_query/<dbs>/<query>/<langs>/<limit>/<case>")
def hello_qcc(dbs, query, langs, limit, case):

    case = case=='true'

    ticket = unique_id()
    p = Process(target=query_process, args=(dbs,query, langs, ticket, limit, case))
    p.start()
    return ticket




@app.route("/query_info/<ticket>")
def qinf(ticket):
    try:
        inf = open(res_file(ticket + '.json'),'rt')
        rr = inf.read()
        inf.close()
    except:
        rr = '{}'
    return rr

@app.route("/kill_query/<ticket>")
def kill_q(ticket):
    return ticket

@app.route("/get_result_count/<ticket>")
def get_res_count(ticket):


    #fi_2304882037610770081_167740.conllu

    files = glob.glob(res_file('*' + ticket + '*.conllu'))

    res = {}
    for f in files:
        lang = f.split('/')[-1].split('_')[0]
        number = int(f.split('/')[-1].split('_')[-1].split('.')[0])
        if lang not in res.keys():
            res[lang] = 0
        if number > res[lang]:
            res[lang] = number

    tr = []
    for k in res.keys():
        if res[k] < 1:
            tr.append(k)
    for k in tr:
        del res[k]

    return jsonify(res)


    '''
    res = 0
    files = glob.glob('./res/' + ticket + '*.conllu')
    files.sort()
    if len(files) > 0:
        res = int(files[-1].split('_')[-1].split('.')[0])

    inf = open(files[-1],'rt')
    stuff = inf.readlines()
    inf.close()
    for l in stuff:
        if '# hittoken:' in l:
            res += 1
    return json.dumps(res)
    '''

@app.route("/is_query_finished/<ticket>")
def gxet_res_count(ticket):
    if os.path.exists(res_file(ticket+'.done')):
        return jsonify(True)
    else:
        return jsonify(False)

@app.route("/get_result_langs/<ticket>")
def get_langs(ticket):

    langs = set()
    try:
        xx = open(res_file(ticket + '.langs'), 'r')
        langs = json.load(xx)
        xx.close()
    except:
        langs = []
    return jsonify(list(langs))

@app.route("/get_tree_count/<ticket>/<lang>/")
def get_tree_count(ticket, lang):

    trees = 0

    curr_tree = []
    inf = open(res_file(ticket),'rt')
    for l in inf:
        curr_tree.append(l)
        if l == '\n':
            for c in curr_tree:
                if c.startswith('# lang:') and lang in c:
                    trees += 1
            curr_tree = []

    return json.dumps(trees)


@app.route("/show/<ticket>/<lang>/<int:start>/<int:end>")
def get_xtrees(ticket, lang, start, end):


    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close()

    approot = xx['approot']


    trees = []

    tc = 0
    curr_tree = []
    '''
    inf = open('./res/' + ticket,'rt')
    for l in inf:
        curr_tree.append(l)
        if l == '\n':
            
            for c in curr_tree:
                if c.startswith('# lang: ' + lang):
                    if tc <= end and tc >= start:
                        trees.append(''.join(curr_tree[:]))
                    if tc > end:
                        break
                    tc += 1
            curr_tree = []
    '''      
    if lang == 'undefined':
        #
        try:
            inf = open(res_file(ticket+'.json'), 'r')
            db = json.load(inf)
            db = db["dbs"]
            inf.close()

            dbs = get_flat_dbs()

            for dib in db.split(','):
                inf = open(dbs[dib] + '/langs', 'rt')
                xx = []
                for ln in inf:
                    xx.append(ln.strip())

                inf.close()
            return render_template('query.html', start=start, end=end, lang=xx[0], idx=ticket, approot=approot)
        except:
            return render_template("qx_hack.html", approot=approot)


  
    return render_template('query.html', start=start, end=end, lang=lang, idx=ticket, approot=approot)

'''
@app.route("/get_trees/<ticket>/<lang>/<int:start>/<int:end>")
def get_trees(ticket, lang, start, end):

    trees = []

    tc = 0
    curr_tree = []
    inf = open('./res/' + ticket,'rt')
    for l in inf:
        curr_tree.append(l)
        if l == '\n':
            
            for c in curr_tree:
                if c.startswith('# lang: ' + lang) or (c.startswith('# lang: ') and lang in c):
                    if tc <= end and tc >= start:
                        trees.append(''.join(curr_tree[:]))
                    if tc > end:
                        break
                    tc += 1
            curr_tree = []

    src = ''.join(trees).split('\n')
    ret = flask.render_template(u"result_tbl.html",trees=yield_trees(src))

    return ret
'''


@app.route("/get_trees/<ticket>/<lang>/<int:start>/<int:end>")
def get_trees(ticket, lang, start, end):

    trees = []

    tc = 0
    curr_tree = []
    its_on = False

    #lets find a starting point
    files = glob.glob(res_file(lang + '_' + ticket + '*.conllu'))
    files.sort()
    prev = ''
    filelist = []
    for f in files:
        #print (int(f.split('_')[-1].split('.')[0]), start, end, (int(f.split('_')[-1].split('.')[0]) >= int(start)) and (int(f.split('_')[-1].split('.')[0]) <= int(end)))
        if (int(f.split('_')[-1].split('.')[0]) >= int(start)) and (int(f.split('_')[-1].split('.')[0]) < int(end)):
            filelist.append(f)

    for f in filelist:
        inf = open(f,'rt')
        '''
        for l in inf:
            curr_tree.append(l)
            if l == '\n':
                for c in curr_tree:
                    if c.startswith('# lang: ' + lang) or (c.startswith('# lang: ') and lang in c):
                        #if tc > start_tree - start:
                        trees.append(''.join(curr_tree[:]))
                        #if tc > start-end:
                        #    break
                        tc += 1
                curr_tree = []
        '''
        trees.extend(inf.readlines())
        inf.close()

    src = ''.join(trees).split('\n')
    ret = flask.render_template(u"result_tbl.html",trees=yield_trees(src))

    return ret

@app.route("/get_page_tree_count/<ticket>/<lang>/<int:start>/<int:end>")
def get_page_tree_count(ticket, lang, start, end):

    trees = []

    tc = 0
    curr_tree = []
    its_on = False

    #lets find a starting point
    files = glob.glob(res_file(lang + '_' + ticket + '*.conllu'))
    files.sort()
    prev = ''
    filelist = []
    for f in files:
        #print (int(f.split('_')[-1].split('.')[0]), start, end, (int(f.split('_')[-1].split('.')[0]) >= int(start)) and (int(f.split('_')[-1].split('.')[0]) <= int(end)))
        if (int(f.split('_')[-1].split('.')[0]) >= int(start)) and (int(f.split('_')[-1].split('.')[0]) < int(end)):
            filelist.append(f)

    for f in filelist:
        inf = open(f,'rt')
        '''
        for l in inf:
            curr_tree.append(l)
            if l == '\n':
                for c in curr_tree:
                    if c.startswith('# lang: ' + lang) or (c.startswith('# lang: ') and lang in c):
                        #if tc > start_tree - start:
                        trees.append(''.join(curr_tree[:]))
                        #if tc > start-end:
                        #    break
                        tc += 1
                curr_tree = []
        '''
        trees.extend(inf.readlines())
        inf.close()

    count = 0
    for l in trees:
        if l.startswith('# hittoken:'): count += 1

    return jsonify(count)


@app.route("/get_err/<ticket>")
def get_err(ticket):

    trees = []

    tc = 0
    curr_tree = []
    inf = open(res_file(ticket+'.err'),'rt')
    err = inf.read()
    inf.close()

    #Syntax error at the token 'ccc' HERE: 'ccc '...

    to_return = ''
    if "Syntax error" in err:
        to_return = err.split('redone_expr.ExpressionError:')[1].split('During')[0]
    return err

@app.route("/tget_trees/<ticket>/<lang>/<int:start>/<int:end>")
def tget_trees(ticket, lang, start, end):

    trees = []

    tc = 0
    curr_tree = []
    inf = open(res_file(ticket),'rt')
    for l in inf:
        curr_tree.append(l)
        if l == '\n':
            
            for c in curr_tree:
                if c.startswith('# lang: ' + lang):
                    if tc <= end and tc >= start:
                        trees.append(''.join(curr_tree[:]))
                    tc += 1
            curr_tree = []
            
    return json.dumps(''.join(trees))


def yield_trees(src):
    current_tree=[]
    current_comment=[]
    current_context=u""
    for line in src[:-1]:
        if line.startswith(u"# visual-style"):
            current_tree.append(line)
        elif line.startswith(u"# URL:"):
            current_comment.append(Markup(u'<a href="{link}">{link}</a>'.format(link=line.split(u":",1)[1].strip())))
        elif line.startswith(u"# context-hit"):
            current_context+=(u' <b>{sent}</b>'.format(sent=flask.escape(line.split(u":",1)[1].strip())))
        elif line.startswith(u"# context"):
            current_context+=(u' {sent}'.format(sent=flask.escape(line.split(u":",1)[1].strip())))
        elif line.startswith(u"# hittoken"):
            current_tree.append(line)
        elif not line.startswith(u"#"):
            current_tree.append(line)
        if line==u"":
            current_comment.append(Markup(current_context))
            yield u"\n".join(current_tree), current_comment
            current_comment=[]
            current_tree=[]
            current_context=u""


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--port', type=int, default=8089, help='Port. Default %(default)d.')
    parser.add_argument('--host', default='127.0.0.1', help='Host. Default %(default)s.')
    parser.add_argument('--debug', default=False, action="store_true", help='Flask debug mode')
    args = parser.parse_args()
    app.run(host=args.host, port=args.port,debug=args.debug)
