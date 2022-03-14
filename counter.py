import datetime
import functools
import math
import flask_tools
import flask_dictabase
from flask import render_template, request, jsonify
from flask_login_dictabase_blueprint import GetUser, IsAdmin, VerifyAdmin
from flask_login_dictabase_blueprint.menu import AddMenuOption, GetMenu

from slack import Slack

ENABLE_COUNTING = True


def Setup(a):
    global app
    app = a

    AddMenuOption(
        url='/counter',
        title='Counters',
        adminOnly=True,
    )

    @app.route('/counter')
    @VerifyAdmin
    def Counter():
        reqDate = request.args.get('date', None)
        if reqDate:
            currentDate = datetime.date.fromisoformat(reqDate)
        else:
            currentDate = datetime.date.today()

        endpoints = app.db.FindAll(EndpointCounter, date=currentDate)
        return render_template(
            'counter.html',
            currentDT=currentDate,
            prevDate=currentDate - datetime.timedelta(days=1),
            nextDate=currentDate + datetime.timedelta(days=1) if currentDate < datetime.date.today() else None,
            endpoints=endpoints,
            menu=GetMenu('Counter'),
        )

    @app.route('/counter/raw')
    @VerifyAdmin
    def CounterRaw():
        reqDate = request.args.get('date', None)
        if reqDate:
            currentDate = datetime.date.fromisoformat(reqDate)
        else:
            currentDate = datetime.date.today()

        endpoints = app.db.FindAll(EndpointCounter, date=currentDate)
        return jsonify(list(endpoints))

    @app.template_filter()
    def FormatDatetime(dt):
        return dt.strftime('%Y-%m-%d %H:%M %p')

    @app.template_filter()
    def FormatDate(dt):
        return dt.isoformat()


def CountViews(func):
    @functools.wraps(func)
    def DoCount(*a, **k):
        if ENABLE_COUNTING:
            user = GetUser()
            if IsAdmin():
                pass  # dont count views by admins
            else:

                endpointCounter = GetEndpointCounter(func.__name__)

                count = endpointCounter.Inc()

                SendPopularityNotification(endpointCounter, count)

        return func(*a, **k)

    return DoCount


def GetEndpointCounter(name):
    date = datetime.date.today()
    endpointCounter = app.db.NewOrFind(EndpointCounter, name=name, date=date)
    return endpointCounter


def SendPopularityNotification(endpointCounter, count):
    if not ENABLE_COUNTING:
        return
    # get exponential notifications, eg. get a notification at 1,2,4,8,16,32...
    print('SendPopularityNotification(', endpointCounter)
    a = count
    b = 2
    if a >= 4:
        # credit to stackoverflow: https://stackoverflow.com/questions/39281632/check-if-a-number-is-a-perfect-power-of-another-number
        if b ** int(round(math.log(a, b))) == a:
            Slack(f'The "{endpointCounter["name"]}" page has gotten {count} views today.')


def GetClientIP():
    return flask_tools.GetClientIP(raiseForLocalAddress=False)


class EndpointCounter(flask_dictabase.BaseTable):
    def Inc(self):
        with self.db.db.lock:
            if self.get('count', None):
                self['count'] = self['count'] + 1
            else:
                self['count'] = 1

            self.Append('ips', {
                'datetime': datetime.datetime.now().isoformat(),
                'ip': GetClientIP()
            })

            return self['count']

    @property
    def Count(self):
        count = self.get('count', None)
        if not count:
            count = 0
        return count

    @property
    def NumUniqueIPs(self):
        allIPs = []
        ips = self.Get('ips', None)
        if ips:
            for d in ips:
                allIPs.append(d['ip'])
        return len(set(allIPs))
