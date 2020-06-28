from flask import Flask, request, render_template, g
from flask import Blueprint
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

import logging

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./replays.db'

Bootstrap(app)
db = SQLAlchemy(app)

logging.basicConfig(filename='fcreplay-site.log',
                    filemode='w', level=logging.DEBUG)


class Replays(db.Model):
    id = db.Column(db.Text, primary_key=True)
    p1_loc = db.Column(db.String(3))
    p2_loc = db.Column(db.String(3))
    p1 = db.Column(db.String(50))
    p2 = db.Column(db.String(50))
    created = db.Column(db.String(3))
    date_org = db.Column(db.Text)
    length = db.Column(db.Integer)
    failed = db.Column(db.String(3))
    player_requested = db.Column(db.String(3))
    date_added = db.Column(db.Integer)


class Descriptions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    description = db.Column(db.Text)


class Character_detect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge = db.Column(db.Text, primary_key=True)
    p1_char = db.Column(db.String)
    p2_char = db.Column(db.String)
    vid_time = db.Column(db.String)


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Replays.query.filter(
        Replays.created == 'yes'
    ).filter(
        Replays.failed == 'no'
    ).order_by(Replays.date_added).paginate(page, per_page=9)
    replays = pagination.items

    return(render_template('start.j2.html', pagination=pagination, replays=replays))


@app.route('/search', methods=['POST', 'GET'])
def search():
    if request.method == 'POST':
        result = request.form
        logging.debug(f"Post results {result}")

        page = request.args.get('page', 1, type=int)
        pagination = Replays.query.filter(
            Replays.created == 'yes'
        ).filter(
            Replays.failed == 'no'
        ).filter(
            Replays.id.in_(
                Descriptions.query.with_entities(Descriptions.id).filter(
                    Descriptions.description.ilike(f'%{result["search"]}%')
                )
            )
        ).paginate(page, per_page=9)
        replays = pagination.items

        return(render_template('start.j2.html', pagination=pagination, replays=replays))