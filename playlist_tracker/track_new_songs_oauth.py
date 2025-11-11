"""
Spotify New Songs Tracker with OAuth Authentication
This version can actually add songs to playlists using user authentication.
"""

import json
import requests
import datetime
from typing import List, Dict, Tuple
import os
import sys
from pathlib import Path
from urllib.parse import urlencode
import webbrowser

# Add parent directory to path to import shared config
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

# Configuration file paths
LAST_RUN_FILE = 'last_run.json'
SONG_LOG_FILE = 'song_log.json'
TOKEN_CACHE_FILE = 'spotify_token_cache.json'
CONFIG_FILE = 'config.json'

def load_config() -> Dict:
    """Load playlist configuration from config.json"""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: {CONFIG_FILE} not found.")
        print("\nPlease create config.json with your playlist settings:")
        print(json.dumps({
            "redirect_uri": "http://localhost:8888/callback",
            "source_playlists": [
                "https://open.spotify.com/playlist/YOUR_PLAYLIST_ID_1",
                "https://open.spotify.com/playlist/YOUR_PLAYLIST_ID_2"
            ],
            "target_playlist_id": "YOUR_TARGET_PLAYLIST_ID"
        }, indent=2))
        exit(1)
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_user_token(client_id: str, client_secret: str, redirect_uri: str) -> str:
    """
    Get user access token using Authorization Code Flow.
    This requires manual intervention to authorize the app.
    """
    # Check if we have a cached token
    if os.path.exists(TOKEN_CACHE_FILE):
        with open(TOKEN_CACHE_FILE, 'r') as f:
            token_data = json.load(f)
            # Check if token is still valid (with 5 min buffer)
            expires_at = datetime.datetime.fromisoformat(token_data['expires_at'])
            if datetime.datetime.now() < expires_at - datetime.timedelta(minutes=5):
                return token_data['access_token']
            # Try to refresh if we have a refresh token
            elif 'refresh_token' in token_data:
                return refresh_access_token(client_id, client_secret, token_data['refresh_token'])
    
    # Need to authorize
    scope = 'playlist-modify-public playlist-modify-private playlist-read-private'
    
    auth_url = 'https://accounts.spotify.com/authorize?' + urlencode({
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': scope
    })
    
    print("\n" + "="*60)
    print("Authorization Required")
    print("="*60)
    print("\nOpening browser for Spotify authorization...")
    print("After authorizing, copy the URL you're redirected to.")
    webbrowser.open(auth_url)
    
    redirect_response = input("\nPaste the full redirect URL here: ")
    
    # Extract code from URL
    if '?code=' in redirect_response:
        code = redirect_response.split('?code=')[1].split('&')[0]
    else:
        print("Error: Could not extract code from URL")
        exit(1)
    
    # Exchange code for token
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    r = requests.post(token_url, data=token_data)
    if r.status_code != 200:
        print(f"Error getting token: {r.status_code}")
        print(r.text)
        exit(1)
    
    response = r.json()
    access_token = response['access_token']
    expires_in = response['expires_in']
    refresh_token = response.get('refresh_token')
    
    # Cache the token
    cache_data = {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_at': (datetime.datetime.now() + datetime.timedelta(seconds=expires_in)).isoformat()
    }
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    return access_token

