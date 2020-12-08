from flask import stream_with_context, Response
import json
from flask import Flask, jsonify, Markup
import os
import time
from flask import render_template, send_from_directory, make_response, redirect
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
import os
from kwic import kwic_gen
from freqs import get_freqs 
import time
import os
from collections import defaultdict
from os import path
from flask import Flask, request
import hashlib
from werkzeug.utils import secure_filename, escape
import uuid
from dep_search import redone_expr
dd = defaultdict(dict)




app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RES_DIR = os.path.join(THIS_DIR, "res")


def get_uuid():
    uu = uuid.uuid4()
    return str(uu)


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
        if len(langs) > 0 and len(langs[0]) > 0:
            langs_in_db = get_db_langs([x])
            if len(set(langs).intersection(set(langs_in_db))) > 0:
                xdb_string.append(xdbs[x])
        else:
            xdb_string.append(xdbs[x])
            
    db_string = ','.join(xdb_string)
    if len(db_string) < 1:
        db_string = xdbs[dbs]
    
    os.system('python3 res_cleaner.py &')
    langs = ','.join(langs)


    print ('case2', type(case))
    if len(langs) > 0:
        if case == 'true':
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--langs', langs, '--chop_dir', RES_DIR, '--chop_ticket', ticket, '--case', query], cwd='../')
            print (' '.join(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--langs', langs, '--chop_dir', RES_DIR, '--chop_ticket', ticket, '--case', query]))
        else:
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--langs', langs, '--chop_dir', RES_DIR, '--chop_ticket', ticket,  query], cwd='../')
            print (' '.join(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--langs', langs, '--chop_dir', RES_DIR, '--chop_ticket', ticket,  query]))
    else:
        if case == 'true':
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--chop_dir', RES_DIR, '--chop_ticket', ticket, '--case', query], cwd='../')
            print (' '.join(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--chop_dir', RES_DIR, '--chop_ticket', ticket, '--case', query]))
        else:
            p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--chop_dir', RES_DIR, '--chop_ticket', ticket,  query], cwd='../')
            print (' '.join(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--chop_dir', RES_DIR, '--chop_ticket', ticket,  query]))

    #oug = open(res_file("ticket.res"), 'wb')
    #p = subprocess.Popen(['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--chop_dir', RES_DIR, '--chop_ticket', ticket , query], cwd='../')
    
    #print ('!!!!!', ['python3', 'query.py', '-d', db_string, '-m', str(limit), '--context', '4', '--chop_dir', RES_DIR, '--chop_ticket', ticket , query])
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

    err_out = open(res_file(ticket + '_err'), 'wb')
    '''
    for l in p.stderr:
        print (l)
        if b'compiled' in l :break
        if b"redone_expr.ExpressionError" in l:
            err_out.write(l.split(b':')[1])
        if l.startswith(b"HERE"):
            err_out.write(l)
            break
    '''        
    err_out.close()

    tree = []
    print ('FUGG')
    empty_cnt = 0
    #p.wait()
    '''
    while True:
        print ('poll', p.poll())   
        l = p.stdout.readline()
        l = l.decode('utf8')
        print (l)
        if len(l) < 1:
            empty_cnt += 1
            if empty_cnt > 10:
                print ('!!!') 
                break
            continue
        else:
            empty_cnt = 0
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
    '''
    p.wait()
    print ('END')    
    outf = open(res_file(ticket+'.done'),'w')
    outf.close()                    

def get_passhash(passw):
    salt = 'erthya!!!4235'
    return hashlib.sha256(salt.encode() + passw.encode()).hexdigest()

@app.route('/login', methods=['POST'])
def signin():
    passw = request.form['pass']
    passhash = get_passhash(passw)

    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close()
    if xx['admin_pass'] == passhash or (xx['admin_pass'] == ''):
        session_id = get_uuid()
        outf = open('sessions', 'wt')
        outf.write(session_id + '\t' + str(time.time() + 60*60*3))

        res = make_response(redirect("/db_config"))
        res.set_cookie("session_id", value=session_id)
        return res
    else:
        return render_template('login.html')

@app.route('/change_pw', methods=['POST'])
def cshange_pw():

    passw = request.form['pass']
    passhash = get_passhash(passw)
    
    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close()
    
    if check_creds(request):
        xx['admin_pass'] = passhash
        outf = open('config.json','wt')
        outf.write(json.dumps(xx))
        outf.close()
        return redirect(xx['approot'] + "/db_config")
    else:
        return render_template("login.html", approot=xx['approot'])


@app.route('/remove_db/<db_name>')
def rmdb(db_name):

    db_r = db_name
    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close()
    
    fd = get_flat_dbs()

    if check_creds(request):
        os.system('rm -rf ' + fd[db_r])
        os.system('cd ..; python3 docker_add_dbs.py')
        return redirect(xx['approot'] + "/db_config")
    else:
        return render_template("login.html", approot=xx['approot'])

@app.route('/index_db', methods=['POST'])
def chansge_pw():

    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close()
    
    db_name = request.form['name']
    db_lang = request.form['lang']
    
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(xx['db_folder'] + filename)    

    if check_creds(request):
        outf = open('index_' + filename + '.sh','wt')
        outf.write('cd ..; cat ' + xx['db_folder'] + filename + ' | python3 build_index.py -d ' + xx['db_folder'] + '/' + db_name + ' --lang ' + db_lang + ' 2>&1 > ' + xx['db_folder'] + filename + '.log\n')
        outf.write('python3 docker_add_dbs.py\n')
        outf.close()
        os.system('chmod +x ' + 'index_' + filename + '.sh')
        os.system('sh ' + 'index_' + filename + '.sh &')
        #os.system('cd ..; cat ' + xx['db_folder'] + filename + ' | python3 build_index.py -d ' + xx['db_folder'] + '/' + db_name + ' --lang ' + db_lang + ' 1&2> ' + xx['db_folder'] + filename + '.log')
        #os.system('cd ..; python3 docker_add_dbs.py')
        
    return redirect(xx['approot'] + "/check_index/" + filename + '.log')


@app.route('/check_index/<filename>')
def rrt(filename):
    if check_creds(request):
        inf = open('config.json', 'r')
        xx = json.load(inf)
        inf.close()
        inf = open(xx['db_folder'] + filename,'rt')
        ff = inf.read()
        ff = ff.replace('\n','<br>')
        inf.close()
    return render_template('check_log.html', log=ff)

@app.route('/db_config')
def db_config():

    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close() 

    xxx = ''
    dd = get_flat_dbs()
    for k in dd.keys():
        #
        #xxx += '<a href=' + xx['approot'] + '/remove_db/' + k + '>Remove ' + k + '</a><br>'
        xxx += '<input type="button" value="Remove ' + k + '" onclick="if(window.confirm(\'Sure?\')){window.location = \'' + xx['approot'] + '/remove_db/' + k + '\';}" /><br>'


    if check_creds(request):
        return render_template("db_config.html", approot=xx['approot'], dbs=xxx)
    return render_template('login.html', approot=xx['approot'])


def check_creds(req):
    
    try:
        inf = open('config.json', 'r')
        xx = json.load(inf)
        inf.close()

        session_id = req.cookies.get('session_id')
        
        inf = open('sessions','rt')
        xln = inf.readline()
        inf.close()
        right_sess_id, xtime = xln.strip().split('\t')
        print (session_id, right_sess_id, float(xtime) > time.time())
        if session_id == right_sess_id and time.time() < float(xtime) and xx['allow_remote_admin']:
            return True
        else:
            return False
    except:
        return False

    
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

    return jsonify(get_node_with_kids(dbs, '')) 

def flatten(current, key='', result=dict()):
    if isinstance(current, dict):
        for k in current:
            new_key = k
            flatten(current[k], new_key, result)
    else:
        result[key] = current
    return result


def get_flat_dbs():


    inf = open('dbs.json','rt')
    dbs = json.load(inf)
    inf.close()

    flat_dict = flatten(dbs)
        

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
    print (fdbs)
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



@app.route("/freqs/<ticket>")
def ffr(ticket):

    ret = get_freqs(res_file('*_' + ticket + '*.conllu'))
    relx = ["dependent_words","dependent_lemmas", "left_words","left_lemmas", "right_words","right_lemmas","parent_words","parent_lemmas","deptypes_as_dependent","deptypes_as_parent","hit_words","hit_lemmas"]    
    return render_template('freqs.html', ret=ret, relx=relx, xurl="/json_freqs/" + ticket)

@app.route("/freqs/<ticket>/<lang>")
def frf(ticket, lang):

    ret = get_freqs(res_file(lang + '_' + ticket + '*.conllu'))
    relx = ["dependent_words","dependent_lemmas", "left_words","left_lemmas", "right_words","right_lemmas","parent_words","parent_lemmas","deptypes_as_dependent","deptypes_as_parent","hit_words","hit_lemmas", "left_words","left_lemmas"]

    return render_template('freqs.html', ret=ret, relx=relx, xurl="/json_freqs/" + ticket + '/' + lang) 


@app.route("/json_freqs/<ticket>")
def fffr(ticket):

    ret = json.dumps(get_freqs(res_file('*_' + ticket + '*.conllu')), indent=4, sort_keys=True)
    resp = Response(response=ret,
                    status=200,
                    mimetype="application/json")    
    return resp

@app.route("/json_freqs/<ticket>/<lang>")
def fr(ticket, lang):

    ret = json.dumps(get_freqs(res_file(lang + '_' + ticket + '*.conllu')), indent=4, sort_keys=True)
    resp = Response(response=ret,
                    status=200,
                    mimetype="application/json")    
    return resp



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

@app.route("/start_query/", methods=['POST'])
def start_post():


    dbs = request.form['dbs']
    query = request.form['query']
    langs = request.form['langs']
    limit = request.form['limit']
    case = request.form['case']


    print ('case', case)

    ticket = unique_id()
    print (dbs,query, langs, ticket, limit, case)    
    p = Process(target=query_process, args=(dbs,query, langs, ticket, limit, case))
    p.start()
    return ticket

from dep_search import redone_expr, get_tags

@app.route("/get_tags/", methods=['POST'])
def tagset():

    dbs = request.form['dbs']
    langs = request.form['langs']
    
    xdbs = get_flat_dbs()

    xdb_string = []
    langs = langs.split(',')
    for x in dbs.split(','):
        if len(langs) > 0 and len(langs[0]) > 0:
            langs_in_db = get_db_langs([x])
            if len(set(langs).intersection(set(langs_in_db))) > 0:
                xdb_string.append(xdbs[x])
        else:
            try:
                xdb_string.append(xdbs[x])
            except:
                pass
    
    dep_types, pos, tags = get_tags.get_tags_list(xdb_string)
    dep_types, pos, tags = list(dep_types), list(pos), list(tags)

    dep_types.sort()
    pos.sort()
    tags.sort()

    return jsonify([dep_types, pos, tags])

@app.route("/check_query_syntax/", methods=['POST'])
def chek_syn():
    query = request.form['query']
    return jsonify(redone_expr.check_and_give_error(query))

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

    try:
        files = glob.glob(res_file('*' + ticket + '*.conllu'))
        print (files)
        res = {}
        for f in files:
            lang = '_'.join(f.split('/')[-1].split('_')[:-2])
            number = int(f.split('/')[-1].split('_')[-1].split('.')[0])
            if lang not in res.keys():
                res[lang] = 0
            if number > res[lang]:
                res[lang] = number

        better_res = {}
        for k in res:
            ## lang_ticket_number
            inf = open(res_file(str(k) + '_' + ticket + '_' + str(res[k])+".conllu"), 'rt')
            cnt = 0
            for l in inf:
                if '# lang:' in l:
                    cnt += 1
            inf.close()
            better_res[k] = res[k] + cnt

        inf = open(res_file(ticket + '_err'),'rt')
        errors = inf.read()
        inf.close()
        if len(better_res) < 1 and len(errors) > 0: better_res = {'': errors}
    except:
        better_res = {}

    tr = []
    for k in better_res.keys():
        if better_res[k] < 1:
            tr.append(k)
    for k in tr:
        del better_res[k]

    return jsonify(better_res)


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
    langs = list(langs)    
    langs.sort()
    print (langs)
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

import time
@app.route("/show/<ticket>/<lang>/<start>/<end>")
def get_xtrees(ticket, lang, start, end):

    try:
        start = int(start)
        end = int(end)
    except:
        start = 0
        end = 10

    inf = open('config.json', 'r')
    xx = json.load(inf)
    inf.close()

    approot = xx['approot']


    trees = []

    tc = 0
    curr_tree = []
    try:
        inf = open(res_file(ticket+'.json'), 'r')
        inf.close()
    except:
        time.sleep(0.5)

    if lang == 'undefined':
        #
        try:
            inf = open(res_file(ticket+'.json'), 'r')
            db = json.load(inf)
            db = db["dbs"]
            inf.close()
        except:
            return render_template('query.html', start=start, end=end, lang=lang, idx=ticket, approot=approot)

        dbs = get_flat_dbs()

        for dib in db.split(','):
            inf = open(dbs[dib] + '/langs', 'rt')
            xx = []
            for ln in inf:
                xx.append(ln.strip())

            inf.close()
        return render_template('query.html', start=start, end=end, lang=xx[0], idx=ticket, approot=approot)
        #except:
        #    return render_template('query.html', start=0, end=(end-start), lang='unknown', idx=ticket, approot=approot)
  
    return render_template('query.html', start=start, end=end, lang=lang, idx=ticket, approot=approot)


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
