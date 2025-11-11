import json
import requests
import base64
import datetime
from typing import List, Dict, Tuple
import os

# Configuration file paths
LAST_RUN_FILE = 'last_run.json'
SONG_LOG_FILE = 'song_log.json'

# Spotify API credentials
CLIENT_ID = '36939ed42fef4a33b670d4a6b6b64db7'
CLIENT_SECRET = '620a5965374c4330b418b277cd522183'

def get_access_token(client_id: str, client_secret: str) -> str:
    """Get Spotify API access token using client credentials flow."""
    token_url = 'https://accounts.spotify.com/api/token'
    token_data = {'grant_type': 'client_credentials'}
    client_creds = f'{client_id}:{client_secret}'
    client_creds_b64 = base64.b64encode(client_creds.encode())
    token_headers = {'Authorization': f'Basic {client_creds_b64.decode()}'}
    
    r = requests.post(token_url, data=token_data, headers=token_headers)
    if r.status_code in range(200, 299):
        return r.json()['access_token']
    raise Exception(f"Failed to get access token: {r.status_code}")

def extract_playlist_id(playlist_link: str) -> str:
    """Extract playlist ID from Spotify URL."""
    # Handle both full URLs and IDs
    if 'spotify.com/playlist/' in playlist_link:
        playlist_id = playlist_link.split('playlist/')[1].split('?')[0]
    else:
        playlist_id = playlist_link
    return playlist_id

def get_playlist_with_dates(playlist_id: str, access_token: str) -> Tuple[List[Dict], str]:
    """
    Get all tracks from a playlist with their added_at dates.
    Returns (tracks_list, playlist_name)
    """
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        raise Exception(f"Failed to get playlist: {r.status_code}")
    
    data = r.json()
    playlist_name = data['name']
    tracks = data['tracks']['items']
    next_url = data['tracks']['next']
    
    # Handle pagination
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
        if item['track'] is None:  # Skip null tracks
            continue
        added_at_str = item['added_at']
        added_at = datetime.datetime.strptime(added_at_str, '%Y-%m-%dT%H:%M:%SZ')
        if added_at > since_date:
            new_tracks.append(item)
    return new_tracks

def load_last_run_date() -> datetime.datetime:
    """Load the last run date from file, or return a default date."""
    if os.path.exists(LAST_RUN_FILE):
        with open(LAST_RUN_FILE, 'r') as f:
            data = json.load(f)
            return datetime.datetime.fromisoformat(data['last_run'])
    # Default to 30 days ago if no previous run
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

def add_tracks_to_playlist(playlist_id: str, track_uris: List[str], access_token: str):
    """
    Add tracks to a playlist. 
    Note: This requires user authentication with playlist-modify-public/private scopes.
    The client credentials flow doesn't have permission to modify playlists.
    """
    url = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Spotify allows max 100 tracks per request
    batch_size = 100
    for i in range(0, len(track_uris), batch_size):
        batch = track_uris[i:i + batch_size]
        data = {'uris': batch}
        r = requests.post(url, headers=headers, json=data)
        if r.status_code not in range(200, 299):
            print(f"Warning: Failed to add batch {i//batch_size + 1}: {r.status_code}")
            print(f"Response: {r.text}")

def save_song_log(log_data: List[Dict]):
    """Save the song log with playlist information."""
    # Load existing log if it exists
    existing_log = []
    if os.path.exists(SONG_LOG_FILE):
        with open(SONG_LOG_FILE, 'r') as f:
            existing_log = json.load(f)
    
    # Add new entry
    entry = {
        'timestamp': datetime.datetime.now().isoformat(),
        'playlists': log_data
    }
    existing_log.append(entry)
    
    with open(SONG_LOG_FILE, 'w') as f:
        json.dump(existing_log, f, indent=2)

def main():
    """Main function to track and aggregate new songs from multiple playlists."""
    
    # Configuration: Add your playlist links here
    PLAYLIST_LINKS = [
        # Example: 'https://open.spotify.com/playlist/XXXXXXXXX',
        # Add your playlists here
    ]
    
    # Optional: specify target playlist ID where songs should be added
    TARGET_PLAYLIST_ID = None  # Set this to your target playlist ID
    
    print("=" * 60)
    print("Spotify New Songs Tracker")
    print("=" * 60)
    
    # Get access token
    print("\n[1/5] Authenticating with Spotify...")
    access_token = get_access_token(CLIENT_ID, CLIENT_SECRET)
    print("✓ Authentication successful")
    
    # Load last run date
    print("\n[2/5] Loading last run date...")
    last_run = load_last_run_date()
    print(f"✓ Checking for songs added since: {last_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Process each playlist
    print("\n[3/5] Processing playlists...")
    all_new_tracks = []
    log_data = []
    
    for idx, playlist_link in enumerate(PLAYLIST_LINKS, 1):
        try:
            playlist_id = extract_playlist_id(playlist_link)
            print(f"\n  Processing playlist {idx}/{len(PLAYLIST_LINKS)}: {playlist_id}")
            
            tracks, playlist_name = get_playlist_with_dates(playlist_id, access_token)
            print(f"  - Playlist name: {playlist_name}")
            print(f"  - Total tracks in playlist: {len(tracks)}")
            
            new_tracks = filter_songs_by_date(tracks, last_run)
            print(f"  - New tracks found: {len(new_tracks)}")
            
            # Store track info for logging
            track_infos = [get_track_info(t) for t in new_tracks]
            
            if new_tracks:
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
            print(f"  ✗ Error processing playlist {playlist_link}: {e}")
    
    print(f"\n✓ Total new tracks across all playlists: {len(all_new_tracks)}")
    
    # Display summary
    print("\n[4/5] Summary of new songs:")
    print("-" * 60)
    for entry in log_data:
        print(f"\n{entry['playlist_name']}:")
        print(f"  Songs {entry['start_index']} to {entry['end_index']-1} ({entry['count']} total)")
        for i, track in enumerate(entry['tracks'][:5]):  # Show first 5
            print(f"    - {track['name']} by {track['artist']}")
        if len(entry['tracks']) > 5:
            print(f"    ... and {len(entry['tracks']) - 5} more")
    
    # Save log
    if log_data:
        save_song_log(log_data)
        print(f"\n✓ Song log saved to {SONG_LOG_FILE}")
    
    # Add tracks to target playlist if specified
    print("\n[5/5] Adding tracks to target playlist...")
    if TARGET_PLAYLIST_ID and all_new_tracks:
        print("⚠ Note: Adding tracks requires user authentication (OAuth).")
        print("  Client credentials flow doesn't have playlist modification permissions.")
        print(f"  You would need to implement OAuth to add {len(all_new_tracks)} tracks")
        print(f"  to playlist {TARGET_PLAYLIST_ID}")
        
        # Uncomment this if you have user OAuth token:
        # track_uris = [get_track_uri(t) for t in all_new_tracks]
        # add_tracks_to_playlist(TARGET_PLAYLIST_ID, track_uris, access_token)
    elif not TARGET_PLAYLIST_ID:
        print("  No target playlist specified. Skipping...")
    else:
        print("  No new tracks to add.")
    
    # Save timestamp for next run
    save_last_run_date()
    print(f"\n✓ Last run timestamp saved to {LAST_RUN_FILE}")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)

if __name__ == '__main__':
    main()

