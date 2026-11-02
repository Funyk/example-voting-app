from flask import Flask, render_template, request, make_response, g
from redis import Redis
import os
import socket
import secrets
import json
import logging
import re

option_a = os.getenv('OPTION_A', "Cats")
option_b = os.getenv('OPTION_B', "Dogs")
hostname = socket.gethostname()

app = Flask(__name__)

gunicorn_error_logger = logging.getLogger('gunicorn.error')
app.logger.handlers.extend(gunicorn_error_logger.handlers)
app.logger.setLevel(logging.INFO)

def get_redis():
    if not hasattr(g, 'redis'):
        g.redis = Redis(host="redis", db=0, socket_timeout=5)
    return g.redis

@app.route("/", methods=['POST','GET'])
def hello():
    voter_id = request.cookies.get('voter_id')
    new_voter_id = None
    if not voter_id or re.fullmatch(r'[0-9a-f]{16}', voter_id) is None:
        new_voter_id = secrets.token_hex(8)
        voter_id = new_voter_id

    vote = None

    if request.method == 'POST':
        redis = get_redis()
        vote = request.form['vote']
        app.logger.info('Received vote for %s', vote)
        data = json.dumps({'voter_id': voter_id, 'vote': vote})
        redis.rpush('votes', data)

    resp = make_response(render_template(
        'index.html',
        option_a=option_a,
        option_b=option_b,
        hostname=hostname,
        vote=vote,
    ))
    if new_voter_id is not None:
        resp.set_cookie('voter_id', new_voter_id, httponly=True, samesite='Lax')
    return resp


if __name__ == "__main__":
    # Container ingress must bind all interfaces; the development debugger stays off.
    app.run(host='0.0.0.0', port=80, debug=False, threaded=True)  # nosec B104
