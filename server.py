from flask import Flask, request, jsonify
from flask_cache import Cache
import requests
import bs4
import json
from sputnikScraper.sputnik import Sputnik

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

def make_cache_key(*args, **kwargs):
    return request.url

@app.route('/')
def index():
    return 'Index'

@app.route('/chart', methods=['GET'])
@cache.cached(300, key_prefix=make_cache_key)
def chart():
    # Get query string arguments
    year = request.args.get('year') # NoneType if not provided
    genre = request.args.get('genre')
    limit = request.args.get('limit')

    chart = Sputnik.get_chart(year, genre)
    return jsonify(chart);

@app.route('/artist/<artist_id>', methods=['GET'])
@cache.cached(300)
def artist(artist_id):
    artist = Sputnik.get_artist(artist_id)
    return jsonify(artist)

@app.route('/album/<album_id>', methods=['GET'])
@cache.cached(300)
def album(album_id):
    album = Sputnik.get_album(album_id)
    return jsonify(album)