def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Refresh an expired access token."""
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    r = requests.post(token_url, data=token_data)
    if r.status_code != 200:
        print(f"Error refreshing token: {r.status_code}")
        # Remove invalid cache
        if os.path.exists(TOKEN_CACHE_FILE):
            os.remove(TOKEN_CACHE_FILE)
        return None
    
    response = r.json()
    access_token = response['access_token']
    expires_in = response['expires_in']
    
    # Update cache
    cache_data = {
        'access_token': access_token,
        'refresh_token': refresh_token,  # Keep the same refresh token
        'expires_at': (datetime.datetime.now() + datetime.timedelta(seconds=expires_in)).isoformat()
    }
    with open(TOKEN_CACHE_FILE, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    return access_token

def extract_playlist_id(playlist_link: str) -> str:
    """Extract playlist ID from Spotify URL."""
    if 'spotify.com/playlist/' in playlist_link:
        return playlist_link.split('playlist/')[1].split('?')[0]
    return playlist_link

def get_playlist_with_dates(playlist_id: str, access_token: str) -> Tuple[List[Dict], str]:
    """Get all tracks from a playlist with their added_at dates."""
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to get playlist: {r.status_code} - {r.text}")
    
    data = r.json()
    playlist_name = data['name']
    tracks = data['tracks']['items']
    next_url = data['tracks']['next']
    
    while next_url:
        r = requests.get(next_url, headers=headers)
        if r.status_code == 200:
            data = r.json()
            tracks.extend(data['items'])
            next_url = data['next']
        else:
            break
    
    return tracks, playlist_name

def filter_songs_by_date(tracks: List[Dict], since_date: datetime.datetime) -> List[Dict]:
    """Filter tracks that were added after the given date."""
    new_tracks = []
    for item in tracks:
        if item['track'] is None:
            continue
        added_at_str = item['added_at']
        added_at = datetime.datetime.strptime(added_at_str, '%Y-%m-%dT%H:%M:%SZ')
        if added_at > since_date:
            new_tracks.append(item)
    return new_tracks

def load_last_run_date() -> datetime.datetime:
    """Load the last run date from file."""
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            data = json.load(f)
            return datetime.datetime.fromisoformat(data['last_run'])
    return datetime.datetime.now() - datetime.timedelta(days=30)

def save_last_run_date():
    """Save the current timestamp as the last run date."""
    data = {'last_run': datetime.datetime.now().isoformat()}
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_track_uri(track_item: Dict) -> str:
    """Extract track URI from track item."""
    return track_item['track']['uri']

def get_track_info(track_item: Dict) -> Dict:
    """Extract relevant track information."""
    track = track_item['track']
    return {
        'uri': track['uri'],
        'name': track['name'],
        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown',
        'added_at': track_item['added_at']
    }

def get_current_user(access_token: str) -> str:
    """Get the current user's Spotify ID."""
    url = 'https://api.spotify.com/v1/me'
    headers = {'Authorization': f'Bearer {access_token}'}
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to get user info: {r.status_code} - {r.text}")
    
    return r.json()['id']

def create_playlist(user_id: str, playlist_name: str, access_token: str, 
                   description: str = "", public: bool = True) -> str:
    """
    Create a new playlist for the user.
    Returns the playlist ID.
    """
    url = f'https://api.spotify.com/v1/users/{user_id}/playlists'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'name': playlist_name,
        'description': description,
        'public': public
    }
    
    r = requests.post(url, headers=headers, json=data)
    if r.status_code not in range(200, 299):
        raise Exception(f"Failed to create playlist: {r.status_code} - {r.text}")
    
    playlist_id = r.json()['id']
    return playlist_id

def add_tracks_to_playlist(playlist_id: str, track_uris: List[str], access_token: str):
    """Add tracks to a playlist."""
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Spotify allows max 100 tracks per request
    batch_size = 100
    total_added = 0
    
    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i:i + batch_size]
        data = {'uris': batch}
        r = requests.post(url, headers=headers, json=data)
        
        if r.status_code in range(200, 299):
            total_added += len(batch)
            print(f"  ✓ Added batch {i//batch_size + 1} ({len(batch)} tracks)")
        else:
            print(f"  ✗ Failed to add batch {i//batch_size + 1}: {r.status_code}")
            print(f"    Response: {r.text}")
    
    return total_added

def save_song_log(log_data: List[Dict]):
    """Save the song log with playlist information."""
    existing_log = []
    if os.path.exists(SONG_LOG_FILE):
        with open(SONG_LOG_FILE, 'r') as f:
            existing_log = json.load(f)
    
    entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'playlists': log_data
    }
    existing_log.append(entry)
    
    with open(SONG_LOG_FILE, 'w') as f:
        json.dump(existing_log, f, indent=2)

