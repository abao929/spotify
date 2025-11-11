"""
Shared configuration for loading Spotify credentials from environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Spotify credentials
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError(
        "Spotify credentials not found! "
        "Please create a .env file in the project root with:\n"
        "SPOTIFY_CLIENT_ID=your_id\n"
        "SPOTIFY_CLIENT_SECRET=your_secret"
    )

