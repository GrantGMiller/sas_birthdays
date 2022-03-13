import datetime
import json
import uuid
from io import BytesIO, StringIO
from pathlib import Path
from typing import TextIO
from urllib.parse import urlencode
from flask import request, render_template, redirect, send_file
from flask_login_dictabase_blueprint import IsAdmin

from flask_login_dictabase_blueprint.menu import AddMenuOption, GetMenu

from api import SearchFor


def Setup(app):
    AddMenuOption(
        title='Search',
        url='/search',
    )

    @app.route('/search', methods=['GET', 'POST'])
    def Search():
        if request.method == 'POST':
            return redirect('/api/people/search?searchFor={}'.format(request.form.get('searchFor')))

        return render_template(
            'search.html',
            menu=GetMenu('Search'),
            initSearch=request.args.get('searchFor', None),
            isAdmin=IsAdmin(),
        )
