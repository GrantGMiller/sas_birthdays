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

    @app.route('/search/today')
    def SearchToday():
        now = datetime.datetime.now()
        kwargs = {
            'day': now.day,
            'month': now.month,
        }
        return redirect(f'/api/people/search?{urlencode(kwargs)}')

    @app.route('/search/thisWeek')
    def SearchThisWeek():
        now = datetime.datetime.now()
        startDT = now - datetime.timedelta(days=now.weekday())
        endDT = startDT + datetime.timedelta(days=7)
        print('now=', now)
        print('startDT=', startDT)
        print('endDT=', endDT)
        kwargs = {
            'start_month': startDT.month,
            'start_day': startDT.day,
            'end_month': endDT.month,
            'end_day': endDT.day,
        }
        return redirect(f'/api/people/search?{urlencode(kwargs)}')

    @app.route('/search/thisMonth')
    def SearchThisMonth():
        now = datetime.datetime.now()
        kwargs = {
            'month': now.month,
        }
        return redirect(f'/api/people/search?{urlencode(kwargs)}')

    @app.route('/search/export/<searchFor>')
    def SearchExport(searchFor):
        print('SearchExport(', searchFor)
        results = SearchFor(searchFor, mode='or')
        results = [r.UISafe() for r in results]
        print('results=', results)
        return send_file(
            BytesIO(json.dumps(results, indent=2).encode()),
            as_attachment=True,
            download_name=f'{uuid.uuid4()}.json',
        )
