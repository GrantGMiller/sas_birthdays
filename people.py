import datetime
import random
import string
import uuid

from flask_login_dictabase_blueprint import VerifyAdmin
from flask_login_dictabase_blueprint.menu import AddMenuOption, GetMenu
from flask import render_template, request, flash
from flask_dictabase import BaseTable
from pathlib import Path
import csv

from werkzeug.utils import redirect


def Setup(a):
    AddMenuOption(
        title='Add a Person',
        url='/people/add',
        adminOnly=True,
    )
    global app
    app = a
    # create at least X ppl
    with app.app_context():
        MIN_NUM_PEOPLE = 365 * 3
        totalPeople = 0
        for p in app.db.FindAll(Person):
            totalPeople += 1
            p.uuid  # make sure each one has a uuid

        if totalPeople < MIN_NUM_PEOPLE:
            needToCreate = MIN_NUM_PEOPLE - totalPeople
            for i in range(needToCreate):
                person = GetRandomPerson(index=needToCreate + i)
                print('added new person=', person)

    @app.route('/people/add', methods=['GET', 'POST'])
    def PeopleAdd():
        if request.method == 'POST':
            person = CreateNewPerson(request.form)
            return redirect(f'/search?searchFor={person["date_of_birth"]} {person["first_name"]} {person["last_name"]}')

        return render_template(
            'people_add.html',
            defaults=Person.GetRandom(),
            menu=GetMenu('Add a Person'),
        )

    @app.route('/people/delete/<uuid>')
    @VerifyAdmin
    def PeopleDelete(uuid):
        person = app.db.FindOne(Person, uuid=uuid)
        if person:
            app.db.Delete(person)
            flash(f'Person Deleted: {person["first_name"]} {person["last_name"]}', 'success')
            return redirect('/')
        else:
            flash(f'No person found with uuid="{uuid}"', 'danger')
            return redirect('/')


class Person(BaseTable):
    @classmethod
    def GetRandom(cls):
        dob_month = random.randint(1, 12)
        dobDT = datetime.date(
            year=random.randint(1970, 2015),
            month=dob_month,
            day=random.randint(1, 30 if dob_month in [9, 4, 6, 11] else 31 if dob_month != 2 else 28),
        )
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
            'date_of_birth_iso': dobDT.isoformat(),
        }
        return defaults

    def UISafe(self):
        ret = {}
        for key in self.keys():
            if key in [
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
                'date_of_birth_timestamp',
                'uuid',
            ]:
                ret[key] = self.get(key, None)

            elif key == 'date_of_birth':
                ret['date_of_birth_iso'] = self[key].isoformat()
                ret[key] = self[key]
        return ret

    @property
    def uuid(self):
        if not self.get('uuid', None):
            self['uuid'] = str(uuid.uuid4())
        return self['uuid']


def GetRandomPerson(index=None):
    index = index or 0
    csvPath = Path(app.config['basedir']) / 'us-50000.csv'
    with open(csvPath, mode='r') as file:
        reader = csv.reader(file)
        for thisIndex, row in enumerate(reader):
            if index == thisIndex:
                dob_month = random.randint(1, 12)
                dobDT = datetime.datetime(
                    year=random.randint(1970, 2015),
                    month=dob_month,
                    day=random.randint(1, 30 if dob_month in [9, 4, 6, 11] else 31 if dob_month != 2 else 28),
                )
                print('dobDT=', dobDT, type(dobDT))
                print('timestamp=', dobDT.timestamp())

                d = {
                    'first_name': row[0],
                    'last_name': row[1],
                    'company': row[2],
                    'address': row[3],
                    'city': row[4],
                    'county': row[5],
                    'state': row[6],
                    'zip': row[7],
                    'phone': row[8],
                    'mobile': row[9],
                    'email': row[10],
                    'website': row[11],
                    'date_of_birth': dobDT,
                    'date_of_birth_timestamp': dobDT.timestamp()
                }
                return app.db.New(Person, **d)


def CreateNewPerson(data):
    with app.app_context():
        if app.db.FindOne(
                Person,
                first_name=data.get('first_name', None),
                last_name=data.get('last_name', None)
        ):
            raise KeyError('This person already exist. Use /api/people/edit instead')

        kwargs = {}
        defaults = Person.GetRandom()
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
        new = app.db.New(Person, **kwargs)
        print('new=', new)
        return new


def EditPerson(data):
    person = app.db.FindOne(
        Person,
        first_name=data.get('first_name', None),
        last_name=data.get('last_name', None)
    )

    # prevent injecting disallowed keys
    sterilized = {}
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
        sterilized[key] = data.get(key, None)

    if person:
        person.update(sterilized)
    else:
        raise KeyError('This person does not exist. Use /api/people/add instead')

    dobDT = person['date_of_birth']
    person['date_of_birth_timestamp'] = dobDT.timestamp()
    return person
