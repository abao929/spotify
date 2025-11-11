# Spotify Toolkit

A collection of tools for working with Spotify playlists, organized by functionality.

## 🔐 Setup

### 1. Get Spotify API Credentials
1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Create a new app (e.g., "Personal Spotify Toolkit")
3. Note your Client ID and Client Secret
4. For OAuth features, add redirect URI: `http://localhost:8888/callback`

### 2. Configure Environment
```bash
# Copy the example env file
cp shared/.env.example .env

# Edit .env with your credentials
SPOTIFY_CLIENT_ID=your_new_client_id_here
SPOTIFY_CLIENT_SECRET=your_new_client_secret_here
```

### 3. Install Dependencies
```bash
pip install requests python-dotenv

# For wordcloud features:
pip install wordcloud matplotlib beautifulsoup4

# For album mosaic features:
pip install opencv-python scikit-learn imutils
```

---

## 📁 Project Structure

```
spotify/
├── playlist_tracker/          # Track and aggregate new songs
│   ├── track_new_songs.py           # Basic version (read-only)
│   └── track_new_songs_oauth.py     # Full version (can modify playlists)
│
├── wordcloud_generator/       # Generate wordclouds from lyrics
│   └── generate_wordcloud.py
│
├── album_mosaic/             # Create rainbow mosaics from album covers
│   ├── create_mosaic.py            # Main mosaic generator
│   └── sort_by_color.py            # Color sorting utility
│
├── shared/                   # Shared utilities
│   ├── spotify_client.py           # Basic Spotify API wrapper
│   ├── config.py                   # Load credentials from .env
│   └── .env.example                # Template for credentials
│
├── .env                      # Your credentials (not in git)
└── .gitignore
```

---

## 🚀 Tools

### 1. Playlist Tracker
**Track new songs from multiple playlists and aggregate them into one**

**Location:** `playlist_tracker/`

**Features:**
- ✅ Track songs added since a specific date
- ✅ Aggregate new songs into a target playlist
- ✅ Log which songs belong to which source playlist
- ✅ Automatic timestamp tracking for incremental updates

**Usage:**
```bash
cd playlist_tracker

# Basic version (read-only, no OAuth needed)
python track_new_songs.py

# Full version (can add songs to playlists)
python track_new_songs_oauth.py
```

**Configuration:** Edit the `PLAYLIST_LINKS` and `TARGET_PLAYLIST_ID` in the scripts, or create a `config.json`.

---

### 2. Wordcloud Generator
**Generate wordclouds from playlist lyrics scraped from Genius**

**Location:** `wordcloud_generator/`

**Features:**
- Scrapes lyrics from genius.com
- Removes common words (and, the, I, etc.)
- Generates beautiful wordcloud visualizations

**Usage:**
```bash
cd wordcloud_generator

# Edit generate_wordcloud.py to set your playlist
python generate_wordcloud.py
```

---

### 3. Album Mosaic
**Create rainbow-sorted mosaics from album covers using K-means clustering**

**Location:** `album_mosaic/`

**Features:**
- Downloads album covers from playlists
- Sorts images by dominant color (HSV)
- Creates rainbow effect mosaics
- Separates colorful and B&W images

**Usage:**
```bash
cd album_mosaic

# Create a mosaic
python create_mosaic.py

# Or use the advanced sorting utility
python sort_by_color.py -i /path/to/images -o output.jpg
```

---

## 🔒 Security Notes

**Important:** Never commit your `.env` file or hardcode credentials!

- ✅ Credentials are now in `.env` (gitignored)
- ✅ Use `shared/config.py` to load credentials in your scripts
- ✅ Old credentials in git history have been scrubbed

---

## 📝 Example: Using Shared Config

Instead of hardcoding credentials, import them:

```python
# Before (❌ BAD):
client_id = 'your_id_here'
client_secret = 'your_secret_here'

# After (✅ GOOD):
from shared.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

client_id = SPOTIFY_CLIENT_ID
client_secret = SPOTIFY_CLIENT_SECRET
```

---

## 🤝 Contributing

Feel free to add more tools or improve existing ones!

---

## 📄 License

Open source - use as you like!
