from flask import Flask, request, jsonify, request, g
#from flask_cache import Cache
from functools import update_wrapper
from redis import StrictRedis
from urllib.parse import urlparse
import time
import os
import requests
import bs4
import json
from sputnik_scraper.sputnik import Sputnik
from cache import Cache

################################################################################
# Initialize
################################################################################
app = Flask(__name__)
redis_url = urlparse(os.environ.get('REDIS_URL'))
redis = StrictRedis(host=redis_url.hostname, # 'localhost'
                    port=redis_url.port, # 6379
                    password=redis_url.password,
                    db=0)
cache = Cache(redis)
#cache = Cache(app, config={'CACHE_TYPE': 'redis',
#                           'CACHE_REDIS_URL': os.environ.get('REDIS_URL')})

################################################################################
# Rate limit helpers -- adapted from: http://flask.pocoo.org/snippets/70/
################################################################################
class RateLimit(object):
    expiration_window = 10

    def __init__(self, key_prefix, limit, per, send_x_headers):
        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        self.send_x_headers = send_x_headers
        p = redis.pipeline()
        p.incr(self.key)
        p.expireat(self.key, self.reset + self.expiration_window)
        self.current = min(p.execute()[0], limit)

    remaining = property(lambda x: x.limit - x.current)
    over_limit = property(lambda x: x.current >= x.limit)

def get_view_rate_limit():
    return getattr(g, '_view_rate_limit', None)

def on_over_limit(limit):
    return 'You hit the rate limit', 400

def ratelimit(limit, per=300, send_x_headers=True,
              over_limit=on_over_limit,
              scope_func=lambda: request.remote_addr):
    def decorator(func):
        def rate_limited(*args, **kwargs):
            key = 'rate-limit/%s/' % (scope_func())
            rlimit = RateLimit(key, limit, per, send_x_headers)
            g._view_rate_limit = rlimit
            if over_limit is not None and rlimit.over_limit:
                return over_limit(rlimit)
            return func(*args, **kwargs)
        return update_wrapper(rate_limited, func)
    return decorator

@app.after_request
def inject_x_rate_headers(response):
    limit = get_view_rate_limit()
    if limit and limit.send_x_headers:
        h = response.headers
        h.add('X-RateLimit-Remaining', str(limit.remaining))
        h.add('X-RateLimit-Limit', str(limit.limit))
        h.add('X-RateLimit-Reset', str(limit.reset))
    return response

def make_cache_key(*args, **kwargs):
    return request.url

################################################################################
# Routes
################################################################################
@app.route('/')
def index():
    return 'Index'

@app.route('/chart', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300, key_prefix=make_cache_key)
def chart():
    print("Only printed if bypass cache.")
    year = request.args.get('year')
    genre = request.args.get('genre')
    limit = request.args.get('limit')
    chart = Sputnik.get_chart(year, genre)

    if chart == -1:
        return 'Bad message\n', 400

    return jsonify(chart), 200

@app.route('/artist/<artist_id>', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300, key_prefix=make_cache_key)
def artist(artist_id):
    artist = Sputnik.get_artist(artist_id)

    if artist == -1:
        return 'Bad message\n', 400

    return jsonify(artist), 200

@app.route('/album/<album_id>', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300, key_prefix=make_cache_key)
def album(album_id):
    album = Sputnik.get_album(album_id)

    if album == -1:
        return 'Bad message\n', 400

    return jsonify(album), 200

@app.route('/user/<username>', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300, key_prefix=make_cache_key)
def user(username):
    user = Sputnik.get_user(username)

    if user == -1:
        return 'Bad message\n', 400

    return jsonify(user), 200

@app.route('/user/<username>/reviews', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300, key_prefix=make_cache_key)
def user_reviews(username):
    user_reviews = Sputnik.get_user_reviews(username)

    if user_reviews == -1:
        return 'Bad message\n', 400

    return jsonify(user_reviews), 200
