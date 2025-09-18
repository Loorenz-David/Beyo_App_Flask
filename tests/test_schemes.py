import pytest
from Purchase_App import create_app
from flask import json
from flask_login import login_user
from Purchase_App.models.query import run_query


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def login_test_user(client,app):
    with app.app_context():
        query_filters = {'id':1}
        user = run_query('User',query_filters).first()
        with client.session_transaction() as sess:
            sess['_user_id'] = str(user.id)


@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


def test_scheme_routers(client,login_test_user):
    payload = { 'model_name':'User',
                'requested_data':['username',{'roles':['role',{'users':['username']}]}],
                'query_filters':{'username':{'operation':'ilike','value':'%test%'},'roles.id':8}
               }
    response = client.get('/schemes/get_items',
                           data=json.dumps(payload),
                           content_type='application/json')
    print(response.get_json())
    print(response.status_code)
    assert response.status_code == 200
 

    