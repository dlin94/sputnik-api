from flask import Flask, request, jsonify
from flask_cache import Cache
import requests
import bs4
import json
from sputnikScraper.sputnik import Sputnik # http://stackoverflow.com/questions/2349991/python-how-to-import-other-python-files
                                           # http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path
                                           # http://stackoverflow.com/questions/4142151/python-how-to-import-the-class-within-the-same-directory-or-sub-directory

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@app.route('/')
def index():
    return 'Index'

@app.route('/chart', methods=['GET'])
@cache.cached(300)
def chart():
    year = request.args.get('year') # NoneType if not provided
    genre = request.args.get('genre')
    limit = request.args.get('limit')

    # http://www.sputnikmusic.com/best/albums/9999/ for all-time
    # Error messages
    chart = Sputnik.get_chart(year, genre)
    #http://stackoverflow.com/questions/12630224/returning-api-error-messages-with-python-and-flask
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
