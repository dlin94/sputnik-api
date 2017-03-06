import bs4
import requests
import os

dir = os.path.dirname(__file__)
filename = os.path.join(dir, '../scripts/genres.csv')
f = open(filename, "r")

genres = { }
for line in f.readlines():
    genre = line.split(",")[0]
    genre_id = line.split(",")[1]
    genres[genre.upper()] = genre_id.replace("\n", "")
f.close()

class Sputnik:
    @staticmethod
    def get_chart(year, genre, limit=0):
        chart = { }
        # Build request URL
        url = "http://sputnikmusic.com/topalbums.php?"
        if (year != None):
            try:
                int(year)
            except ValueError:
                print("Non-integer year given.")
                return
            url += "year=" + year + "&"
            chart["year"] = year
        else: # no year provided, so assume all-time (9999)
            url += "year" + "9999" + "&"
            chart["year"] = "all"
        if (genre != None):
            if genre.upper() not in genres:
                print("Bad genre given.")
                return
            url += "t=" + genres[genre.upper()]
            chart["genre"] = genre.lower()
        else:
            chart["genre"] = "all"

        print(url)
        req = requests.get(url)
        soup = bs4.BeautifulSoup(req.text, "lxml")
        albums = []
        rows = soup.find_all("tr", class_="alt1")

        i = 1
        for row in rows:
            for j in range(1, 5, 2):
                try:
                    info = row.contents[j]
                except IndexError:
                    break

                # image: info.find("img", class_="lazy")
                info_dict = { }

                artist_and_score = info.find_all("b")
                info_dict['artist'] = artist_and_score[0].get_text()
                info_dict['score'] = artist_and_score[1].get_text()
                info_dict['album'] = info.find("font", class_="darktext").get_text()
                info_dict['votes'] = info.find("font", class_="contrasttext").get_text()[:-6]
                info_dict['ranking'] = i
                albums.append(info_dict)

                i += 1
        chart["albums"] = albums

        return chart

    @staticmethod
    def get_artist(artist_id): # TODO: get artist name
        try:
            int(artist_id)
        except ValueError:
            print("Non-integer id given.")
            return

        url = "http://sputnikmusic.com/bands/a/" + artist_id
        req = requests.get(url)
        soup = bs4.BeautifulSoup(req.text, "lxml")

        if soup.find("table", class_="bandbox") == None:
            return

        artist = { }
        artist["genres"] = get_artist_genres(soup)
        artist["similar"] = get_artist_similar(soup)
        artist["description"] = get_artist_description(soup)
        artist["releases"] = get_artist_releases(soup)
        return artist

    @staticmethod
    def get_album(album_id):
        try:
            int(album_id)
        except ValueError:
            print("Non-integer id given.")
            return

        url = 'http://www.sputnikmusic.com/soundoff.php?albumid=' + album_id
        req = requests.get(url)
        soup = bs4.BeautifulSoup(req.text, "lxml")

        album = { }
        artist, album_name, rating, year = get_album_info(soup)
        album["artist"] = artist
        album["album"] = album_name
        album["rating"] = rating
        album["year"] = year
        album["rating_count"] = get_album_rating_count(soup)
        album["tracks"] = get_album_tracklist(album_id)
        return album

    @staticmethod
    def get_user(username):
        url = 'http://www.sputnikmusic.com/user/' + username
        req = requests.get(url)
        soup = bs4.BeautifulSoup(req.text, "lxml")

        user = { 'username': username}
        user.update(get_user_info(soup))
        return user


################################################################################
# Artist helpers
################################################################################
headers = ["LPs", "EPs", "Compilations", "Live Albums"]
def get_artist_genres(soup):
    genres = soup.find("ul", class_="tags").contents
    genre_list = []
    for genre in genres:
        genre_list.append(genre.get_text())
    return genre_list

def get_artist_similar(soup):
    sims = soup.find("table", class_="bandbox").next_sibling.contents
    sims_list = []
    for sim in sims:
        # Don't consider the commas (NavigableStrings)
        if type(sim) is bs4.element.Tag and sim.get_text() != "Similar Bands: ":
            sims_list.append(sim.get_text())
    return sims_list

def get_artist_description(soup):
    try:
        desc =  soup.find(id="slidebox").get_text()
    except AttributeError:
        return ''

    desc = desc.replace("  « hide", " ")
    return desc

def get_artist_releases(soup):
    releases = []
    release_table = soup.find("table", class_="plaincontentbox")
    lp_header = release_table.contents[2]

    # Go through each album row
    album_row = lp_header
    while album_row is not None:
        album_row = album_row.next_sibling
        album_row, albums = get_artist_albums(album_row)
        for album in albums:
            releases.append(album)
    return releases

# Helper for get_artist_releases()
def get_artist_albums(album_row):
    albums = [ ]
    while album_row is not None and album_row.get_text() not in headers:
        # Each album row has at most 2 albums
        for i in range(1, 5, 3):
            # Index error if we're trying to find the second album of a 1-album row
            try:
                album = album_row.contents[i]
            except IndexError:
                break
            release = { }
            # Get all the info
            release["title"] = album.contents[0].find("a").get_text()
            release["date"] = album.contents[2].get_text()
            release["rating"] = album.contents[5].contents[0].find("td").contents[0].contents[0].get_text()
            release["votes"] = album.contents[5].contents[0].find("td").contents[0].contents[2].get_text()
            albums.append(release)
        album_row = album_row.next_sibling
    return (album_row, albums) # stops at a header

################################################################################
# Album helpers
################################################################################
def get_album_info(soup):
    try:
        tr = soup.find("tr", class_="alt1")
        info = tr.contents[1]
        artist = info.contents[0].get_text()
        album_name = info.contents[2].string

        other_info = tr.find("tr")
        rating = other_info.contents[0].contents[0].contents[0].get_text()
        year = other_info.contents[1].contents[0].contents[1].string
        return (artist, album_name, rating, year)
    except AttributeError:
        return ('', '', '', '')

def get_album_rating_count(soup):
    ratings_tab = soup.find("td", class_="reviewtabs_selected").get_text()
    count = ratings_tab[9:-1]
    return count

def get_album_tracklist(album_id):
    url = 'http://www.sputnikmusic.com/tracklist.php?albumid=' + album_id
    req = requests.get(url)
    soup = bs4.BeautifulSoup(req.text, "lxml")
    soup = soup.find("table")
    tracklist = []
    for line in soup.get_text().splitlines():
        try:
            int(line[0])
        except ValueError:
            continue
        line_split = line.split(" ")
        num = line_split[0][:-1]
        name = " ".join(line_split[1:])
        track = { "track_number": num, "track_name": name }
        tracklist.append(track)
    return tracklist

################################################################################
# User helpers
################################################################################
def get_user_info(soup):
    info_box = soup.find("font", class_="category").parent
    info = { }
    info["title"] = info_box.contents[0].string
    for child in info_box.contents[3:]:
        if type(child) is bs4.element.NavigableString or child.get_text() == '':
            continue

        if child['class'] == ['category']:
            category = child.string.lower().replace(" ", "_")
            info[category] = ''
        elif child['class'] == ['normal']:
            val = child.string
            category = child.previous_sibling.previous_sibling.string.lower().replace(" ", "_")
            info[category] = val
    return info
