from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client(tmp_path: Path):
    with TestClient(create_app(tmp_path / 'casepilot.sqlite3')) as c:
        yield c

def login(client, email='agent@casepilot.local', password='demo1234'):
    response=client.post('/api/login',json={'email':email,'password':password})
    assert response.status_code==200
    return {'Authorization':'Bearer '+response.json()['token']}

def test_health(client):
    assert client.get('/api/health').json()['status']=='ok'

def test_reject_bad_password(client):
    assert client.post('/api/login',json={'email':'agent@casepilot.local','password':'wrong'}).status_code==401

def test_seeded_tickets(client):
    r=client.get('/api/tickets',headers=login(client))
    assert r.status_code==200 and r.json()['total']==3

def test_auth_required(client):
    assert client.get('/api/tickets').status_code==401

def test_create_search_filter(client):
    headers=login(client)
    r=client.post('/api/tickets',headers=headers,json={'title':'Erro de autenticação','description':'Reproduzido na autenticação do aplicativo','priority':'HIGH'})
    assert r.status_code==201
    result=client.get('/api/tickets?search=autenticação&status=OPEN',headers=headers).json()
    assert any(x['id']==r.json()['id'] for x in result['items'])

def test_reject_invalid_ticket(client):
    r=client.post('/api/tickets',headers=login(client),json={'title':'oi','description':'curta','priority':'HIGH'})
    assert r.status_code==422

def test_agent_can_update_status(client):
    r=client.patch('/api/tickets/1/status',headers=login(client),json={'status':'RESOLVED'})
    assert r.status_code==200 and r.json()['status']=='RESOLVED'

def test_viewer_cannot_update_status(client):
    r=client.patch('/api/tickets/1/status',headers=login(client,'viewer@casepilot.local'),json={'status':'RESOLVED'})
    assert r.status_code==403

def test_logout_revokes_session(client):
    auth=login(client)
    assert client.post('/api/logout',headers=auth).status_code==204
    assert client.get('/api/tickets',headers=auth).status_code==401

def test_xss_is_stored_but_rendering_must_escape(client):
    r=client.post('/api/tickets',headers=login(client),json={'title':'<script>alert(1)</script>','description':'Injection payload for frontend verification','priority':'LOW'})
    assert r.status_code==201

def test_reject_invalid_status_filter(client):
    headers = login(client)

    response = client.get(
        '/api/tickets?status=INVALID',
        headers=headers
    )

    assert response.status_code == 422

    
def test_viewer_only_sees_own_tickets(client):
    headers = login(client, 'viewer@casepilot.local')

    response = client.get(
        '/api/tickets',
        headers=headers
    )

    assert response.status_code == 200
    assert response.json()['total'] == 0
    assert response.json()['items'] == []
