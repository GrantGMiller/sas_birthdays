import main


def test_home_page():
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    app = main.app
    print('\napp=', app)
    # Create a test client using the Flask application configured for testing
    with app.test_client() as test_client:
        print('test_client=', test_client)
        response = test_client.get('/')
        print('response=', response)
        assert response.status_code == 302


def test_search_page():
    app = main.app
    print('\napp=', app)
    # Create a test client using the Flask application configured for testing
    with app.test_client() as test_client:
        print('test_client=', test_client)
        response = test_client.get('/search')
        print('response=', response)
        assert response.status_code == 200


def test_api():
    # Test the search API
    app = main.app
    print('\napp=', app)
    with app.test_client() as test_client:
        print('test_client=', test_client)
        response = test_client.post(
            '/api/people/search',
            data={'first_name': 'Alda', 'last_name': 'Antony'}
        )
        print('response=', response)
        assert response.status_code == 200
        for item in response.json['results']:
            print('item=', item)
            if item['first_name'] == 'Alda' and item['last_name'] == 'Antony':
                break
        else:
            raise ValueError('Did not find Alda Antony')
