import datetime
import functools
import time
from flask import request, jsonify
from flask_login_dictabase_blueprint import AddAdmin
import config
import people
from counter import CountViews


def Setup(a):
    global app
    app = a

    # Only 'admins' can add users from the web UI
    AddAdmin('grant@grant-miller.com')

    @app.route('/api/people/search', methods=['GET', 'POST'])
    @CountViews
    def APIPeopleSearch():
        '''
        search params will be in the 'request.form' dict
        use 'month' and/or 'day' in request.form to search for a birthday
        use 'thisWeek' as a key in reqeust.form to get birthdays for the current week

        if none of the above are in 'request.form', then the values of request.form
            will be used to perform a full-text-search on all users.
            Example: if 'request.form' = {'search': 'john smith'} will return any
             users with 'john' and 'smith' in their row

        include {'export': 'true'} in request.form to return ALL results (not limited/paginated)

        :return: json response
        '''
        print('APIPeopleSearch()', request.method, 'request.form=', request.form, ', request.json=', request.json)
        export = request.form.get('export', False)
        export = {'true': True}.get(export, False)
        print('export=', export)

        startTime = time.time()
        MAX_RESULTS_PER_PAGE = 15

        requestData = request.form or request.json

        offset = int(requestData.get('offset', 0))
        print('offset=', offset)

        if requestData.get('month', None):
            searchMonth = int(requestData['month'])
            if requestData.get('day', None):
                searchDay = int(requestData['day'])

                ret = app.db.FindAll(
                    people.Person,
                    _where='birth_month', _equals=searchMonth,
                    __where='birth_day', __equals=searchDay,

                    _limit=None if export else MAX_RESULTS_PER_PAGE,
                    _offset=None if export else offset,
                )

            else:  # search the month only
                ret = app.db.FindAll(
                    people.Person,
                    _where='birth_month', _equals=searchMonth,
                    _orderBy='birth_day',
                    _limit=None if export else MAX_RESULTS_PER_PAGE,
                    _offset=None if export else offset,
                )

        elif requestData.get('day', None):
            # search the day only
            searchDay = int(requestData['day'])
            ret = app.db.FindAll(
                people.Person,
                _where='birth_day', _equals=searchDay,

                _limit=None if export else MAX_RESULTS_PER_PAGE,
                _offset=None if export else offset,
            )

        elif 'thisWeek' in requestData:
            now = datetime.datetime.now()
            startDT = now - datetime.timedelta(days=now.weekday())
            endDT = startDT + datetime.timedelta(days=7, microseconds=-1)
            print('now=', now)
            print('startDT=', startDT)
            print('endDT=', endDT)

            if endDT.month > startDT.month:
                # the week crosses into a new month, so the query has to be a little
                #   more specific
                s = f'(birth_month == {startDT.month} and birth_day >= {startDT.day})'
                s += ' or '
                s += f'(birth_month == {endDT.month} and birth_day <= {endDT.day})'

                q = f"SELECT * FROM Person WHERE {s}"
                ret = RawSQLQuery(
                    q,
                    _limit=None if export else MAX_RESULTS_PER_PAGE,
                    _offset=None if export else offset,
                )

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

        else:
            searchString = ''
            for key, value in requestData.items():
                if key not in ['export', 'offset'] and value:
                    searchString += f'{value} '

            print('122 searchString=', searchString)
            ret = SearchFor(
                searchString,
                _limit=None if export else MAX_RESULTS_PER_PAGE,
                _offset=None if export else offset,
            )

        # return the results
        pageNum = int(offset / MAX_RESULTS_PER_PAGE)
        ret = {
            'offset': offset,
            'max_results_per_page': MAX_RESULTS_PER_PAGE,
            'pageNum': pageNum,
            'search_params': requestData,
            'results': list(r.UISafe() for r in ret),
        }
        endTime = time.time()
        deltaTime = endTime - startTime
        print('deltaTime=', deltaTime)
        ret['search_time_milliseconds'] = deltaTime * 1000
        print("len(ret['results'])=", len(ret['results']))
        return jsonify(ret)

    @app.post('/api/people/add')
    @CountViews
    @VerifyAPIKey
    def APIPeopleAdd():
        print('APIPeopleAdd request.form=', request.form)
        new = people.CreateNewPerson(request.form)
        return jsonify(new.UISafe())

    @app.post('/api/people/edit')
    @CountViews
    @VerifyAPIKey
    def APIPeopleEdit():
        print('APIPeopleAdd request.form=', request.form)
        person = people.EditPerson(request.form)
        return jsonify(person.UISafe())

    @app.post('/api/people/delete')
    @CountViews
    @VerifyAPIKey
    def APIPeopleDelete():
        print('APIPeopleAdd request.form=', request.form)
        person = app.db.FindOne(
            people.Person,
            uuid=request.form.get('uuid', None)
        )
        if person:
            app.db.Delete(person)
            return jsonify(f'Deleted uuid="{person.uuid}')
        else:
            return jsonify('Person not found'), 404


def VerifyAPIKey(func):
    '''
    Use this decorator to verify a request has the correct API_KEY
    :param func:
    :return:
    '''

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
    Performs a full-text-search on all the users.
    :param searchFor: str > space-separated search string(s)
    :return:
    '''
    searchFor = searchFor.strip()
    print('SearchFor=', searchFor, ', len(searchFor)=', len(searchFor))
    if searchFor:
        # q = f"SELECT * FROM Person WHERE first_name LIKE '%{searchFor}%'";
        sub = ''
        cols = app.db.db['Person'].columns

        s = '('
        for index, subString in enumerate(searchFor.split(' ')):
            if index > 0:
                s += ') and ('
            s += ' or '.join(f"{col} LIKE '%{subString}%'" for col in cols)
        s += ')'

        q = f"SELECT * FROM Person WHERE {s}"
        return RawSQLQuery(q, _limit, _offset)
    else:
        return ''


def RawSQLQuery(q, _limit=None, _offset=None):
    '''
    Run a raw SQL query
    :param q: str
    :param _limit: None or int
    :param _offset: None or int
    :return: generator of db results
    '''
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
