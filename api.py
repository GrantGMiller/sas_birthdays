import datetime
from urllib.parse import urlencode

from flask import request, render_template, jsonify
from werkzeug.utils import redirect

import people


def Setup(app):
    @app.route('/api/people/search')
    def APIPeopleSearch():
        ret = []
        searchFor = request.args.get('searchFor', None)
        print('searchFor=', searchFor)
        if searchFor:
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

                if numMatches >= len(subSearchFor):
                    # all the sub matches were found
                    ret.append(p)

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

        return jsonify(ret)
