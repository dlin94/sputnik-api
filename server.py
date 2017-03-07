from flask import Flask, request, jsonify, request, g
from flask_cache import Cache
from functools import update_wrapper
from redis import StrictRedis
from urllib.parse import urlparse
import time
import os
import requests
import bs4
import json
from sputnik_scraper.sputnik import Sputnik

################################################################################
# Initialize
################################################################################
app = Flask(__name__)
redis_url = urlparse(os.environ.get('REDIS_URL'))
redis = StrictRedis(host=redis_url.hostname, # 'localhost'
                    port=redis_url.port, # 6379
                    password=redis_url.password,
                    db=0)
cache = Cache(app, config={'CACHE_TYPE': 'redis',
                           'CACHE_REDIS_URL': os.environ.get('REDIS_URL')})

################################################################################
# Rate limit helpers
################################################################################
# Credit: http://flask.pocoo.org/snippets/70/
class RateLimit(object):
    expiration_window = 10

    def __init__(self, key_prefix, limit, per):
        self.reset = (int(time.time()) // per) * per + per
        self.key = key_prefix + str(self.reset)
        self.limit = limit
        self.per = per
        p = redis.pipeline()
        p.incr(self.key)
        p.expireat(self.key, self.reset + self.expiration_window)
        self.current = min(p.execute()[0], limit)

    over_limit = property(lambda x: x.current >= x.limit)

def get_view_rate_limit():
    return getattr(g, '_view_rate_limit', None)

def on_over_limit(limit):
    return 'You hit the rate limit', 400

def ratelimit(limit, per=300,
              over_limit=on_over_limit,
              scope_func=lambda: request.remote_addr,
              key_func=lambda: request.endpoint):
    def decorator(func):
        def rate_limited(*args, **kwargs):
            key = 'rate-limit/%s/%s/' % (key_func(), scope_func())
            rlimit = RateLimit(key, limit, per)
            g._view_rate_limit = rlimit
            if over_limit is not None and rlimit.over_limit:
                return over_limit(rlimit)
            return func(*args, **kwargs)
        return update_wrapper(rate_limited, func)
    return decorator

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
    return jsonify(chart);

@app.route('/artist/<artist_id>', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300)
def artist(artist_id):
    artist = Sputnik.get_artist(artist_id)
    return jsonify(artist)

@app.route('/album/<album_id>', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300)
def album(album_id):
    album = Sputnik.get_album(album_id)
    return jsonify(album)

@app.route('/user/<username>', methods=['GET'])
@ratelimit(limit=30, per=60)
@cache.cached(300)
def user(username):
    user = Sputnik.get_user(username)
    return jsonify(user)
