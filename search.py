import datetime
from urllib.parse import urlencode
from flask import request, render_template, redirect


def Setup(app):
    @app.route('/search', methods=['GET', 'POST'])
    def Search():
        if request.method == 'POST':
            return redirect('/api/people/search?searchFor={}'.format(request.form.get('searchFor')))

        return render_template(
            'search.html',
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