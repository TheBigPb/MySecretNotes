import base64
import json, sqlite3, click, functools, os, hashlib,time, random, sys
import pickle

from flask import Flask, current_app, g, session, redirect, render_template, url_for, request, make_response


# DATABASE FUNCTIONS #

def connect_db():
    return sqlite3.connect(app.database)


def init_db():
    """Initializes the database with our great SQL schema"""
    conn = connect_db()
    db = conn.cursor()
    db.executescript("""

DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS notes;

CREATE TABLE notes (
    id INTEGER PRIMARY KEY,
    assocUser INTEGER NOT NULL,
    dateWritten DATETIME NOT NULL,
    note TEXT NOT NULL,
    publicID INTEGER NOT NULL
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

INSERT INTO users VALUES(null,"admin", "password");
INSERT INTO users VALUES(null,"bernardo", "omgMPC");
INSERT INTO notes VALUES(null,2,"1993-09-23 10:10:10","hello my friend",1234567890);
INSERT INTO notes VALUES(null,2,"1993-09-23 12:10:10","i want lunch pls",1234567891);

""")


# APPLICATION SETUP #
app = Flask(__name__)
app.database = "db.sqlite3.db"
app.secret_key = os.urandom(32)


# ADMINISTRATOR'S PANEL #
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view


@app.route("/")
def index():
    if not session.get('logged_in'):
        return render_template('index.html')
    else:
        return redirect(url_for('notes'))


@app.route("/notes/", methods=('GET', 'POST'))
@login_required
def notes():
    importerror=""
    # Posting a new note:
    if request.method == 'POST':
        if request.form['submit_button'] == 'add note':
            note = request.form['noteinput']
            db = connect_db()
            c = db.cursor()
            c.execute("INSERT INTO notes(id, assocUser, dateWritten, note, publicID) VALUES(null, (?), (?), (?), (?));",
                      (session['userid'], time.strftime('%Y-%m-%d %H:%M:%S'), note,
                       random.randrange(1000000000, 9999999999)))
            db.commit()
            db.close()
        elif request.form['submit_button'] == 'import note':
            noteid = request.form['noteid']
            db = connect_db()
            c = db.cursor()
            c.execute("SELECT * FROM NOTES where publicID = (?)", (noteid, ))
            result = c.fetchall()
            if len(result)>0:
                row = result[0]
                c.execute("INSERT INTO notes(id, assocUser, dateWritten, note, publicID) VALUES(null, (?), (?), (?), (?));", (session['userid'],row[2],row[3],row[4]))
            else:
                importerror="No such note with that ID!"
            db.commit()
            db.close()
    
    db = connect_db()
    c = db.cursor()
    c.execute("SELECT * FROM notes WHERE assocUser = (?);", (session['userid'], ))
    notes = c.fetchall()

    if 'username_pickled' in request.cookies:
        try:
            username_pickled = base64.urlsafe_b64decode(request.cookies.get('username_pickled'))
            username = pickle.loads(username_pickled)
            return render_template('notes.html', username=username, notes=notes, importerror=importerror)
        except Exception as e:
            print(e)
            render_template('notes.html', notes=notes, importerror=importerror)

    return render_template('notes.html', notes=notes, importerror=importerror)


@app.route("/login/", methods=('GET', 'POST'))
def login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = connect_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE username = (?) AND password = (?);", (username, password))
        result = c.fetchall()

        if len(result) > 0:
            session.clear()
            session['logged_in'] = True
            session['userid'] = result[0][0]
            session['username'] = result[0][1]
            resp = make_response(redirect(url_for('index')))
            username_picked = base64.urlsafe_b64encode(pickle.dumps(session['username']))
            resp.set_cookie('username_pickled', username_picked)
            return resp
        else:
            error = "Wrong username or password!"
    return render_template('login.html', error=error)


@app.route("/register/", methods=('GET', 'POST'))
def register():
    errored = False
    usererror = ""
    passworderror = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = connect_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE password = (?);", (password, ))
        if len(c.fetchall())>0:
            errored = True
            passworderror = "That password is already in use by someone else!"

        c.execute("SELECT * FROM users WHERE username = (?);", (username,))
        if len(c.fetchall())>0:
            errored = True
            usererror = "That username is already in use by someone else!"

        if not errored:
            c.execute("INSERT INTO users(id, username, password) VALUES(null, (?), (?));", (username, password))
            db.commit()
            db.close()
            return f"""<html>
                        <head>
                            <meta http-equiv="refresh" content="2;url=/" />
                        </head>
                        <body>
                            <h1>SUCCESS!!! Redirecting in 2 seconds...</h1>
                        </body>
                        </html>
                        """
        
        db.commit()
        db.close()
    return render_template('register.html',usererror=usererror,passworderror=passworderror)


@app.route("/logout/")
@login_required
def logout():
    """Logout: clears the session"""
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
    # Create database if it doesn't exist yet
    if not os.path.exists(app.database):
        init_db()
    runport = 8080
    if len(sys.argv)==2:
        runport = sys.argv[1]
    try:
        app.run(host='0.0.0.0', port=runport)  # runs on machine ip address to make it visible on netowrk
    except:
        print("Something went wrong. the usage of the server is either")
        print("'python3 app.py' (to start on port 5000)")
        print("or")
        print("'sudo python3 app.py 80' (to run on any other port)")
