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

app = Flask(__name__)


def query_process(dbs, query, langs, ticket, limit=10000, case=False):



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

    inf = open('dbs.json','rt')
    xdbs = json.load(inf)
    inf.close()

    #Replace with call
    #open res file
    outf_err = open('res/'+ticket+'.err','w')


    #query_py = 'cd ..;python3 query.py'
    #cmd = query_py + ' -d "' + xdbs[dbs] + '" -m 0 --langs ' + langs + ' "' + query + '"'
    #os.system(cmd + ' > ./api_gui/res/' + ticket + ' &')

    os.system('python3 res_cleaner.py &')

    print('db', dbs)


    if len(langs) > 0:
        if case:
            p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', str(limit), '--context', '4', '--langs', langs, '--ticket', ticket, '--case', query], cwd='../', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=sys.stderr)
        else:
            p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', str(limit), '--context', '4', '--langs', langs, '--ticket', ticket,  query], cwd='../', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=sys.stderr)
    else:
        p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', str(limit) , '--context', '4', '--ticket', ticket ,query], cwd='../', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr)

        if case:
            p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', str(limit), '--context', '4', '--ticket', ticket, '--case', query], cwd='../', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=sys.stderr)
        else:
            p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', str(limit), '--context', '4', '--ticket', ticket,  query], cwd='../', stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=sys.stderr)




    xoutf = open('./res/' + ticket + '.json','wt')
    xoutf.write(json.dumps({'query':query, 'dbs':dbs, 'langs':langs, 'ticket':ticket, 'limit': limit}))
    xoutf.close()

    '''
    for l, err in p.communicate():
        #write to res file
        try:
            outf_err.write(err.decode('utf8'))
            outf_err.flush()
        except:
            pass

    outf.close()
    outf_err.close()
    '''

@app.route('/do_query/<dbs>/<query>/<m>/<langs>/')
def xxquery_process(dbs, query, m, langs):

    inf = open('dbs.json','rt')
    xdbs = json.load(inf)
    inf.close()

    #query_py = 'cd ..;python3 query.py'
    #cmd = query_py + ' -d "' + xdbs[dbs] + '" -m 0 --langs ' + langs + ' "' + query + '"'
    #os.system(cmd + ' > ./api_gui/res/' + ticket + ' &')
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
    return render_template("qx.html")


@app.route("/get_dbs/")
def gdb():
    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()
    xx = []
    print ('DB', dbs)
    for k in dbs:
        xx.append(k)
    print (json.dumps(xx))
    return json.dumps(xx)

@app.route("/get_langs/<db>")
def dbl(db):

    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()
    
    inf = open(dbs[db] + '/langs', 'rt')
    
    xx = []
    for ln in inf:
        xx.append(ln.strip())

    inf.close()
    xx.sort()

    print (xx)
    return jsonify(xx)


def file_generator_lang(ticket, lang):

    step = 10
    c = 0
    while True:
        fname = './res/' + lang + '_' + ticket + '_' + str(c) + '.conllu'
        if not os.path.isfile(fname):
            break
        inf = open(fname, 'r')
        for l in inf:
            yield l
        inf.close()
        c += step
        

def file_generator(ticket):

    files = glob.glob('./res/*'+ticket+'*.conllu')
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
        xfiles = set(glob.glob('./res/*'+ticket+'*.conllu'))
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

    content_gen = kwic_gen('./res/*' + ticket + '*.conllu')
    response = Response(stream_with_context(content_gen))

    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + ticket + '.tsv'

    return response


@app.route("/kwic_download/<ticket>/<lang>")
def kdll(ticket, lang):

    content_gen = kwic_gen('./res/'+lang + '_' + ticket + '*.conllu')
    response = Response(stream_with_context(content_gen))

    response.headers['Content-Type'] = "application/octet-stream"
    response.headers['Content-Disposition'] = "inline; filename=" + lang + '_' + ticket + '.tsv'

    return response

@app.route("/freqs/<ticket>/<lang>")
def fr(ticket, lang):

    return jsonify(get_freqs('./res/'+lang + '_' + ticket + '*.conllu'))

@app.route("/freqs/<ticket>")
def ffr(ticket):

    freqs = get_freqs('./res/*' + ticket + '*.conllu')
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

    print ('XXXX')
    langs = ''

    case = case=='true'
    ticket = unique_id()
    p = Process(target=query_process, args=(dbs,query, langs, ticket, limit, case))
    p.start()
    return ticket

@app.route("/start_query/<dbs>/<query>/<langs>/<limit>/<case>")
def hello_qcc(dbs, query, langs, limit, case):

    case = case=='true'
    print ('WBIN!')

    ticket = unique_id()
    p = Process(target=query_process, args=(dbs,query, langs, ticket, limit, case))
    p.start()
    return ticket




@app.route("/query_info/<ticket>")
def qinf(ticket):
    try:
        inf = open('./res/' + ticket + '.json','rt')
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

    files = glob.glob('./res/*' + ticket + '*.conllu')

    res = {}
    for f in files:
        lang = f.split('/')[-1].split('_')[0]
        number = int(f.split('/')[-1].split('_')[-1].split('.')[0])
        if lang not in res.keys():
            res[lang] = 0
        if number > res[lang]:
            res[lang] = number

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
    if os.path.exists('res/'+ticket+'.done'):
        return jsonify(True)
    else:
        return jsonify(False)

@app.route("/get_result_langs/<ticket>")
def get_langs(ticket):

    langs = set()

    xx = open('./res/' + ticket + '.langs', 'r')
    langs = json.load(xx)
    xx.close()

    return jsonify(list(langs))

@app.route("/get_tree_count/<ticket>/<lang>/")
def get_tree_count(ticket, lang):

    trees = 0

    curr_tree = []
    inf = open('./res/' + ticket,'rt')
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
        inf = open('res/'+ticket+'.json', 'r')
        db = json.load(inf)
        print (db)
        db = db["dbs"].split(',')[0]
        inf.close()

        inf = open('dbs.json','rt')
        dbs = json.load(inf)
        inf.close()

        inf = open(dbs[db] + '/langs', 'rt')

        xx = []
        for ln in inf:
            xx.append(ln.strip())

        inf.close()
        return render_template('query.html', start=start, end=end, lang=xx[0], idx=ticket, approot=approot)


  
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
    files = glob.glob('./res/' + lang + '_' + ticket + '*.conllu')
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
    files = glob.glob('./res/' + lang + '_' + ticket + '*.conllu')
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
    inf = open('./res/'+ticket+'.err','rt')
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
    inf = open('./res/' + ticket,'rt')
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
