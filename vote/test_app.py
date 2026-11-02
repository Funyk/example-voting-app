"""Unit tests isolate the web application from the real Redis service."""
import json
from unittest.mock import Mock

import pytest
import app as vote_app


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


def test_get_creates_voter_cookie_without_connecting_to_redis(client, monkeypatch):
    redis_factory = Mock(side_effect=AssertionError('GET must not use Redis'))
    monkeypatch.setattr(vote_app, 'get_redis', redis_factory)
    response = client.get('/')
    assert 'voter_id=' in response.headers['Set-Cookie']
    redis_factory.assert_not_called()


def test_post_enqueues_selected_option_for_existing_voter(client, monkeypatch):
    redis = Mock()
    monkeypatch.setattr(vote_app, 'get_redis', lambda: redis)
    client.set_cookie('voter_id', 'test-voter-42')
    response = client.post('/', data={'vote': 'a'})
    assert response.status_code == 200
    redis.rpush.assert_called_once()
    queue, payload = redis.rpush.call_args.args
    assert queue == 'votes'
    assert json.loads(payload) == {'voter_id': 'test-voter-42', 'vote': 'a'}


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
