#!/usr/bin/env python3

"""
This module handles all of the URL dispatching for guampa, mapping from
URLs to the functions that will be called in response.
"""
import json
import os

from flask import Flask, request, session, url_for, redirect, render_template,\
                  abort, g, flash, _app_ctx_stack, send_from_directory, jsonify
from werkzeug import check_password_hash, generate_password_hash

import model
import db
import utils
import urllib.parse

DEBUG = True
SECRET_KEY = 'development key'
app = Flask(__name__)
app.config.from_object(__name__)

## this file is in serverside, but we need one directory up.
myfn = os.path.abspath(__file__)
app.root_path = os.path.dirname(os.path.dirname(myfn)) + os.path.sep
app.debug = DEBUG

@utils.nocache
@app.route('/')
def index():
    return send_from_directory(app.root_path + 'app', 'index.html')

@app.route('/partials/<fn>')
def partials(fn):
    return send_from_directory(app.root_path + 'app/partials', fn)

@app.route('/css/<fn>')
def css(fn):
    return send_from_directory(app.root_path + 'app/css', fn)

@utils.nocache
@app.route('/js/<fn>')
def js(fn):
    return send_from_directory(app.root_path + 'app/js', fn)

@app.route('/img/<fn>')
def img(fn):
    return send_from_directory(app.root_path + 'app/img', fn)

@app.route('/lib/<fn>')
def lib(fn):
    return send_from_directory(app.root_path + 'app/lib', fn)

@app.route('/json/documents')
@utils.json
@utils.nocache
def documents():
    docs = db.list_documents()
    out = {'documents': [{'title': doc.title, 'id':doc.id} for doc in docs]}
    return(json.dumps(out))

@app.route('/json/tags')
@utils.json
@utils.nocache
def tags():
    tags = db.list_tags()
    out = {'tags': [tag.text for tag in tags]}
    return(json.dumps(out))

@app.route('/json/documents/<path:tagname>')
@utils.json
@utils.nocache
def documents_for_tag(tagname):
    tagname = urllib.parse.unquote(tagname)
    docs = db.documents_for_tagname(tagname)
    out = {'documents': [{'title': doc.title, 'id':doc.id} for doc in docs]}
    return(json.dumps(out))

@app.route('/json/document/<docid>')
@utils.json
@utils.nocache
def document(docid):
    """All the stuff you need to render a document in the editing interface."""
    docid = int(docid)

    sent_texts = []
    trans_texts = []

    ## sentence ids for which we've seen a translation
    have_translation = set()
    for (s,t) in db.sentences_with_translations_for_document(docid):
        if s.id in have_translation:
            continue
        else:
            sent_texts.append(s.text)
            if t:
                have_translation.add(s.id)
            translation_text = t.text if t else None
            trans_texts.append({'text':translation_text,
                                'sentenceid':s.id,
                                'docid':docid})
    out = {'docid': docid, 'sentences':sent_texts, 'translations':trans_texts}
    return(json.dumps(out))

@app.route('/json/add_translation', methods=['post'])
@utils.json
@utils.nocache
def add_translation():
    if g.user is None:
        abort(403)
    try:
        d = request.get_json()
        text = d['text']
        sentenceid = d['sentenceid']
        documentid = d['documentid']
        db.save_translation(g.user.id, documentid, sentenceid, text)
    except Exception as inst:
        import traceback
        traceback.print_exc()
        print("it was an exception somewhere")
        abort(500)
    return "OK"


def ts_format(timestamp):
    """Given a datetime.datetime object, format it. This could/should probably
    be localized."""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

@app.route('/json/sentencehistory/<sentenceid>')
@utils.json
@utils.nocache
def sentencehistory(sentenceid):
    """All the stuff you need to render the history of a sentence."""
    sentenceid = int(sentenceid)

    sentence = db.get_sentence(sentenceid)
    ## get all the translations and all the comments, sort them by timestamp.
    comments_users = db.things_for_sentence_with_user(sentenceid, model.Comment)
    translations_users = db.things_for_sentence_with_user(sentenceid,
                                                          model.Translation)
    items = []
    for (item, user) in comments_users:
        items.append({'text':item.text,'ts':ts_format(item.timestamp),
                      'username':user.username,'type':'comment'})
    for (item, user) in translations_users:
        items.append({'text':item.text,'ts':ts_format(item.timestamp),
                      'username':user.username, 'type':'translation'})
    out = {'docid': sentence.docid, 'text': sentence.text, 'items':items}
    return(json.dumps(out))

### Dealing with logins; demonstrates sessions and the g global.
### Need to make this work with Angular templating instead.
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = db.get_user(session['user_id'])

@app.route('/json/currentuser')
@utils.json
@utils.nocache
def currentuser():
    """Surface the currently logged in user to the client."""
    if g.user:
        out = {'username': g.user.username, 'fullname':g.user.fullname}
    else:
        out = {'username': None, 'fullname':None}
    return(json.dumps(out))

@app.route('/json/login', methods=['POST'])
@utils.json
@utils.nocache
def json_login():
    """Logs the user in."""
    d = request.get_json()
    username = d['username']
    password = d['password']

    user = db.lookup_username(username)
    ## also check password.
    if user is None:
        error = 'Invalid username'
        abort(403)
    else:
        session['user_id'] = user.id
        g.user = user
    return "OK"

@app.route('/json/logout')
@utils.json
@utils.nocache
def json_logout():
    """Logs the user out."""
    session.pop('user_id', None)
    return "OK"

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs the user in."""
    error = None
    if request.method == 'POST':
        username = request.form['username']
        user = db.lookup_username(username)
        if user is None:
            error = 'Invalid username'
        else:
            flash('You were logged in')
            session['user_id'] = user.id
            g.user = user # session['user_id']
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """Logs the user out."""
    flash('You were logged out')
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0')
