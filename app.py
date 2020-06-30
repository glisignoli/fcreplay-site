from flask import Flask, request, render_template, g, session
from flask import Blueprint
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

from flask_wtf import FlaskForm
from wtforms import Form, StringField, BooleanField, SubmitField, SelectField

import logging

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./replays.db'
app.config['SECRET_KEY'] = "YjA0NmNmNzQtYjQxOS00ZWRkLWI4MzItN2U4ZTEwYjk3ODY3Cg=="

Bootstrap(app)
db = SQLAlchemy(app)

logging.basicConfig(filename='fcreplay-site.log',
                    filemode='w', level=logging.DEBUG)
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

    search = StringField('Search',)
    char1 = SelectField('Character1', choices=characters)
    char2 = SelectField('Character2', choices=characters)
    player_requested = BooleanField('Player Submitted')
    submit = SubmitField()


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
    player_requested = db.Column(db.Text)
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
    searchForm = SearchForm()
    page = request.args.get('page', 1, type=int)
    pagination = Replays.query.filter(
        Replays.created == 'yes'
    ).filter(
        Replays.failed == 'no'
    ).order_by(Replays.date_added).paginate(page, per_page=9)
    replays = pagination.items

    return(render_template('start.j2.html', pagination=pagination, replays=replays, form=searchForm))


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

        searchForm = SearchForm()#(result, char1=char1,
                                #char2=char2, search=search_query,
                                #player_requested=player_requested)

        session['search'] = result.search.data
        session['char1'] = result.char1.data
        session['char2'] = result.char2.data
        session['player_requested'] = result.player_requested.data
    else:
        search_query = session['search']
        char1 = session['char1']
        char2 = session['char2']
        player_requested = session['player_requested']

        searchForm = SearchForm(request.form, char1=char1,
                                char2=char2, search=search_query,
                                player_requested=player_requested)

    if player_requested:
        player_requested = 'yes'
    else:
        player_requested = 'no'


    page = request.args.get('page', 1, type=int)

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
        ).paginate(page, per_page=9)
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
                Character_detect.query.with_entities(Character_detect.challenge).filter(
                    Character_detect.p1_char.ilike(
                        f'{char1}') & Character_detect.p2_char.ilike(f'{char2}')
                ).union(
                    Character_detect.query.with_entities(Character_detect.challenge).filter(
                        Character_detect.p1_char.ilike(
                            f'{char2}') & Character_detect.p2_char.ilike(f'{char1}')
                    )
                )
            )
        )

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
        Character_detect.challenge == challenge_id
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