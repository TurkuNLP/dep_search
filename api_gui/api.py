import json
from flask import Flask, jsonify, Markup
import os
import time
from flask import render_template, send_from_directory
from flask import Flask, Markup
import flask

app = Flask(__name__)

#https://stackoverflow.com/questions/34344836/will-hashtime-time-always-be-unique
def unique_id():
    return str(hash(time.time()))


@app.route('/static/<path:path>')
def send_js(path):
    print (path)
    return send_from_directory('static', path)



@app.route("/get_dbs")
def gdb(ticket):
    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()
    xx = []
    for k,v in dbs:
        xx.append(k)
    return jsonify(xx)

@app.route("/get_langs/<db>")
def dbl(db):

    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()
    
    inf = open(dbs[db] + '/langs', 'rt')
    
    xx = '[' + ','.join(inf.readlines()) + ']'
    inf.close()

    return xx

@app.route("/start_query/<dbs>/<query>/<langs>")
def hello_q(dbs, query, langs):


    #Replace with call

    ticket = unique_id()
    query_py = 'cd ..;python3 query.py'
    cmd = query_py + ' -d ' + dbs + ' -m 0 --langs ' + langs + ' ' + query
    os.system(cmd + ' > ./api_gui/res/' + ticket + ' &')

    return ticket

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
    return ticket

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
            
    return render_template('query.html')


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
                if c.startswith('# lang: ' + lang):
                    if tc <= end and tc >= start:
                        trees.append(''.join(curr_tree[:]))
                    tc += 1
            curr_tree = []

    src = ''.join(trees).split('\n')
    ret = flask.render_template(u"result_tbl.html",trees=yield_trees(src))

    return ret


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
    for line in src:
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



app.run(host='0.0.0.0', port= 81,debug=True)