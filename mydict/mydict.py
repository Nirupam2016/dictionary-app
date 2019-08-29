#TO DO:
    #verify term doesn't exist yet
    #Delete term
    #display terms once even with multiple symbols/definitions
    #Display each symbolic term in term page
    #Apply dynamic entires to other term fields and to phrases and rules
    #error page for incorrect urls
    #check for empty fields, (verify non repeated information?)
    #allow removal of extra fields
    #romaji should seperate particles from words(for better auto matching terms
        #to phrases/rules)
    #implement rules and phrases pages
    #implement multiple sybolic terms for rules and phrases
    #implement tags(user defined?)
    #navigation, links between terms and term page
    #table of individual characters, match to words and phrases? efficient?
    #reduce code duplication, maybe OOP?
    #seperate functions into different files
    #easily clear data
    #auto load data?




import os
import pymysql.cursors
import re
import string
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
     render_template, flash

app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , mydict.py

DATABASE = '../mydict_DB.db'

# Load default config and override config from an environment variable
app.config.update(dict(
    USER='root',
    PASSWORD='Millie1997',
    HOST = 'localhost',
    DATABASE = 'jap_dict',
    SECRET_KEY = 'japdict key',
    CHARSET = 'utf8',
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)
config = {
    "user": "root",
    "password": "Millie1997",
    "host": "localhost",
    "database": "jap_dict",
    "charset": "utf8",
}

def connect_db(): 
    connection = pymysql.connect(**config)
    return connection

def get_db(): 
    """Opens a new d atabase connection if there is none yet for the
    current application context.
    """
    '''if not hasattr(g, 'mysql_db'):
        g.mysql_db = connect_db()
    return g.mysql_db'''
    
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db



@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    '''if hasattr(g, 'mysql_db'):
        g.mysql_db.close()'''
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

#clean up strings punctuation before matching, especially lterm to rules
def match_term_to_lterms(term,  cursor, term_id):
    term_search = '%' + term + '%'
    fetch_lterm_id = 'SELECT id FROM long_term \
            WHERE long_term LIKE %s'
    cursor.execute(fetch_lterm_id, (term_search))
    lterm_id_list = cursor.fetchall()

    try:
        for lterm_id in lterm_id_list:
            sql = 'INSERT INTO term_long_term_join \
                    VALUES (%s, %s)'
            cursor.execute(sql, (term_id, lterm_id))
        flash('word matched to phrases successfully')
    except:
        flash('error with matching word to phrases')

def match_term_to_rules(term,  cursor, term_id):
    term_search = '%' + term + '%'
    fetch_rule_id = 'SELECT id FROM rule \
            WHERE rule LIKE %s'
    cursor.execute(fetch_rule_id, (term_search))
    rule_id_list = cursor.fetchall()

    try:
        for rule_id in rule_id_list:
            sql = 'INSERT INTO term_rule_join \
                    VALUES (%s, %s)'
            cursor.execute(sql, (term_id, rule_id))
        flash('word matched to rules successfully')
    except:
        flash('error with matching word to rules')


def match_lterm_to_terms(lterm, cursor, lterm_id):
    lterm_terms = re.sub('['+string.punctuation+']', '',lterm).split()

#need to deal with terms included but not seperated by spaces, 
#e.g watashiwa, genkidesu
    try:
        for term in lterm_terms:
            fetch_term_id = 'SELECT id FROM term \
                    WHERE term = %s'
            cursor.execute(fetch_term_id, (term))

            term_id_list = cursor.fetchall()

            #need to deal with duplicate words in a phrase,
            #getting matched multiple times
            for term_id in term_id_list:
                sql = 'INSERT INTO term_long_term_join \
                    VALUES (%s, %s)'
                cursor.execute(sql, (term_id, lterm_id))
        flash('phrase matched to words successfully')
    except:
        flash('error matching phrase to words')

def match_lterm_to_rules(lterm, cursor, lterm_id):
    get_rules = "select id, rule from rule"
    cursor.execute(get_rules)
    rules = cursor.fetchall()

    try:
        for rule in rules:
            rule_comp = rule[1].split("~")
            comp_pattern = [".*?"]

            for comp in rule_comp:
                comp_pattern.append(comp + ".*?")

            comp_pattern_str = "".join(comp_pattern)

            matched = re.match(comp_pattern_str, lterm)

            if matched:
                sql = 'INSERT INTO long_term_rule_join \
                    VALUES (%s, %s)'
                cursor.execute(sql, (lterm_id, rule[0]))
        flash("phrase matched to rules successfuly")
    except:
        flash('error matching phrase to rules')


def match_rule_to_terms(rule, cursor, rule_id):

    rule_terms = re.sub('['+string.punctuation+']', '',rule).split()
    flash(rule_terms)

    try:
        for term in rule_terms:
            fetch_term_id = 'SELECT id FROM term \
                    WHERE term = %s'
            cursor.execute(fetch_term_id, (term))

            term_id_list = cursor.fetchall()
            #need to deal with duplicate words in a rule/phrase

            for term_id in term_id_list:
                sql = 'INSERT INTO term_rule_join \
                    VALUES (%s, %s)'
                cursor.execute(sql, (term_id, rule_id))
        flash('phrase matched to words successfully')
    except:
        flash('error matching phrase to words')

def match_rule_to_lterms(rule, cursor, rule_id):
    rule_comp = rule.split("~")
    comp_search = ["%"]

    for comp in rule_comp:
        comp_search.append(comp + "%")

    comp_search_str = "".join(comp_search)
    flash(comp_search_str)

    try:
        fetch_lterm_id = 'SELECT id FROM long_term \
                WHERE long_term LIKE %s'
        cursor.execute(fetch_lterm_id, (comp_search_str))

        lterm_id_list = cursor.fetchall()

        for lterm_id in lterm_id_list:
            sql = 'INSERT INTO long_term_rule_join \
                VALUES (%s, %s)'
            cursor.execute(sql, (lterm_id, rule_id))
        flash('rule matched to phrases successfully')
    except:
        flash('error matching rule to phrases')


def return_term_id(term, cursor):
    sql = 'SELECT id FROM term WHERE term = %s'
    cursor.execute(sql, (term))
    term_id = cursor.fetchall()
    return term_id


@app.route('/terms')
def show_terms():
    db = get_db()
    cursor = db.cursor()

    sql = 'select distinct term.term, symbolic_term.symb_term, term_def.def, \
           term_def.long_def \
           from term  \
           left join term_def \
           on term.id = term_def.term_id \
           left join symbolic_term \
           on term.id = symbolic_term.term_id \
           order by term.term'

    cursor.execute(sql)
    entries = cursor.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/lterms')
def show_phrases():
    db = get_db()
    cursor = db.cursor()

    sql = 'select long_term.long_term, symbolic_long_term.symb_long_term, \
           long_term.def, long_term.long_def \
           from long_term \
           left join symbolic_long_term \
           on long_term.id = symbolic_long_term.long_term_id'

    cursor.execute(sql)
    entries = cursor.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/rules')
def show_rules():
    db = get_db()
    cursor = db.cursor()

    sql = 'select rule.rule, symbolic_rule.symb_rule, \
           rule.def, rule.long_def \
           from rule \
           left join symbolic_rule \
           on rule.id = symbolic_rule.rule_id'

    cursor.execute(sql)
    entries = cursor.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/add')
def form_entries():
    return render_template ('add_entries.html')


@app.route('/insert_term', methods = ['POST'])
def insert_term():
    db = get_db()
    cursor = db.cursor()

    ent_term = request.form['term']
    print("testing1")
    #ent_symbs_init = request.form.getlist('symb_term0')
    ent_symbs = request.form.getlist('symb_term')
    #print(ent_symbs_init)
    print(ent_symbs)
    print("testing")
    ent_def = request.form['def']
    ent_long_def = request.form['long_def']
    term_sql = 'INSERT INTO term (term) VALUES (?)'
    term_def_sql = 'insert into term_def (term_id, def, long_def) \
            values (?, ?, ?)'
    term_symb_sql = 'insert into symbolic_term (term_id, symb_term) \
            values (?, ?)'

    try:
        cursor.execute(term_sql, (ent_term,))
        term_id = cursor.lastrowid
        cursor.execute(term_def_sql, (term_id, ent_def, ent_long_def,))
        for symbol in ent_symbs:
            cursor.execute(term_symb_sql, (term_id, symbol))
        #match_term_to_lterms(ent_term, cursor, term_id)
        #match_term_to_rules(ent_term, cursor, term_id)
        db.commit()
        print('init success')
    except:
        db.rollback()
        flash('init failure')
        flash('error executing sql')

    return redirect(url_for('form_entries'))

@app.route('/insert_lterm', methods = ['POST'])
def insert_lterm():
    db = get_db()
    cursor = db.cursor()

    ent_lterm = request.form['lterm']
    ent_symb = request.form['symb_lterm']
    ent_def = request.form['def']
    ent_long_def = request.form['long_def']
    lterm_sql = 'INSERT INTO long_term (long_term, \
            def, long_def) VALUES (%s, %s, %s)'
    lterm_symb_sql = 'insert into symbolic_long_term \
            (long_term_id, symb_long_term) \
            values (%s, %s)'

    try:
        cursor.execute(lterm_sql, (ent_lterm, ent_def, ent_long_def))
        lterm_id = cursor.lastrowid
        cursor.execute(lterm_symb_sql, (lterm_id, ent_symb))
        print('testing')
        match_lterm_to_terms(ent_lterm, cursor, lterm_id)
        match_lterm_to_rules(ent_lterm, cursor, lterm_id)
        print('test2')
        db.commit()
    except:
        db.rollback()
        print('fail')
        flash('error executing sql')

    return redirect(url_for('form_entries'))

@app.route('/insert_rule', methods = ['POST'])
def insert_rule():
    db = get_db()
    cursor = db.cursor()

    ent_rule = request.form['rule']
    ent_symb = request.form['symb_rule']
    ent_def = request.form['def']
    ent_long_def = request.form['long_def']
    rule_sql = 'INSERT INTO rule (rule, \
            def, long_def) VALUES (%s, %s, %s)'
    rule_symb_sql = 'insert into symbolic_rule \
            (rule_id, symb_rule) \
            values (%s, %s)'

    try:
        cursor.execute(rule_sql, (ent_rule, ent_def, ent_long_def))
        rule_id = cursor.lastrowid
        cursor.execute(rule_symb_sql, (rule_id, ent_symb))
        match_rule_to_terms(ent_rule, cursor, rule_id)
        match_rule_to_lterms(ent_rule, cursor, rule_id)
        db.commit()
    except:
        db.rollback()
        flash('error executing sql')

    return redirect(url_for('form_entries'))

@app.route('/insert_symb', methods = ['POST'])
def insert_symb():
    db = get_db()
    cursor = db.cursor()

    ent_symb = request.form['symb']
    ent_def = request.form['def']
    ent_long_def = request.form['long_def']
    symb_sql = 'INSERT INTO symbol (symbol, \
            def, long_def) VALUES (%s, %s, %s)'

    try:
        cursor.execute(symb_sql, (ent_symb, ent_def, ent_long_def))
       # match_lterm_to_terms(ent_lterm, cursor)
        db.commit()
    except:
        db.rollback()
        flash('error executing sql')

    return redirect(url_for('form_entries'))


@app.route('/terms/<term>')
def term_page(term):
    db = get_db()
    cursor = db.cursor()

    term_id = return_term_id(term, cursor)

    sql = 'select term.term, symbolic_term.symb_term, term_def.def, \
           term_def.long_def, long_term.long_term, symbolic_long_term.symb_long_term, \
           long_term.def, long_term.long_def, rule.rule, symbolic_rule.symb_rule, \
            rule.def, rule.long_def \
           from term  \
           left join term_def \
           on term.id = term_def.term_id \
           left join symbolic_term \
           on term.id = symbolic_term.term_id \
           where term.term = %s'


    sql_term = 'select term.term, symbolic_term.symb_term, term_def.def, \
           term_def.long_def \
           from term  \
           left join term_def \
           on term.id = term_def.term_id \
           left join symbolic_term \
           on term.id = symbolic_term.term_id \
           where term.term = %s'

    sql_phrase = 'select long_term.long_term, symbolic_long_term.symb_long_term, \
           long_term.def, long_term.long_def \
           from long_term \
           left join symbolic_long_term \
           on long_term.id = symbolic_long_term.long_term_id \
           join term_long_term_join \
           on long_term.id = term_long_term_join.long_term_id \
           where term_long_term_join.term_id = %s'

    sql_rule = 'select rule.rule, symbolic_rule.symb_rule, \
           rule.def, rule.long_def \
           from rule \
           left join symbolic_rule \
           on rule.id = symbolic_rule.rule_id \
           join term_rule_join \
           on rule.id = term_rule_join.rule_id \
           where term_rule_join.term_id = %s'


    cursor.execute(sql_term, (term))
    term_inf = cursor.fetchall()

    cursor.execute(sql_phrase, (term_id))
    term_phr = cursor.fetchall()

    cursor.execute(sql_rule, (term_id))
    term_rule = cursor.fetchall()

    return render_template(
        'show_term.html',
        term = term_inf,
        phrases = term_phr,
        rules = term_rule)
