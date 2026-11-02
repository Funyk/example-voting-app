"""Unit tests isolate the web application from the real Redis service."""
import json
import re
from html.parser import HTMLParser
from unittest.mock import Mock

import pytest
import app as vote_app


class VoteButtons(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.buttons = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'button' and attrs.get('name') == 'vote':
            self.buttons[attrs['value']] = attrs


@pytest.fixture
def client():
    vote_app.app.config.update(TESTING=True)
    with vote_app.app.test_client() as test_client:
        yield test_client


def test_vote_page_loads(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Cats' in response.data
    assert b'Dogs' in response.data
    buttons = VoteButtons(response.get_data(as_text=True)).buttons
    assert set(buttons) == {'a', 'b'}
    assert all('disabled' not in attrs for attrs in buttons.values())


def test_get_creates_voter_cookie_without_connecting_to_redis(client, monkeypatch):
    redis_factory = Mock(side_effect=AssertionError('GET must not use Redis'))
    monkeypatch.setattr(vote_app, 'get_redis', redis_factory)
    response = client.get('/')
    assert 'voter_id=' in response.headers['Set-Cookie']
    assert 'HttpOnly' in response.headers['Set-Cookie']
    assert 'SameSite=Lax' in response.headers['Set-Cookie']
    assert re.fullmatch(r'[0-9a-f]{16}', client.get_cookie('voter_id').value)
    redis_factory.assert_not_called()


def test_post_enqueues_selected_option_for_existing_voter(client, monkeypatch):
    redis = Mock()
    monkeypatch.setattr(vote_app, 'get_redis', lambda: redis)
    client.set_cookie('voter_id', '0123456789abcdef')
    response = client.post('/', data={'vote': 'a'})
    assert response.status_code == 200
    redis.rpush.assert_called_once()
    queue, payload = redis.rpush.call_args.args
    assert queue == 'votes'
    assert json.loads(payload) == {'voter_id': '0123456789abcdef', 'vote': 'a'}
    assert 'Set-Cookie' not in response.headers


@pytest.mark.parametrize('invalid_id', [
    'not-a-voter', '0123456789abcdeF', '0123456789abcdef0', 'bad; Path=/'
])
def test_invalid_voter_cookie_is_replaced(client, invalid_id):
    client.set_cookie('voter_id', invalid_id)
    response = client.get('/')
    generated = client.get_cookie('voter_id').value
    assert response.status_code == 200
    assert generated != invalid_id
    assert re.fullmatch(r'[0-9a-f]{16}', generated)
    assert 'HttpOnly' in response.headers['Set-Cookie']


@pytest.mark.parametrize('selected,other', [('a', 'b'), ('b', 'a')])
def test_vote_response_keeps_other_option_available(client, monkeypatch, selected, other):
    monkeypatch.setattr(vote_app, 'get_redis', Mock(return_value=Mock()))
    response = client.post('/', data={'vote': selected})
    buttons = VoteButtons(response.get_data(as_text=True)).buttons
    assert 'disabled' in buttons[selected]
    assert 'disabled' not in buttons[other]
    assert buttons[other]['style'] == 'opacity:0.5'


def test_changing_choice_reuses_same_voter_id(client, monkeypatch):
    redis = Mock()
    monkeypatch.setattr(vote_app, 'get_redis', lambda: redis)
    client.get('/')
    client.post('/', data={'vote': 'a'})
    client.post('/', data={'vote': 'b'})
    first = json.loads(redis.rpush.call_args_list[0].args[1])
    second = json.loads(redis.rpush.call_args_list[1].args[1])
    assert first['voter_id'] == second['voter_id']
    assert [first['vote'], second['vote']] == ['a', 'b']
