from wsgiref import simple_server
from collections import OrderedDict
import cgi
import fnmatch
import time
from datetime import datetime
from sqlite3 import dbapi2 as sqlite
import os

from flask import Flask, render_template, request, g, session, flash, \
     redirect, url_for, abort
from flask_openid import OpenID
from flask import Markup

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# setup flask
app = Flask(__name__)
app.config.update(
    DATABASE_URI = 'sqlite:////tmp/flask-openid.db',
    SECRET_KEY = 'development key',
    DEBUG = True
)

# setup flask-openid
oid = OpenID(app)

# setup sqlalchemy
engine = create_engine(app.config['DATABASE_URI'])
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    Base.metadata.create_all(bind=engine)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(60))
    email = Column(String(200))
    openid = Column(String(200))

    def __init__(self, name, email, openid):
        self.name = name
        self.email = email
        self.openid = openid


@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = User.query.filter_by(openid=session['openid']).first()


@app.after_request
def after_request(response):
    db_session.remove()
    return response




@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    """Does the login via OpenID.  Has to call into `oid.try_login`
    to start the OpenID machinery.
    """
    # if we are already logged in, go back to were we came from
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'fullname',
                                                  'nickname'])
    return render_template('login.html', next=oid.get_next_url(),
                           error=oid.fetch_error())


@oid.after_login
def create_or_login(resp):
    """This is called when login with OpenID succeeded and it's not
    necessary to figure out if this is the users's first login or not.
    This function has to redirect otherwise the user will be presented
    with a terrible URL which we certainly don't want.
    """
    session['openid'] = resp.identity_url
    user = User.query.filter_by(openid=resp.identity_url).first()
    if user is not None:
        flash(u'Successfully signed in')
        g.user = user
        return redirect(oid.get_next_url())
    return redirect(url_for('create_profile', next=oid.get_next_url(),
                            name=resp.fullname or resp.nickname,
                            email=resp.email))


@app.route('/create-profile', methods=['GET', 'POST'])
def create_profile():
    """If this is the user's first login, the create_or_login function
    will redirect here so that the user can set up his profile.
    """
    if g.user is not None or 'openid' not in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        if not name:
            flash(u'Error: you have to provide a name')
        elif '@' not in email:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            db_session.add(User(name, email, session['openid']))
            db_session.commit()
            return redirect(oid.get_next_url())
    return render_template('create_profile.html', next_url=oid.get_next_url())


@app.route('/profile', methods=['GET', 'POST'])
def edit_profile():
    """Updates a profile"""
    if g.user is None:
        abort(401)
    form = dict(name=g.user.name, email=g.user.email)
    if request.method == 'POST':
        if 'delete' in request.form:
            db_session.delete(g.user)
            db_session.commit()
            session['openid'] = None
            flash(u'Profile deleted')
            return redirect(url_for('index'))
        form['name'] = request.form['name']
        form['email'] = request.form['email']
        if not form['name']:
            flash(u'Error: you have to provide a name')
        elif '@' not in form['email']:
            flash(u'Error: you have to enter a valid email address')
        else:
            flash(u'Profile successfully created')
            g.user.name = form['name']
            g.user.email = form['email']
            db_session.commit()
            return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', form=form)


@app.route('/logout')
def logout():
    session.pop('openid', None)
    flash(u'You have been signed out')
    return redirect(oid.get_next_url())


def get_series():
    conn = sqlite.connect("tml.db")
    cur = conn.cursor()
    conn.text_factory = str
    cur.execute("select distinct series from userdata where user=?",[g.user.name])
    series = []
    for row in cur.fetchall():
      series.append(row[0])
    return series

def get_data(series):
    conn = sqlite.connect("tml.db")
    cur = conn.cursor()
    conn.text_factory = str
    cur.execute("select value, at from userdata where series = ? and user = ? ", [series,g.user.name])
    data = {}
    for row in cur.fetchall():
      data[time.mktime(datetime.strptime(row[1], '%Y-%m-%d').timetuple())] = float(row[0])
    return data

@app.route('/not_found')
def not_found():
    #start_response('404 Not Found', [('content-type','text/html')])
    return "<html><h1>Page not Found</h1><p>That page is unknown. Return to the <a href="/">home page</a></p></html>"


@app.route('/')
@app.route('/index.html')
def index():

    if g.user is None:
        return redirect(url_for('login'))

    values = {}
    values["graphs"] = ""

    for s in get_series():
      #print s
      params={}
      vs = get_data(s)
      vs = OrderedDict(sorted(vs.items(), key=lambda t: t[0]))
      #print vs
      params["id"] = s
      def normalise(v, vs):
        if (max(vs) - min(vs) <= 0):
          return (v - min(vs))
        else:
          return ((v - min(vs)) / (max(vs) - min(vs)))
      params["points"] = "["
      for k in vs.keys():
        kn = normalise(k,vs.keys())
        vn = normalise(vs[k],vs.values())
        params["points"] += "{x:"+str(kn)+",y:"+str(vn)+"},"
      params["points"] += "]"
      #g = load_page(params, "graph.html")

      gds= render_template('graph.html', points=params["points"],id=params["id"])
      values["graphs"] += gds

    #page = load_page(values, "index.html")

    return render_template('index.html',graphs=values["graphs"])

@app.route('/form/new_value',methods=['GET', 'POST'])
def add_value():

    if g.user is None:
        abort(401)

    if request.method == 'POST':

        print "adding value"
        print "It works"
        Series = request.form['series']
        value = request.form['value']
        date = request.form['date']

        print Series
    
        conn = sqlite.connect("tml.db")
        cur = conn.cursor()
        cur.execute("insert into userdata values (?,?,?,?)", [date,
                                                    value, 
                                                    Series, g.user.name
                                                   ])
        print "value added"
        conn.commit()
    
        return redirect(url_for('index'))









if __name__ == '__main__':
    app.run()
    
