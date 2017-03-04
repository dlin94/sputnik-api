from flask import Flask, request, jsonify
import requests
import bs4
import json
from sputnikScraper.sputnik import Sputnik # http://stackoverflow.com/questions/2349991/python-how-to-import-other-python-files
                                           # http://stackoverflow.com/questions/279237/import-a-module-from-a-relative-path
                                           # http://stackoverflow.com/questions/4142151/python-how-to-import-the-class-within-the-same-directory-or-sub-directory

app = Flask(__name__)

@app.route('/')
def index():
    return 'Index'

@app.route('/hello')
def hello_world():
    return 'Hello, world!'

@app.route('/chart')
def chart():
    year = request.args.get('year') # NoneType if not provided
    genre = request.args.get('genre')
    limit = request.args.get('limit')

    # http://www.sputnikmusic.com/best/albums/9999/ for all-time
    # Error messages
    chart = Sputnik.get_chart(year, genre)
    #http://stackoverflow.com/questions/12630224/returning-api-error-messages-with-python-and-flask
    return jsonify(chart);

@app.route('/artist/<artist_id>')
def artist(artist_id):
    artist = Sputnik.get_artist(artist_id)
    return jsonify(artist)
