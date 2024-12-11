import yt_dlp
import uuid
import os

def download_and_convert_audio(url: str):
    """Downloads raw audio from YouTube and converts it to MP3 using ffmpeg."""
    # Download raw audio file
    ydl_opts = {
        'format': 'bestaudio',  # Download the best audio quality available
        'outtmpl': 'tmp_raw_audio.%(ext)s',  # Save as 'tmp_raw_audio' with correct extension
        'quiet': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    raw_file = info['requested_downloads'][0]['filepath']  # Path to the downloaded raw file

    # Convert to MP3 using ffmpeg
    # converted_file = "tmp_output_audio_file.mp3"  # Output MP3 file
    unique_id = str(uuid.uuid4())
    converted_file = f"tmp_{unique_id}.mp3"
    
    command = [
        'ffmpeg',
        '-i', raw_file,
        '-vn',
        '-acodec', 'mp3',
        converted_file,
    ]

    # Suppress output
    with open(os.devnull, 'w') as devnull:
        subprocess.run(command, stdout=devnull, stderr=devnull)

    # Clean up the raw file
    if os.path.exists(raw_file):
        os.remove(raw_file)

    # print(f"Converted file saved as: {converted_file}")
    return converted_file

def fetch_song_title(url: str) -> str:
    """Fetches the song title from a YouTube URL."""
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,  # Do not download the video
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = f"✅ {info.get('title', 'Unknown Title') }"
            return title
    except Exception as e:
        return f"❌ Could not fetch song"