from flask import Flask, request, render_template, g, session, send_from_directory, redirect, url_for
from flask import Blueprint
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm

from wtforms import Form, StringField, BooleanField, SubmitField, SelectField

import os
import json
import logging


try:
    import googleclouddebugger
    googleclouddebugger.enable(
        breakpoint_enable_canary=True
    )
except ImportError:
    pass

with open("config.json", 'r') as json_data_file:
    config = json.load(json_data_file)

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = config['sql_baseurl']
app.config['SECRET_KEY'] = config['secret_key']

Bootstrap(app)
db = SQLAlchemy(app)

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class SearchForm(FlaskForm):
    characters = [
        ('Any', 'Any'),
        ('alex', 'alex'),
        ('akuma', 'akuma'),
        ('chunli', 'chunli'),
        ('dudley', 'dudley'),
        ('elena', 'elena'),
        ('hugo', 'hugo'),
        ('ibuki', 'ibuki'),
        ('ken', 'ken'),
        ('makoto', 'makoto'),
        ('necro', 'necro'),
        ('oro', 'oro'),
        ('q', 'q'),
        ('remy', 'remy'),
        ('ryu', 'ryu'),
        ('sean', 'sean'),
        ('twelve', 'twelve'),
        ('urien', 'urien'),
        ('yang', 'yang'),
        ('yun', 'yun')]

    orderby_list = [
        ('date_replay', 'Replay Date'),
        ('date_added', 'Date Added')
    ]

    search = StringField()
    char1 = SelectField('Character1', choices=characters, render_kw={'class': 'fixed'})
    char2 = SelectField('Character2', choices=characters, render_kw={'class': 'fixed'})
    player_requested = BooleanField('Player Submitted')
    order_by = SelectField('Order by', choices=orderby_list, render_kw={'class': 'fixed'})
    submit = SubmitField()


class SubmitForm(FlaskForm):
    player_id = StringField()
    challenge_url = StringField()
    submit = SubmitField()


class Replays(db.Model):
    id = db.Column(db.Text, primary_key=True)
    p1_loc = db.Column(db.String)
    p2_loc = db.Column(db.String)
    p1 = db.Column(db.String)
    p2 = db.Column(db.String)
    date_replay = db.Column(db.DateTime)
    length = db.Column(db.Integer)
    created = db.Column(db.Boolean)
    failed = db.Column(db.Boolean)
    status = db.Column(db.String)
    date_added = db.Column(db.Integer)
    player_requested = db.Column(db.Boolean)


class Descriptions(db.Model):
    id = db.Column(db.Text, primary_key=True)
    description = db.Column(db.Text)


