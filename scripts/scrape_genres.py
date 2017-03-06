import bs4
import requests

def get_genres():
    f = open('genres.csv', 'w')
    req = requests.get("http://www.sputnikmusic.com/static/navigation.html")
    soup = bs4.BeautifulSoup(req.text, "lxml")

    table = soup.find("table", class_="gmenu")
    genres = table.find_all("a")
    for genre in genres:
        genre_id = genre.attrs["href"].split("/")[2]
        f.write(genre.text + "," + genre_id + "\n")
    f.close()

if __name__ == "__main__":
    get_genres()
