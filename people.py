import datetime
import random
import string
import time
import uuid
from flask_login_dictabase_blueprint import VerifyAdmin
from flask_login_dictabase_blueprint.menu import AddMenuOption, GetMenu
from flask import render_template, request, flash, send_file, redirect, jsonify
from flask_dictabase import BaseTable
from pathlib import Path
import csv

from slack import Slack


def Setup(a):
    AddMenuOption(
        title='Add a Person',
        url='/people/add',
        adminOnly=True,
    )

    global app
    app = a

    # Create a background job to add a large number of people to the database
    # every X minutes, add Y number of people to the database
    JOB_NAME = 'Add More People'
    with app.app_context():
        for job in app.jobs.GetJobs():
            if job['name'] == JOB_NAME or job['name'] is None:
                job.Delete()

        # job = app.jobs.RepeatJob(
        #     func=AddMorePeople,
        #     minutes=1,
        #     name=JOB_NAME,
        # )
        # print('job=', job)

    @app.route('/people/add', methods=['GET', 'POST'])
    @VerifyAdmin  # restrict this page to admins only
    def PeopleAdd():
        '''
        Add a new user to the database
        :return:
        '''
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

    @app.route('/people/face/<UUID>')
    def PeopleFace(UUID):
        '''
        Return the user's profile image.
        :param UUID:
        :return:
        '''
        person = app.db.FindOne(Person, uuid=UUID)
        return send_file(person.thumbPath, as_attachment=True, )


class Person(BaseTable):
    def __init(self, *a, **k):
        super().__init__(*a, **k)
        self.uuid  # ensure this person has a uuid
        self['birth_year'] = self['date_of_birth'].year
        self['birth_month'] = self['date_of_birth'].month
        self['birth_day'] = self['date_of_birth'].day

    @classmethod
    def GetRandom(cls):
        dobDT = GetRandomDatetime()
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
                'birth_month',
                'birth_day',
                'birth_year',
            ]:
                value = self.get(key, None)
                if isinstance(value, (datetime.datetime,)):
                    value = value.isoformat()
                ret[key] = value

            elif key == 'date_of_birth':
                ret['date_of_birth_iso'] = self[key].isoformat()

        ret['imgSrc'] = self.imgSrc
        ret['uuid'] = self.uuid

        return ret

    @property
    def uuid(self):
        if not self.get('uuid', None):
            self['uuid'] = str(uuid.uuid4())
        return self['uuid']

    @property
    def imgPath(self):
        '''
        Return the local path to the user's image
        :return: str
        '''
        p = Path(self.app.config['basedir']) / 'faces' / f'{self["id"] % 100}_face.png'
        if not p.exists():
            return 'https://thispersondoesnotexist.com'
        return p

    @property
    def thumbPath(self):
        '''
        Return the local path to the user's image (low res)
        :return: str
        '''
        p = Path(self.app.config['basedir']) / 'faces' / f'{self["id"] % 100}_face_200x200.png'
        if not p.exists():
            return 'https://thispersondoesnotexist.com'
        return p

    @property
    def imgSrc(self):
        '''
        Return the relative URL to the user's profile image
        :return: str
        '''
        return f'/people/face/{self.uuid}'


def GetRandomPerson(index=None):
    '''
    Create a random person from the CSV file and insert them into the database.
    :param index:
    :return: Person() obj
    '''
    index = index or 0
    csvPath = Path(app.config['basedir']) / 'us-50000.csv'
    with open(csvPath, mode='r') as file:
        reader = csv.reader(file)
        for thisIndex, row in enumerate(reader):
            if index == thisIndex:
                dobDT = GetRandomDatetime()
                # print('dobDT=', dobDT, type(dobDT))
                # print('timestamp=', dobDT.timestamp())

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
                return CreateNewPerson(d)


def CreateNewPerson(data):
    '''
    Create a new person from 'data' and insert into the db.
    If any data is missing, it will be given a random value.

    The dict must contain {'first_name' and 'last_name'} and there must not be
        a person with that same name in the db already.

    :param data: dict
    :return: Person() obj
    '''
    with app.app_context():
        existingPerson = app.db.FindOne(
            Person,
            first_name=data.get('first_name', None),
            last_name=data.get('last_name', None)
        )
        if existingPerson:
            print('existingPerson=', existingPerson)
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
            if data.get(key, None):
                kwargs[key] = data.get(key)
            else:
                kwargs[key] = defaults[key]

        if 'date_of_birth_iso' in data:
            print('using form bday')
            kwargs['date_of_birth'] = datetime.datetime.fromisoformat(data['date_of_birth_iso'])
            kwargs['date_of_birth_timestamp'] = kwargs['date_of_birth'].timestamp()

        else:
            # make a random bday
            dobDT = GetRandomDatetime()
            kwargs['date_of_birth'] = dobDT
            kwargs['date_of_birth_timestamp'] = dobDT.timestamp()

        kwargs['birth_month'] = kwargs['date_of_birth'].month
        kwargs['birth_day'] = kwargs['date_of_birth'].day
        kwargs['birth_year'] = kwargs['date_of_birth'].year

        # print('kwargs=', kwargs)
        new = app.db.New(Person, **kwargs)
        # print('new=', new)
        return new


def EditPerson(data):
    '''
    Edit a person in the db.
    Must pass data['uuid']

    :param data: dict
    :return: Person() obj with updated data
    '''
    person = app.db.FindOne(
        Person,
        uuid=data['uuid'],
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


def GetRandomDatetime():
    '''
    Return a random datetime between 1970 and (today -18years)
    Used to give people a random birthday
    :return:
    '''
    endDT = datetime.datetime.now() - datetime.timedelta(days=365*18)
    dobDT = datetime.datetime.fromtimestamp(
        random.randint(0, int(endDT.timestamp()))
    )
    return dobDT


def AddMorePeople():
    '''
    If db has less than MIN_NUM_PEOPLE in it. Add some more.
    Run this periodically unstil the db has met the MIN_NUM_PEOPLE.
    :return: None
    '''
    print('AddMorePeople')
    # create at least X ppl
    with app.app_context():
        MIN_NUM_PEOPLE = 365 * 100
        print('MIN_NUM_PEOPLE=', MIN_NUM_PEOPLE)
        totalPeople = 0
        for p in app.db.FindAll(Person):
            totalPeople += 1

        print('totalPeople=', totalPeople)
        if totalPeople < MIN_NUM_PEOPLE:
            needToCreate = MIN_NUM_PEOPLE - totalPeople
            print('needToCreate=', needToCreate)
            newlyCreated = 0
            index = totalPeople
            errors = 0
            while newlyCreated < min(100, needToCreate) and errors < 1000:
                index += 1
                try:
                    person = GetRandomPerson(index=index)
                    if person['id'] % 100 == 0:
                        print('added new person=', person['id'])
                    newlyCreated += 1
                except Exception as e:
                    print(newlyCreated, index, e)
                    errors += 1

            else:
                LAST_NOTIFICATION_NUM = 'last_notification_number'
                newNumber = totalPeople + newlyCreated
                if newNumber >= app.db.var.Get(LAST_NOTIFICATION_NUM, 0) + 2000:
                    Slack(f'There are now {newNumber} people in the database')
                    app.db.var.Set(LAST_NOTIFICATION_NUM, newNumber)
