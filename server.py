from flask import Flask, request, jsonify, request, g
from flask_cache import Cache
from functools import update_wrapper
from redis import StrictRedis
import time
import os
import requests
import bs4
import json
from urllib.parse import urlparse
from sputnik_scraper.sputnik import Sputnik

app = Flask(__name__)
redis_url = urlparse(os.environ.get('REDIS_URL'))
redis = StrictRedis(host=redis_url.hostname, port=redis_url.port, password=redis_url.password, db=0) #host='localhost' port=6379
cache = Cache(app, config={'CACHE_TYPE': 'redis'})

# http://flask.pocoo.org/snippets/70/
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
              scope_func=lambda: request.remote_addr,
              key_func=lambda: request.endpoint):
    def decorator(f):
        def rate_limited(*args, **kwargs):
            key = 'rate-limit/%s/%s/' % (key_func(), scope_func())
            rlimit = RateLimit(key, limit, per, send_x_headers)
            g._view_rate_limit = rlimit
            if over_limit is not None and rlimit.over_limit:
                return over_limit(rlimit)
            return f(*args, **kwargs)
        return update_wrapper(rate_limited, f)
    return decorator

def make_cache_key(*args, **kwargs):
    return request.url

@app.route('/')
def index():
    return 'Index'

@app.route('/chart', methods=['GET'])
@ratelimit(limit=16, per=1)
@cache.cached(300, key_prefix=make_cache_key)
def chart():
    print("Only printed if bypass cache.")
    # Get query string arguments
    year = request.args.get('year') # NoneType if not provided
    genre = request.args.get('genre')
    limit = request.args.get('limit')
    chart = Sputnik.get_chart(year, genre)
    return jsonify(chart);

@app.route('/artist/<artist_id>', methods=['GET'])
@ratelimit(limit=16, per=1)
@cache.cached(300)
def artist(artist_id):
    artist = Sputnik.get_artist(artist_id)
    return jsonify(artist)

@app.route('/album/<album_id>', methods=['GET'])
@ratelimit(limit=16, per=1)
@cache.cached(300)
def album(album_id):
    album = Sputnik.get_album(album_id)
    return jsonify(album)

@app.route('/user/<username>', methods=['GET'])
@cache.cached(300)
def user(username):
    user = Sputnik.get_user(username)
    #print(redis.get("flask_cache_view//user/mynameischan"))
    return jsonify(user)
