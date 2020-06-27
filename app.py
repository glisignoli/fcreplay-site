from flask import Flask, request, render_template, g
from flask import Blueprint
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

import logging
import sqlite3
import requests
import xml.etree.ElementTree as ET

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/sqlalchemy.db'

Bootstrap(app)
db = SQLAlchemy(app)

logging.basicConfig(filename='fcreplay-site.log',
                    filemode='w', level=logging.DEBUG)
DATABASE = './replays.db'


class Replay(db.Model):
    id = db.Column(db.Text, primary_key=True)
    p1_loc = db.Column(db.String(3))
    p2_loc = db.Column(db.String(3))
    p1 = db.Column(db.String(50))
    p2 = db.Column(db.String(50))


def get_db():
    replay_db = getattr(g, '_database', None)
    if replay_db is None:
        replay_db = g._database = sqlite3.connect(DATABASE)
    return replay_db


def get_latest_replays():
    logging.info("Getting latest replays from DB")
    cur = get_db().cursor()
    rows = cur.execute(
        "SELECT * FROM replays WHERE created = 'yes' AND failed = 'no' LIMIT 90")
    replays = rows.fetchall()
    logging.debug(f"Returning: {replays}")
    return(replays)


def get_card_details(challenge_id):
    logging.info("Getting description from DB")
    cur = get_db().cursor()
    challenge_details = cur.execute(
        "SELECT p1_loc,p2_loc,p1,p2 FROM replays WHERE ID = ?",(challenge_id,)).fetchone()
    
    character_details = cur.execute(
        "SELECT p1_char,p2_char,vid_time FROM character_detect WHERE challenge = ?",(challenge_id,)).fetchall()

    return(challenge_details, character_details)


def get_latest():
    challenge_ids = get_latest_replays()
    for i in challenge_ids:
        card_details = get_card_details(i[0])
        logging.debug(f"Card details: {card_details}")
        sql_data = Replay(
            id=i[0],
            p1_loc=card_details[0][0],
            p2_loc=card_details[0][1],
            p1=card_details[0][2],
            p2=card_details[0][3]
        )
        db.session.add(sql_data)
    db.session.commit()

  
def get_search_results(search_data):
    logging.info(f"Doing search for {search_data}")
    cur = get_db().cursor()
    challenge_ids = cur.execute(
        'SELECT ID FROM descriptions WHERE description LIKE ?',('%'+search_data['search']+'%',)).fetchall()
    logging.debug(f"Got results: {challenge_ids}")
    
    for i in challenge_ids:
        card_details = get_card_details(i[0])
        logging.debug(f"Card details: {card_details}")
        sql_data = Replay(
            id=i[0],
            p1_loc=card_details[0][0],
            p2_loc=card_details[0][1],
            p1=card_details[0][2],
            p2=card_details[0][3]
        )
        db.session.add(sql_data)
    db.session.commit()


@app.route('/')
def index():
    db.drop_all()
    db.create_all()
    get_latest()

    page = request.args.get('page', 1, type=int)
    pagination = Replay.query.paginate(page, per_page=9)
    replays = pagination.items

    return(render_template('start.j2.html', pagination=pagination, replays=replays))


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        db.drop_all()
        db.create_all()
        result = request.form
        
        get_search_results(result)
        logging.debug(f"Post results {result}")

        page = request.args.get('page', 1, type=int)
        pagination = Replay.query.paginate(page, per_page=9)
        replays = pagination.items

        return(render_template('start.j2.html', pagination=pagination, replays=replays))


@app.teardown_appcontext
def close_connection(exception):
    replay_db = getattr(g, '_database', None)
    if db is not None:
        replay_db.close()
