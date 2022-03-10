Birthdays
=============

This project presents a simple web UI to look up employees.
You can use the '/search' page to find employees by their name, company, birthday, or any other meta data.

API
===
An api is also supported to integrate with other tools.

All API commands should encode and send data as HTTP Form Data.
Some API commands require the user to pass an 'apiKey' in the form data.

API responses will return data in JSON format.
HTTP code 2XX are used for successful responses. HTTP code 4XX/5XX are used for failed responses.

The below examples are using the python-requests package (https://pypi.org/project/requests/)

::

    # Perform a search
    resp = requests.post(
        url='https://sas.grant-miller.com/api/people/search',
        data={'first_name': 'John', 'last_name': 'Smith'},
    )
    for item in resp.json():
        print('item=', item)

    >>> item= {
        "address": "79 Wiley Post Way",
        "city": "Orlando",
        "company": "Awesome, Co A Iii",
        "county": "Orange",
        "date_of_birth": "Sat, 06 Nov 1993 00:00:00 GMT",
        "date_of_birth_iso": "1993-11-06T00:00:00",
        "date_of_birth_timestamp": 752558400.0,
        "email": "jama.armen@armen.org",
        "first_name": "John",
        "last_name": "Smith",
        "mobile": "407-669-5881",
        "phone": "407-581-5321",
        "state": "FL",
        "uuid": "b5a33cbc-0d15-4cfe-9495-1ffe30954d11",
        "website": "http://www.smithjohnaiii.com",
        "zip": "32804"
    }

::

    # Add a new user
    requests.post(
        url='https://sas.grant-miller.com/api/people/add',
        data={
            'apiKey': 'secretApiKey',
            'first_name': 'John',
            'last_name': 'Smith',
            },
    )
    # any data that is not included will be given a random default value


::

    # Edit a user
    requests.post(
        url='https://sas.grant-miller.com/api/people/edit',
        data={
            'apiKey': 'secretApiKey',
            'uuid': '123-456',
            'address': '123 Fake St.'
            },
    )
    # data must include the 'uuid' of the user to edit.
    # Any other data will override the current data.
    # Any data excluded will remain intact.

::

    # Delete a user
    requests.post(
        url='https://sas.grant-miller.com/api/people/delete',
        data={
            'apiKey': 'secretApiKey',
            'uuid': '123-456',
            },
    )
    # data must include the 'uuid' of the user to edit.



