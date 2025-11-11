import json
import requests
import base64
import datetime
import csv
from collections import Counter
import timeit
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

client_id = SPOTIFY_CLIENT_ID
client_secret = SPOTIFY_CLIENT_SECRET

token_url = 'https://accounts.spotify.com/api/token'
method = 'POST'
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
    now = datetime.datetime.now()
    access_token = token_response_data['access_token']
    expires_in = token_response_data['expires_in']
    expires = now + datetime.timedelta(seconds=expires_in)
    did_expire = expires < now

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

#playlist = get_playlist('5USCz2dkmTbJ3nLhk4UVip', access_token) # not like the other playlists, 5 extra songs???
playlist = get_playlist('3wvz4S5XN7131OLvoI2DU3', access_token) # ching chong, 1 extra song?
#playlist = get_playlist('77wWhI7tSED6ahLhOWmAfW', access_token) # self care 120 times

song_names = []
song_artists = []
print(playlist[0]['track'].keys())
print(playlist[0]['track']['artists'][0].keys())

for song in playlist:
    song_names.append(song['track']['name'])
    song_artists.append(song['track']['artists'][0]['name'])

print(song_names)
print(song_artists)
print(f'num songs is {len(song_names)}')
print(f'num songs is {len(song_artists)}')
print(Counter(song_names).most_common())