import os

import flask_dictabase
from flask import Flask, redirect

import config
import search
import people
import api

app = Flask('SAS Birthdays')
app.config['SECRET_KEY'] = config.SECRET_KEY

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['basedir'] = basedir

app.db = flask_dictabase.Dictabase(app)


@app.route('/')
def Index():
    return redirect('/search')


search.Setup(app)
people.Setup(app)
api.Setup(app)

if __name__ == '__main__':
    app.run(debug=True)
