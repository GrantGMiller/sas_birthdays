import datetime
import functools
import random
import string
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
        ret = []
        searchFor = request.args.get('searchFor', None)
        if searchFor:
            ret.extend(SearchFor(searchFor))

        elif 'month' in request.args or 'day' in request.args:
            searchMonth = int(request.args.get('month', 0))
            searchDay = int(request.args.get('day', 0))
            for p in app.db.FindAll(people.Person):
                if searchMonth and searchDay:
                    if p['date_of_birth'].month == searchMonth and \
                            p['date_of_birth'].day == searchDay:
                        ret.append(p)
                elif searchMonth:
                    if p['date_of_birth'].month == searchMonth:
                        ret.append(p)
                elif searchDay:
                    if p['date_of_birth'].day == searchDay:
                        ret.append(p)

        elif 'start_month' in request.args:
            startMonth = int(request.args.get('start_month', 0))
            startDay = int(request.args.get('start_day', 0))
            endMonth = int(request.args.get('end_month', 0))
            endDay = int(request.args.get('end_day', 0))

            for p in app.db.FindAll(people.Person):
                if startMonth <= p['date_of_birth'].month <= endMonth:
                    if startDay <= p['date_of_birth'].day <= endDay:
                        ret.append(p)

        elif 'thisWeek' in request.args:
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

        elif request.form:
            print('request.form=', request.form)
            s = ' '.join(request.form.values())
            ret.extend(SearchFor(s))

        return jsonify(list(r.UISafe() for r in ret))

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


def SearchFor(searchFor, mode='and'):
    '''

    :param searchFor: str > space-separated search string(s)
    :param mode: str > should be 'and' or 'or' to indicate if the individual sub string must all match (and) or only one (or)
    :return:
    '''
    ret = []
    print('searchFor=', searchFor)
    if searchFor:
        with app.app_context():
            searchFor = searchFor.lower()

            # user should be able to type in multiple words, separate by space
            # only results that have a match for each sub-word should be returned

            subSearchFor = searchFor.split(' ')
            for p in app.db.FindAll(people.Person):
                numMatches = 0
                for subSearch in subSearchFor:
                    for value in p.values():
                        if subSearch in str(value).lower():
                            numMatches += 1
                            break

                if mode == 'and' and numMatches >= len(subSearchFor):
                    # all the sub matches were found
                    ret.append(p)
                elif mode == 'or' and numMatches >= 1:
                    ret.append(p)
    return ret
