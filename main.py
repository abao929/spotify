from bs4 import BeautifulSoup as bs
import urllib.request
from urllib.error import HTTPError
import csv
import re
import requests
from collections import Counter
import base64
import datetime
import time
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt

start = time.time()

client_id = ''
client_secret = ''

#url = 'https://open.spotify.com/playlist/348iMtCvYQQdICvrxIBbbe?si=GbdYjuDkQ7GtMV-R2cZ98Q' #kofc
url = 'https://open.spotify.com/playlist/5USCz2dkmTbJ3nLhk4UVip?si=UnYZdZeHQH-4MGsE0Iz0SA' #not like the other
#url = 'https://open.spotify.com/playlist/1LKVe8ZEmFlxlCjqi8Us82?si=BwhGCvPuT02rjc0WQrIpFA' # 20 deloreans
#url = 'https://open.spotify.com/playlist/1na8htLAvxOM3cWLuaublx?si=_vKbFl78S5WWJ8XIfhFhQg' #bossman
#url = 'https://open.spotify.com/playlist/2GI6Z1IZIlsI2KCAECxBj0?si=rqJItCgnTJ6VddPYTZThCw' #sadge
#url = 'https://open.spotify.com/playlist/4XpLccSePOM5xUvsKhkitA?si=nWoxhRJ5ShSWOZV4fxMzzg' #ncs
page = urllib.request.urlopen(url)
soup = bs(page, 'html.parser')
soup = str(soup)

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers = {'User-Agent': user_agent,}

bad_urls = []

COMMON_WORDS = ["a", "about", "all", "also", "and", "as", "at", "be", "because", "but", "by", "can", "come", "could", "day", "do", "even", "find", "first",
 "for", "from", "get", "give", "go", "have", "he", "her", "here", "him", "his", "how", "i", "if", "im", "in", "into", "it", "its", "just", "know", "like", "look",
 "make", "man", "many", "me", "more", "my", "new", "no", "not", "now", "of", "on", "one", "only", "or", "other", "our", "out", "people", "say", "see", "she",
 "so", "some", "take", "tell", "than", "that", "the", "their", "them", "then", "there", "these", "they", "thing", "think", "this", "those", "time", "to", "two",
 "up", "use", "very", "want", "way", "we", "well", "what", "when", "which", "who", "will", "with", "would", "year", "you", "your"]

def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        start += len(sub)

#new api stuff
def get_token(client_id, client_secret):
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = { 
        'grant_type': 'client_credentials'
    }
    client_creds = f'{client_id}:{client_secret}'
    client_creds_b64 = base64.b64encode(client_creds.encode())
    token_headers = {
        'Authorization': f'Basic {client_creds_b64.decode()}'
    }
    r = requests.post(token_url, data=token_data, headers=token_headers)
    valid_request = r.status_code in range (200, 299)
    if valid_request:
        token_response_data = r.json()
        return token_response_data['access_token']
    return

def get_playlist(playlist_id, access_token):
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    r = requests.get(url, headers=headers).json()
    #print(r.keys())
    playlist = r['tracks']['items']
    #print(len(playlist))
    #print(r['tracks'].keys())
    next_100 = r['tracks']['next']
    #print(f'next 100 is {next_100}')
    while next_100 != None:
        r = requests.get(next_100, headers=headers).json()
        playlist.extend(r['items'])
        next_100 = r['next']
    return playlist

def get_all_name_and_artist(playlist):
    table = []
    for song in playlist:
        temp = []
        temp.append(song['track']['name'])
        temp.append(song['track']['artists'][0]['name'])
        table.append(temp)
    return table

def cleanup(string):
    string = string.split('-')[0]
    string = string.split(' (')[0]
    string = string.strip()
    string = re.sub(' +', ' ', string)
    string = string.replace(' ', '-')
    string = string.replace('&', 'and')
    string = re.sub('[^A-Za-z0-9-]', '', string)
    return string

def genius_url(name_and_artist):
    return 'https://genius.com/' + cleanup(name_and_artist[1]) + '-' + cleanup(name_and_artist[0]) + '-lyrics'

def scrape_genius(url):
    cycle_time = time.time()
    request = urllib.request.Request(url, None, headers)
    try:
        response = urllib.request.urlopen(request)
    except HTTPError as err:
        if err.code == 404:
            #print(str(url) + 'error')
            bad_urls.append(url)
            return
        else:
            raise
    genius_soup = bs(response, 'html.parser')
    #print(genius_soup)
    p_tag = genius_soup.p
    text = p_tag.get_text()
    text = re.sub(r'\[.*\]', '', text)
    text = re.sub('[\n]', ' ', text)
    text = re.sub(r'[^A-Za-z0-9 ]+', '', text)
    text = text.lower()
    text = text.split()
    scrape_genius.calls += 1
    end_cycle = time.time()
    print(f'spent {end_cycle-cycle_time} seconds on song {scrape_genius.calls}: {url}')
    return text

scrape_genius.calls = 0

def everything():
    total_text = []
    all_songs = get_all_name_and_artist(get_playlist('1na8htLAvxOM3cWLuaublx', get_token(client_id, client_secret)))
    #all_songs = get_all_name_and_artist(split_song())
    for pair in all_songs:
        genius_data = scrape_genius(genius_url(pair))
        if genius_data != None:
            #print(genius_data)
            total_text.extend(genius_data)
        #print(total_text)
    filtered_text = filter(lambda s: s not in COMMON_WORDS, total_text)
    print(str(len(all_songs)) + ' songs')
    print(all_songs)
    print(str(len(bad_urls)) + ' invalid urls: ' + str(bad_urls))
    separator = ' '
    return separator.join(filtered_text)
    #return Counter(filtered_text).most_common()

def get_album_covers(playlist):
    album_list = []
    for song in playlist:
        cover = song['track']['album']['images'][0]['url']
        if cover not in album_list:
            album_list.append(cover)
    return album_list

def download_album_covers():
    album_covers = get_album_covers(get_playlist(('3V9lwpgW0JHH9ORXbMrjfQ'),  get_token(client_id, client_secret)))
    counter = 1062
    for link in album_covers:
        counter += 1
        urllib.request.urlretrieve(link, f'cover{counter}.jpg')

download_album_covers()

""" result = everything()
wordcloud = WordCloud(width = 800, height = 800, 
				background_color ='white',
				min_font_size = 10).generate(result) 

# plot the WordCloud image					 
plt.figure(figsize = (8, 8), facecolor = None) 
plt.imshow(wordcloud) 
plt.axis("off") 
plt.tight_layout(pad = 0) 

plt.savefig("mygraph.png") 

end = time.time()
print(end - start) """
