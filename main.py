import os
import sys

import flask_dictabase
from flask import Flask, redirect, render_template

import config
import search
import people
import api
from slack import Slack

app = Flask('SAS Birthdays')
app.config['SECRET_KEY'] = config.SECRET_KEY

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['basedir'] = basedir

app.db = flask_dictabase.Dictabase(app)


@app.route('/')
def Index():
    return redirect('/search')


@app.errorhandler(500)
def Error(e):
    msg = str(e)
    if not sys.platform.startswith('win'):
        try:
            with open(f'{app.config["basedir"]}/gerror.log', mode='rt') as file:
                msg += '\r\n\r\n****GUNICORN ERROR LOG****\r\n' + file.read()
        except Exception as e2:
            msg += str(e2)

        Slack('HTTP Error' + msg)

    return render_template(
        'error.html',
        message=str(e),
    )


@app.route('/error_test')
def ErrorTest():
    raise Exception('This is a fake error.')


search.Setup(app)
people.Setup(app)
api.Setup(app)

if __name__ == '__main__':
    app.run(debug=True)
