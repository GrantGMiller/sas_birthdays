import datetime
import functools
import random
import string
import time
from urllib.parse import urlencode
from flask import request, redirect, jsonify
from flask_login_dictabase_blueprint import AddAdmin
import config
import people


def Setup(a):
    global app
    app = a

    AddAdmin('grant@grant-miller.com')

    @app.route('/api/people/search', methods=['GET', 'POST'])
    def APIPeopleSearch():
        print('APIPeopleSearch()', request.method, 'request.form=', request.form)
        export = request.form.get('export', False)
        export = {'true': True}.get(export, False)
        print('export=', export)

        startTime = time.time()
        MAX_RESULTS_PER_PAGE = 15
        offset = int(request.form.get('offset', 0))
        print('offset=', offset)
        ret = []
        if 'month' in request.form:
            searchMonth = int(request.form['month'])
            if 'day' in request.form:
                searchDay = int(request.form['day'])
                ret = app.db.FindAll(
                    people.Person,
                    _where='birth_month', _equals=searchMonth,
                    __where='birth_day', __equals=searchDay,

                    _limit=None if export else MAX_RESULTS_PER_PAGE,
                    _offset=None if export else offset,
                )
            else:
                ret = app.db.FindAll(
                    people.Person,
                    _where='birth_month', _equals=searchMonth,

                    _limit=None if export else MAX_RESULTS_PER_PAGE,
                    _offset=None if export else offset,
                )
        elif 'day' in request.form:
            searchDay = int(request.form['day'])
            ret = app.db.FindAll(
                people.Person,
                _where='birth_day', _equals=searchDay,

                _limit=None if export else MAX_RESULTS_PER_PAGE,
                _offset=None if export else offset,
            )

        elif 'thisWeek' in request.form:
            now = datetime.datetime.now()
            startDT = now - datetime.timedelta(days=now.weekday())
            endDT = startDT + datetime.timedelta(days=7)
            print('now=', now)
            print('startDT=', startDT)
            print('endDT=', endDT)

            if endDT.month > startDT.month:
                # todo - deal with when 'endDT' is in the next month
                pass
            else:
                ret = app.db.FindAll(
                    people.Person,
                    _where='birth_month', _greaterThanOrEqualTo=startDT.month,
                    __where='birth_day', __greaterThanOrEqualTo=startDT.day,

                    ___where='birth_month', ___lessThanOrEqualTo=endDT.month,
                    ____where='birth_day', ____lessThanOrEqualTo=endDT.day,

                    _limit=None if export else MAX_RESULTS_PER_PAGE,
                    _offset=None if export else offset,
                )

        elif 'searchFor' in request.form:
            ret = SearchFor(
                request.form['searchFor'],
                _limit=None if export else MAX_RESULTS_PER_PAGE,
                _offset=None if export else offset,
            )

        endTime = time.time()
        pageNum = int(offset / MAX_RESULTS_PER_PAGE)
        ret = {
            'offset': offset,
            'max_results_per_page': MAX_RESULTS_PER_PAGE,
            'pageNum': pageNum,
            'search_params': request.form,
            'results': list(r.UISafe() for r in ret),
            'search_time_seconds': endTime - startTime,
        }
        print("len(ret['results'])=", len(ret['results']))
        return jsonify(ret)

    @app.post('/api/people/add')
    @VerifyAPIKey
    def APIPeopleAdd():
        print('APIPeopleAdd request.form=', request.form)
        new = people.CreateNewPerson(request.form)
        return jsonify(new)

    @app.post('/api/people/edit')
    @VerifyAPIKey
    def APIPeopleEdit():
        print('APIPeopleAdd request.form=', request.form)
        person = people.EditPerson(request.form)
        return jsonify(person)

    @app.post('/api/people/delete')
    @VerifyAPIKey
    def APIPeopleDelete():
        print('APIPeopleAdd request.form=', request.form)
        person = app.db.FindOne(
            people.Person,
            uuid=request.form.get('uuid', None)
        )
        if person:
            app.db.Delete(person)
            return jsonify('Deleted')
        else:
            return jsonify('Person not found'), 404


def VerifyAPIKey(func):
    @functools.wraps(func)
    def VerifyAPIKeyWrapper(*a, **k):
        print('req key   =', request.form.get('apiKey', None))
        print('config key=', config.API_KEY)
        if request.form.get('apiKey', None) != config.API_KEY:
            return jsonify('Wrong API KEY'), 403
        return func(*a, **k)

    return VerifyAPIKeyWrapper


def SearchFor(searchFor, _limit=None, _offset=None):
    '''

    :param searchFor: str > space-separated search string(s)
    :param mode: str > should be 'and' or 'or' to indicate if the individual sub string must all match (and) or only one (or)
    :return:
    '''
    print('searchFor=', searchFor)
    if searchFor:
        # q = f"SELECT * FROM Person WHERE first_name LIKE '%{searchFor}%'";
        sub = ''
        cols = app.db.db['Person'].columns

        s = ''
        for index, subString in enumerate(searchFor.split(' ')):
            if index > 0:
                s += ' or '
            s += ' or '.join(f"{col} LIKE '%{subString}%'" for col in cols)

        q = f"SELECT * FROM Person WHERE {s}"
        if _limit:
            q += f' LIMIT {_limit}'
        if _offset:
            q += f' OFFSET {_offset}'

        print('q=', q)
        r = app.db.db.query(q)
        for item in r:
            # print('item=', item)
            item['date_of_birth'] = datetime.datetime.fromisoformat(item['date_of_birth'])
            yield people.Person(db=app.db, app=app, **item)

