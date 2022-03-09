import datetime
import random
import string
from urllib.parse import urlencode
from flask import request, redirect, jsonify

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

        return jsonify(list(r.UISafe() for r in ret))

    @app.post('/api/people/add')
    def APIPeopleAdd():
        print('APIPeopleAdd request.form=', request.form)
        if app.db.FindOne(people.Person, **request.form):
            return jsonify('This person already exist. Use /api/people/edit instead'), 500

        kwargs = {}
        for key in [
            'first_name',
            'last_name',
            'company',
            'address',
            'city',
            'county',
            'state',
            'zip',
            'phone',
            'mobile',
            'email',
            'website',
        ]:

            if request.form.get(key, None):
                kwargs[key] = request.form.get(key)
            else:

                defaults = {
                    'first_name': random.choice(string.ascii_uppercase),
                    'last_name': random.choice(string.ascii_uppercase),
                    'company': f'Company {random.choice(string.ascii_uppercase)}',
                    'address': f'{random.randint(100, 999)} Avenue {random.choice(string.ascii_uppercase)}',
                    'city': f'City {random.choice(string.ascii_uppercase)}',
                    'county': f'County {random.choice(string.ascii_uppercase)}',
                    'state': random.choice(['CA', 'NC']),
                    'zip': random.randint(10000, 99999),
                    'phone': f'{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'mobile': f'{random.randint(100, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                    'email': f'{random.choice(string.ascii_lowercase)}@{random.choice(string.ascii_lowercase)}.com',
                    'website': f'www.{"".join(random.choice(string.ascii_lowercase) for _ in range(5))}.com',

                }
                kwargs[key] = defaults[key]

        if 'date_of_birth_iso' in request.form:
            print('using form bday')
            kwargs['date_of_birth'] = datetime.datetime.fromisoformat(request.form['date_of_birth_iso'])
            kwargs['date_of_birth_timestamp'] = kwargs['date_of_birth'].timestamp()
        else:
            # make a random bday
            dob_month = random.randint(1, 12)
            dobDT = datetime.datetime(
                year=random.randint(1970, 2015),
                month=dob_month,
                day=random.randint(1, 30 if dob_month in [9, 4, 6, 11] else 31 if dob_month != 2 else 28),
            )
            kwargs['date_of_birth'] = dobDT
            kwargs['date_of_birth_timestamp'] = dobDT.timestamp()

        print('kwargs=', kwargs)
        new = app.db.New(people.Person, **kwargs)
        print('new=', new)
        return jsonify(new)

    @app.post('/api/people/edit')
    def APIPeopleEdit():
        print('APIPeopleAdd request.form=', request.form)
        person = app.db.FindOne(
            people.Person,
            first_name=request.form.get('first_name', None),
            last_name=request.form.get('last_name', None)
        )
        if person:
            person.update(request.form)
        else:
            return jsonify('This person does not exist. Use /api/people/add instead'), 500

        dobDT = person['date_of_birth']
        person['date_of_birth_timestamp'] = dobDT.timestamp()
        return jsonify(person)
