import streamlit as st
import yt_dlp
import io
import os
from pydub import AudioSegment
import tempfile
import subprocess


SOUND_CLIPS_PATH = 'sound_clips/'

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
    converted_file = "tmp_output_audio_file.mp3"  # Output MP3 file
    # command = f'ffmpeg -i "{raw_file}" -vn -acodec mp3 "{converted_file}"'
    # os.system(command)
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

def create_playlist(music_links, start_seconds):
    """
    Creates a playlist by processing music from YouTube links.
    """
    final_song = AudioSegment.empty()

    # Load horn and personal tag
    horn = AudioSegment.from_file(SOUND_CLIPS_PATH + 'horn.m4a', format="m4a")[:-1300]
    tchica = AudioSegment.from_file(SOUND_CLIPS_PATH + 'tchica_tchica.m4a', format="m4a")[:-300]
    personal_tag = AudioSegment.from_file(SOUND_CLIPS_PATH + 'signature_tag.m4a')

    total_songs = len(music_links)
    
    progress_bar = st.progress(0)

    with st.spinner("Downloading songs..."):
        for i, url in enumerate(music_links):
            # Download each song and get file path
            audio_file_path = download_and_convert_audio(url)
            
            # Load the song directly from the file path
            sound = AudioSegment.from_file(audio_file_path, format="mp3")
            
            # Get start time for the song (in milliseconds)
            start_time = start_seconds.get(url, 0) * 1000  # Convert seconds to milliseconds
            
            # Trim the song to the specified start time and first minute
            sound = sound[start_time:start_time + 60000]  # First 1 minute in milliseconds
            
            # Add personal tag for the first song and sound bites in between songs
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
            progress_bar.progress((i + 1) / total_songs)
    
    return final_song

def fetch_song_title(url: str) -> str:
    """Fetches the song title from a YouTube URL."""
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,  # Do not download the video
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', 'Unknown Title')
    except Exception as e:
        return f"Error fetching title: {str(e)}"

def main():
    st.set_page_config(page_title='Power Hour', page_icon=':beer:') # layout='wide', 
    st.title("Power Hour Playlist Maker")
    
    # Introductory section
    with st.expander('About this App', expanded=True, icon=':material/info:'):
        st.markdown("""
        ### Power Hour
        This app allows you to create a personalized Power Hour playlist by downloading and combining audio clips from YouTube.
        Follow these steps to create your playlist:
        1. Enter a name for your playlist.
        2. Specify the number of songs you want in the playlist.
        3. Provide YouTube links for each song and optionally set a custom start time for each clip.
        4. Click "Create Playlist file" to generate the MP3 file.
        5. Download your playlist and enjoy your personalized Power Hour!

        **Note:** Each song will be trimmed to 1 minute starting from the provided start time.
        """)

    # Initialize session state for song titles if not already done
    if "song_titles" not in st.session_state:
        st.session_state["song_titles"] = {}

    # Get playlist name from user
    playlist_name = st.text_input("Enter Playlist Name:")
    if not playlist_name:
        st.warning("Please enter a playlist name.")
        return
    
    # Initialize music_links and start_seconds dictionaries
    music_links = []
    start_seconds = {}
    # song_titles = []

    num_songs = st.number_input("Enter number of songs:", min_value=1, max_value=90, value=60)
    
    for i in range(num_songs):
        col1, col2 = st.columns([4, 1])
        with col1:
            # url = st.text_input(
            #     f"Enter YouTube link for song {i + 1}:" if i >= len(song_titles) else f"Song Title: {song_titles[i]}",
            #     key=f'url_{i}'
            # )
            url = st.text_input(
                f"Enter YouTube link for song {i + 1}",
                key=f"url_{i}"
            )
            if url:
                # Fetch title if URL is new or changed
                if url not in st.session_state["song_titles"]:
                    with st.spinner("Fetching song title..."):
                        title = fetch_song_title(url)
                        st.session_state["song_titles"][url] = title
                else:
                    title = st.session_state["song_titles"][url]

                # Display the title
                st.write(f"✅ {title}")

                # # Fetch title if a URL is provided
                # if len(song_titles) <= i:
                #     title = fetch_song_title(url)
                #     song_titles.append(title)
                # else:
                #     title = song_titles[i]

                # # Update the placeholder dynamically
                # st.write(f"Song Title: {title}")
            
        with col2:
            seconds = st.number_input(f"Start time for song {i + 1}", min_value=0, value=0, key=f"start_{i}")
        
        if url:
            music_links.append(url)
            start_seconds[url] = seconds
    
    if len(music_links) < num_songs:
        st.warning("Please enter all the song links.")
        return
    
    # Only enable download button when all links and start times are entered
    if st.button("Create Playlist"):
        final_song = create_playlist(music_links, start_seconds)
        
        # Convert final playlist to byte data for download
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
            final_song.export(temp_file.name, format="mp3")
            temp_file_path = temp_file.name
        
        st.balloons()

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
