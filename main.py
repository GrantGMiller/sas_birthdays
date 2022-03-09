import os
import sys

import flask_dictabase
import jinja2
from flask import Flask, redirect, render_template, jsonify

import config
import search
import people
import api
from slack import Slack

app = Flask('SAS Birthdays')
app.config['SECRET_KEY'] = config.SECRET_KEY

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['basedir'] = basedir

app.config['STATIC_FOLDER'] = f'static'
# print("app.config['STATIC_FOLDER']=", app.config['STATIC_FOLDER'])

app.config['STATIC_PATH'] = f'/static'
# print("app.config['STATIC_PATH']=", app.config['STATIC_PATH'])

# overriding jinja template loader so that pytest can acccess templates
my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader(app.config['basedir'] + '/templates'),
])
app.jinja_loader = my_loader

app.db = flask_dictabase.Dictabase(app)


@app.route('/')
def Index():
    return redirect('/search')


@app.errorhandler(500)
def Error(e):
    msg = str(e)
    try:
        with open(f'{app.config["basedir"]}/gerror.log', mode='rt') as file:
            msg += '\r\n\r\n****GUNICORN ERROR LOG****\r\n' + file.read()
    except Exception as e2:
        msg += str(e2)

    if sys.platform.startswith('win'):
        print('HTTP Error ' + msg)
    else:
        Slack('HTTP Error ' + msg)

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
    app.run()  # debug=True)
