import streamlit as st
import yt_dlp
import io
import os
from pydub import AudioSegment
import tempfile

SOUND_CLIPS_PATH = 'sound_clips/'

def download_audio(url: str, show_progress: bool = False, _progress_bar=None):
    """Download audio from YouTube and use a temporary file for pydub."""
    fd, temp_path = tempfile.mkstemp()  # Temporary base path without extension
    os.close(fd)

    ydl_opts = {
        'format': 'bestaudio',
        'outtmpl': temp_path,  # Use base path
        'quiet': True,
        'verbose': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }],
        # 'ffmpeg_location': 'D:\\ytdl\\ffmpeg.exe',  # Path to ffmpeg
    }


    if show_progress and _progress_bar:
        ydl_opts['progress_hooks'] = [lambda d: _progress_bar.progress(d.get('percent', 0))]

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    temp_path_mp3 = f"{temp_path}.mp3"
    if not os.path.exists(temp_path_mp3):
        temp_path_mp3 = f"{temp_path_mp3}.mp3"

    if not os.path.exists(temp_path_mp3):
        raise FileNotFoundError(f"Downloaded file not found: {temp_path_mp3}")
    if os.path.getsize(temp_path_mp3) == 0:
        raise ValueError("Downloaded file is empty.")

    # Return the path instead of loading into memory
    return temp_path_mp3

def download_and_convert_audio(url: str):
    """Downloads raw audio from YouTube and converts it to MP3 using ffmpeg."""
    # Step 1: Download raw audio file
    ydl_opts = {
        'format': 'bestaudio',  # Download the best audio quality available
        'outtmpl': 'raw_audio.%(ext)s',  # Save as 'raw_audio' with correct extension
        'quiet': False,  # Enable logging for debugging
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    raw_file = info['requested_downloads'][0]['filepath']  # Path to the downloaded raw file
    print(f"Raw file downloaded: {raw_file}")

    # Step 2: Convert to MP3 using ffmpeg
    converted_file = "output.mp3"  # Output MP3 file
    command = f'ffmpeg -i "{raw_file}" -vn -acodec mp3 "{converted_file}"'
    os.system(command)

    # Step 3: Clean up the raw file (optional)
    if os.path.exists(raw_file):
        os.remove(raw_file)

    print(f"Converted file saved as: {converted_file}")
    return converted_file

def create_playlist(music_links, start_seconds, show_progress=False):
    """
    Creates a playlist by processing music from YouTube links.
    """
    final_song = AudioSegment.empty()

    # Load horn and personal tag
    horn = AudioSegment.from_file(SOUND_CLIPS_PATH + 'horn.m4a', format="m4a")[:-1300]
    tchica = AudioSegment.from_file(SOUND_CLIPS_PATH + 'tchica_tchica.m4a', format="m4a")[:-300]
    personal_tag = AudioSegment.from_file(SOUND_CLIPS_PATH + 'signature_tag.m4a')

    total_songs = len(music_links)

    if show_progress:
        progress_bar = st.progress(0)

    with st.spinner("Downloading songs..."):
        for i, url in enumerate(music_links):
            # Download each song and get file path
            # audio_file_path = download_audio(url, show_progress, progress_bar)
            audio_file_path = download_and_convert_audio(url)
            
            # Load the song directly from the file path
            sound = AudioSegment.from_file(audio_file_path, format="mp3")
            
            # Get start time for the song (in milliseconds)
            start_time = start_seconds.get(url, 0) * 1000  # Convert seconds to milliseconds
            
            # Trim the song to the specified start time and first minute
            sound = sound[start_time:start_time + 60000]  # First 1 minute in milliseconds
            
            # Add personal tag for the first song
            if i == 0:
                final_song += personal_tag
                final_song += sound
            else:
                final_song += tchica
                final_song += horn
                final_song += sound

            # Cleanup the temporary file
            os.remove(audio_file_path)

            # Update progress bar
            if show_progress:
                progress_bar.progress((i + 1) / total_songs)
    
    return final_song



def main():
    st.title("Power Hour Playlist Maker")
    
    # Get playlist name from user
    playlist_name = st.text_input("Enter Playlist Name:")
    if not playlist_name:
        st.warning("Please enter a playlist name.")
        return
    
    # Initialize music_links and start_seconds dictionaries
    music_links = []
    start_seconds = {}

    num_songs = st.number_input("Enter number of songs:", min_value=1, max_value=60, value=60)
    
    for i in range(num_songs):
        col1, col2 = st.columns([4, 1])
        with col1:
            link = st.text_input(f"Enter YouTube link for song {i + 1}:")
        with col2:
            seconds = st.number_input(f"Start time for song {i + 1}", min_value=0, value=0, key=f"start_{i}")
        
        if link:
            music_links.append(link)
            start_seconds[link] = seconds
    
    if len(music_links) < num_songs:
        st.warning("Please enter all the song links and start times.")
        return
    
    # Create playlist with or without progress bar
    show_progress = st.checkbox("Show download progress")
    
    # Only enable download button when all links and start times are entered
    if st.button("Download Playlist"):
        final_song = create_playlist(music_links, start_seconds, show_progress)
        
        # Convert final playlist to byte data for download
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            final_song.export(temp_file.name, format="mp3")
            temp_file_path = temp_file.name
        
        # Allow the user to download the generated playlist
        with open(temp_file_path, 'rb') as file:
            st.download_button(
                label="Download Playlist",
                data=file,
                file_name=f"{playlist_name}.mp3",
                mime="audio/mp3"
            )

if __name__ == "__main__":
    main()
