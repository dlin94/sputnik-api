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
    # Follow this URL pattern instead: http://www.sputnikmusic.com/topalbums.php?t=97&year=2015
    # where t is a genre number
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
                # TODO: Read this discussion: http://ux.stackexchange.com/questions/85451/when-invalid-querystring-paramater-detected-in-a-web-page-url-throw-an-error-or
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
            # info_dict_1 = { } # for first artist
            # info_dict_2 = { } # for second artist
            for j in range(1, 5, 2):
                try:
                    info = row.contents[j]
                except IndexError:
                    break

                # image: info.find("img", class_="lazy")
                info_dict = { } # need to find a way to add album art to the same dict without adding the other artist's info

                artist_and_score = info.find_all("b")
                info_dict['artist'] = artist_and_score[0].get_text()
                info_dict['score'] = artist_and_score[1].get_text()
                info_dict['album'] = info.find("font", class_="darktext").get_text()
                info_dict['votes'] = info.find("font", class_="contrasttext").get_text()[:-6]
                info_dict['ranking'] = i
                #chart[i] = info_dict
                albums.append(info_dict)

                i += 1
        chart["albums"] = albums

        return chart

    def get_artist(artist_id):
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
        artist["genres"] = get_genres(soup)
        artist["similar"] = get_similar(soup)
        artist["description"] = get_description(soup)
        artist["releases"] = get_releases(soup)
        return artist

################################################################################
# Artist helpers
################################################################################
headers = ["LPs", "EPs", "Compilations", "Live Albums"]
def get_genres(soup):
    genres = soup.find("ul", class_="tags").contents
    genre_list = []
    for genre in genres:
        genre_list.append(genre.get_text())
    return genre_list

def get_similar(soup):
    sims = soup.find("table", class_="bandbox").next_sibling.contents
    sims_list = []
    for sim in sims:
        # Don't consider the commas (NavigableStrings)
        if type(sim) is bs4.element.Tag and sim.get_text() != "Similar Bands: ":
            sims_list.append(sim.get_text())
    return sims_list

def get_description(soup):
    try:
        desc =  soup.find(id="slidebox").get_text()
    except AttributeError:
        return ''

    desc = desc.replace("  « hide", " ")
    return desc

def get_releases(soup):
    releases = []
    release_table = soup.find("table", class_="plaincontentbox")
    lp_header = release_table.contents[2]

    # Go through each album row
    album_row = lp_header
    while album_row is not None:
        album_row = album_row.next_sibling
        album_row, albums = get_albums(album_row)
        for album in albums:
            releases.append(album)
    return releases

# Helper for get_releases()
def get_albums(album_row):
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