def main():
    """Main function to track and aggregate new songs."""
    
    print("=" * 60)
    print("Spotify New Songs Tracker (OAuth Version)")
    print("=" * 60)
    
    # Load configuration
    print("\n[1/6] Loading configuration...")
    print(f"✓ Credentials loaded from .env")
    print(f"  - Client ID: {SPOTIFY_CLIENT_ID[:10]}...")
    
    config = load_config()
    REDIRECT_URI = config.get('redirect_uri', 'http://localhost:8888/callback')
    PLAYLIST_LINKS = config['source_playlists']
    TARGET_PLAYLIST_ID = config.get('target_playlist_id')
    CREATE_NEW_PLAYLIST = config.get('create_new_playlist', False)
    PLAYLIST_NAME_TEMPLATE = config.get('playlist_name_template', 'New Songs - {date}')
    PLAYLIST_DESCRIPTION = config.get('playlist_description', 'Automatically aggregated new songs')
    PLAYLIST_PUBLIC = config.get('playlist_public', True)
    
    print(f"✓ Playlist configuration loaded")
    print(f"  - Source playlists: {len(PLAYLIST_LINKS)}")
    if CREATE_NEW_PLAYLIST:
        print(f"  - Mode: Create new playlist")
        print(f"  - Template: {PLAYLIST_NAME_TEMPLATE}")
    else:
        print(f"  - Mode: Use existing playlist")
        print(f"  - Target playlist: {TARGET_PLAYLIST_ID or 'Not specified'}")
    
    # Get access token
    print("\n[2/6] Authenticating with Spotify...")
    access_token = get_user_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, REDIRECT_URI)
    print("✓ Authentication successful")
    
    # Load last run date
    print("\n[3/6] Loading last run date...")
    last_run = load_last_run_date()
    print(f"✓ Checking for songs added since: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Process playlists
    print("\n[4/6] Processing playlists...")
    all_new_tracks = []
    log_data = []
    
    for idx, playlist_link in enumerate(PLAYLIST_LINKS, 1):
        try:
            playlist_id = extract_playlist_id(playlist_link)
            print(f"\n  Processing playlist {idx}/{len(PLAYLIST_LINKS)}")
            
            tracks, playlist_name = get_playlist_with_dates(playlist_id, access_token)
            print(f"  - Name: {playlist_name}")
            print(f"  - Total tracks: {len(tracks)}")
            
            new_tracks = filter_songs_by_date(tracks, last_run)
            print(f"  - New tracks: {len(new_tracks)}")
            
            if new_tracks:
                track_infos = [get_track_info(t) for t in new_tracks]
                log_entry = {
                    'playlist_id': playlist_id,
                    'playlist_name': playlist_name,
                    'start_index': len(all_new_tracks),
                    'count': len(new_tracks),
                    'end_index': len(all_new_tracks) + len(new_tracks),
                    'tracks': track_infos
                }
                log_data.append(log_entry)
                all_new_tracks.extend(new_tracks)
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print(f"\n✓ Total new tracks: {len(all_new_tracks)}")
    
    # Display summary
    print("\n[5/6] Summary:")
    print("-" * 60)
    for entry in log_data:
        print(f"\n{entry['playlist_name']}:")
        print(f"  Index range: {entry['start_index']} to {entry['end_index']-1} ({entry['count']} songs)")
        for track in entry['tracks'][:3]:
            print(f"    • {track['name']} - {track['artist']}")
        if len(entry['tracks']) > 3:
            print(f"    ... and {len(entry['tracks']) - 3} more")
    
    # Save log
    if log_data:
        save_song_log(log_data)
        print(f"\n✓ Log saved to {SONG_LOG_FILE}")
    
    # Add to target playlist
    print("\n[6/6] Adding tracks to playlist...")
    if all_new_tracks:
        track_uris = [get_track_uri(t) for t in all_new_tracks]
        
        # Determine playlist ID
        playlist_id = None
        if CREATE_NEW_PLAYLIST:
            # Create new playlist
            try:
                user_id = get_current_user(access_token)
                
                # Generate playlist name from template
                now = datetime.datetime.now()
                playlist_name = PLAYLIST_NAME_TEMPLATE.format(
                    date=now.strftime('%Y-%m-%d'),
                    datetime=now.strftime('%Y-%m-%d %H:%M'),
                    month=now.strftime('%B %Y'),
                    year=now.strftime('%Y')
                )
                
                print(f"  Creating new playlist: {playlist_name}")
                playlist_id = create_playlist(
                    user_id, 
                    playlist_name, 
                    access_token,
                    description=PLAYLIST_DESCRIPTION,
                    public=PLAYLIST_PUBLIC
                )
                print(f"  ✓ Playlist created: {playlist_id}")
                
            except Exception as e:
                print(f"  ✗ Failed to create playlist: {e}")
        else:
            playlist_id = TARGET_PLAYLIST_ID
        
        # Add tracks to playlist
        if playlist_id:
            try:
                total_added = add_tracks_to_playlist(playlist_id, track_uris, access_token)
                print(f"\n✓ Successfully added {total_added} tracks to playlist")
                print(f"  Playlist URL: https://open.spotify.com/playlist/{playlist_id}")
            except Exception as e:
                print(f"  ✗ Failed to add tracks: {e}")
        elif not CREATE_NEW_PLAYLIST and not TARGET_PLAYLIST_ID:
            print("  ⚠ No target playlist specified in config")
    else:
        print("  No new tracks to add")
    
    # Save timestamp
    save_last_run_date()
    print(f"\n✓ Timestamp saved to {LAST_RUN_FILE}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == '__main__':
    main()

