from flask import request, render_template, jsonify
import people


def Setup(app):
    @app.route('/api/people/search')
    def APIPeopleSearch():
        ret = []
        searchFor = request.args.get('searchFor', None)
        print('searchFor=', searchFor)
        if searchFor:
            searchFor = searchFor.lower()
            for p in app.db.FindAll(people.Person):
                for key, value in p.items():
                    if searchFor in str(value).lower():
                        ret.append(p)
                        break
                        
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
        return jsonify(ret)
