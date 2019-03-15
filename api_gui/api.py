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

app = Flask(__name__)


def query_process(dbs, query, langs, ticket):

    inf = open('dbs.json','rt')
    xdbs = json.load(inf)
    inf.close()

    #Replace with call
    #open res file
    outf = open('res/'+ticket,'w')
    outf_err = open('res/'+ticket+'.err','w')


    #query_py = 'cd ..;python3 query.py'
    #cmd = query_py + ' -d "' + xdbs[dbs] + '" -m 0 --langs ' + langs + ' "' + query + '"'
    #os.system(cmd + ' > ./api_gui/res/' + ticket + ' &')
    limit = 5000


    if len(langs) > 0:
        p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', str(limit), '--langs', langs, query], cwd='../', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        p = subprocess.Popen(['python3', 'query.py', '-d', xdbs[dbs], '-m', str(limit), query], cwd='../', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


    xoutf = open('./res/' + ticket + '.json','wt')
    xoutf.write(json.dumps({'query':query, 'dbs':dbs, 'langs':langs, 'ticket':ticket}))
    xoutf.close()

    '''
    for l, err in p.communicate():
        #write to res file
        try:
            outf.write(l.decode('utf8'))
            outf.flush()

            outf_err.write(err.decode('utf8'))
            outf_err.flush()
        except:
            pass
        #flush!!
    #print (cmd)
    outf.close()
    '''

    for l in p.stdout:
        #write to res file
        try:
            outf.write(l.decode('utf8'))
            outf.flush()
        except:
            pass

    for l in p.stderr:
        #write to res file
        try:
            outf_err.write(l.decode('utf8'))
            outf_err.flush()
        except:
            pass


        #flush!!
    #print (cmd)
    outf.close()



    #mark its done!
    outf = open('res/'+ticket+'.done','w')
    outf.close()


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


@app.route("/get_dbs")
def gdb():
    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()
    xx = []
    print (dbs)
    for k in dbs:
        xx.append(k)
    return jsonify(xx)

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
    print (xx)
    return jsonify(xx)

@app.route("/start_query/<dbs>/<query>/<langs>")
def hello_q(dbs, query, langs):

    ticket = unique_id()
    p = Process(target=query_process, args=(dbs,query, langs, ticket))
    p.start()
    return ticket

@app.route("/start_query/<dbs>/<query>/")
def hello_qc(dbs, query):

    langs = ''
    ticket = unique_id()
    p = Process(target=query_process, args=(dbs,query, langs, ticket))
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
    inf = open('./res/' + ticket,'rt')
    stuff = inf.readlines()
    inf.close()
    res = 0
    for l in stuff:
        if '# hittoken:' in l:
            res += 1
    return jsonify(res)

@app.route("/is_query_finished/<ticket>")
def gxet_res_count(ticket):
    if os.path.exists('res/'+ticket+'.done'):
        return jsonify(True)
    else:
        return jsonify(False)

@app.route("/get_result_langs/<ticket>")
def get_langs(ticket):

    langs = set()

    curr_tree = []
    inf = open('./res/' + ticket,'rt')
    for l in inf:
        curr_tree.append(l)
        if l == '\n':
            for c in curr_tree:
                if c.startswith('# lang: '):
                    langs.add(c.split(':')[1].strip())
            curr_tree = []

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

    return jsonify(trees)


@app.route("/show/<ticket>/<lang>/<int:start>/<int:end>")
def get_xtrees(ticket, lang, start, end):

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
            
    return render_template('query.html', start=start, end=end, lang=lang, idx=ticket)


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
                    tc += 1
            curr_tree = []

    src = ''.join(trees).split('\n')
    ret = flask.render_template(u"result_tbl.html",trees=yield_trees(src))

    return ret

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
            
    return jsonify(''.join(trees))


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
