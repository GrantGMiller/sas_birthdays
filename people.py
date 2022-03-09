import datetime
import random

from flask_dictabase import BaseTable
from pathlib import Path
import csv


def Setup(a):
    global app
    app = a
    # create at least X ppl
    with app.app_context():
        MIN_NUM_PEOPLE = 365 * 3
        totalPeople = 0
        for person in app.db.FindAll(Person):
            totalPeople += 1

        if totalPeople < MIN_NUM_PEOPLE:
            needToCreate = MIN_NUM_PEOPLE - totalPeople
            for i in range(needToCreate):
                person = GetRandomPerson(index=needToCreate + i)
                print('added new person=', person)


class Person(BaseTable):
    pass


def GetRandomPerson(index=None):
    index = index or 0
    csvPath = Path(app.config['basedir']) / 'us-50000.csv'
    with open(csvPath, mode='r') as file:
        reader = csv.reader(file)
        for thisIndex, row in enumerate(reader):
            if index == thisIndex:
                dob_month = random.randint(1, 12)
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
                    'date_of_birth': datetime.date(
                        year=random.randint(1922, 2015),
                        month=dob_month,
                        day=random.randint(1, 30 if dob_month in [9, 4, 6, 11] else 31 if dob_month != 2 else 28),
                    )
                }
                return app.db.New(Person, **d)