class Character_detect(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_id = db.Column(db.Text, primary_key=True)
    p1_char = db.Column(db.String)
    p2_char = db.Column(db.String)
    vid_time = db.Column(db.String)


@app.route('/')
def index():
    searchForm = SearchForm()
    page = request.args.get('page', 1, type=int)
    pagination = Replays.query.filter(
        Replays.created == 'yes'
    ).filter(
        Replays.failed == 'no'
    ).order_by(Replays.date_added.desc()).paginate(page, per_page=9)
    replays = pagination.items

    return(render_template('start.j2.html', pagination=pagination, replays=replays, form=searchForm))

@app.route('/submit')
def submit():
    searchForm = SearchForm()
    submitForm = SubmitForm()
    return(render_template('submit.j2.html', form=searchForm, submitForm=submitForm))

@app.route('/submitResult')
def submitResult():
    logging.debug(f"Session: {session}")
    # I feel like there should be a better way to do this
    if request.method == 'POST':
        result = SearchForm(request.submitForm)

        player_id = result.player_id.data
        challenge_id = result.challenge_url.data
        session['player_id'] = result.player_id.data
        session['challenge_url'] = result.challenge_url.data

        # Add replay and get status here
        return redirect(url_for('search'))
    else:
        return(render_template('submitResult.j2.html'))

@app.route('/assets/<path:path>')
def send_js(path):
    return send_from_directory('templates/assets', path)

@app.route('/search', methods=['POST', 'GET'])
def search():
    logging.debug(f"Session: {session}")
    # I feel like there should be a better way to do this
    if request.method == 'POST':
        result = SearchForm(request.form)

        search_query = result.search.data
        char1 = result.char1.data
        char2 = result.char2.data
        player_requested = result.player_requested.data
        order_by = result.order_by.data

        searchForm = SearchForm()

        session['search'] = result.search.data
        session['char1'] = result.char1.data
        session['char2'] = result.char2.data
        session['player_requested'] = result.player_requested.data
        session['order_by'] = result.order_by.data
        return redirect(url_for('search'))
    else:
        search_query = session['search']
        char1 = session['char1']
        char2 = session['char2']
        player_requested = session['player_requested']
        order_by = session['order_by']

        searchForm = SearchForm(request.form, char1=char1,
                                char2=char2, search=search_query,
                                player_requested=player_requested)

    if player_requested:
        player_requested = 'yes'
    else:
        player_requested = 'no'

    page = request.args.get('page', 1, type=int)

    if order_by == 'date_replay':
        order = Replays.date_replay.desc()
    elif order_by == 'date_added':
        order = Replays.date_added.desc()
    else:
        raise LookupError

    if (char1 == 'Any' and char2 == 'Any'):
        logging.debug(f'Player Requested: {player_requested}')

        pagination = Replays.query.filter(
            Replays.created == 'yes'
        ).filter(
            Replays.failed == 'no'
        ).filter(
            Replays.player_requested == player_requested
        ).filter(
            Replays.id.in_(
                Descriptions.query.with_entities(Descriptions.id).filter(
                    Descriptions.description.ilike(f'%{search_query}%')
                )
            )
        ).order_by(order).paginate(page, per_page=9)

    else:
        if char1 == 'Any':
            char1 = '%'
        if char2 == 'Any':
            char2 = '%'

        logging.debug(f'Player Requested: {player_requested}')

        replay_query = Replays.query.filter(
            Replays.created == 'yes'
        ).filter(
            Replays.failed == 'no'
        ).filter(
            Replays.player_requested == player_requested
        ).filter(
            Replays.id.in_(
                Descriptions.query.with_entities(Descriptions.id).filter(
                    Descriptions.description.ilike(f'%{search_query}%')
                )
            )
        ).filter(
            Replays.id.in_(
                Character_detect.query.with_entities(Character_detect.challenge_id).filter(
                    Character_detect.p1_char.ilike(
                        f'{char1}') & Character_detect.p2_char.ilike(f'{char2}')
                ).union(
                    Character_detect.query.with_entities(Character_detect.challenge_id).filter(
                        Character_detect.p1_char.ilike(
                            f'{char2}') & Character_detect.p2_char.ilike(f'{char1}')
                    )
                )
            )
        ).order_by(order)

        logging.debug(replay_query)

        pagination = replay_query.paginate(page, per_page=9)

    replays = pagination.items

    return(render_template('start.j2.html', pagination=pagination, replays=replays, form=searchForm))


@app.route('/video/<challenge_id>',)
def videopage(challenge_id):
    searchForm = SearchForm()

    replay = Replays.query.filter(
        Replays.id == challenge_id
    ).first()
    char_detect = Character_detect.query.filter(
        Character_detect.challenge_id == challenge_id
    ).all()

    characters = []
    for c in char_detect:
        characters.append(
            {
                'p1_char': c.p1_char,
                'p2_char': c.p2_char,
                'vid_time': c.vid_time,
                'seek_time': sum(int(x) * 60 ** i for i, x in enumerate(reversed(c.vid_time.split(":"))))
            }
        )

    seek = request.args.get('seek', default=0, type=float)

    logging.debug(
        f"Video page, replay: {replay}, characters: {characters}, seek: {seek}")
    return(render_template('video.j2.html', replay=replay, characters=characters, seek=seek, form=searchForm))


if __name__ == "__main__":
    app.run(debug=True)
