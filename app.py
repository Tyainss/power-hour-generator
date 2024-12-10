import streamlit as st
import yt_dlp
import io
import os
import re
from pydub import AudioSegment
import tempfile
import subprocess
import random
import uuid

from utils.config_manager import ConfigManager

SOUND_CLIPS_PATH = 'sound_clips/'

def validate_playlist_name(name: str) -> tuple:
    """Validates the playlist name for invalid characters."""
    invalid_chars = r'[<>:"/\\|?*]'
    valid = True
    message = ''
    if re.search(invalid_chars, name):
        valid = False 
        message = """
        The playlist name contains invalid characters: < > : " / \\ | ? *\n
        Please remove any invalid character.
        """
    
    return valid, message

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

def create_playlist(music_links, start_seconds):
    """
    Creates a playlist by processing music from YouTube links.
    """
    final_song = AudioSegment.empty()

    # Load horn and personal tag and trimm them
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

@st.cache_data
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

def _load_sound_clips(uploaded_tchica=False):
    """Load the sound clips necessary for the playlist"""
    ## Intro sound
    personal_tag = AudioSegment.from_file(SOUND_CLIPS_PATH + 'signature_tag.m4a')

    ## In-between sounds
    # Process the uploaded file or use the default tchica_tchica sound
    if uploaded_tchica_file:
        # Save the uploaded file to a temporary location
        with open("temp_tchica.m4a", "wb") as temp_file:
            temp_file.write(uploaded_tchica_file.read())
        
        # Load the uploaded file as an AudioSegment
        tchica = AudioSegment.from_file("temp_tchica.m4a")
        st.sidebar.success("Custom sound loaded successfully!")
    else:
        # Use the default 'tchica_tchica.m4a' if no file is uploaded
        tchica = AudioSegment.from_file(SOUND_CLIPS_PATH + 'tchica_tchica.m4a', format="m4a")[:-300]
    
    # Load horn and trimm it
    horn = AudioSegment.from_file(SOUND_CLIPS_PATH + 'horn.m4a', format="m4a")[:-1300]

    sound_clips = {
        'personal_tag': personal_tag,
        'tchica': tchica,
        'horn': horn,
    }
    return sound_clips

def main():
    st.title(':beer: Power Hour Playlist Maker')

    # Config Sidebar
    st.sidebar.title('Playlist Options')
        # Button to select playlist order
    order_option = st.sidebar.radio(
        'Select the playlist order:',
        options=['In Order', 'Random Order'],
        index=0,  # Default to "In Order"
        help='Choose whether the playlist follows the entered song order or shuffles the songs randomly.'
    )
    st.sidebar.divider()
        # Widget for uploading custom tchica_tchica
    with st.sidebar.expander(label="Upload a custom sound to replace 'tchica_tchica.m4a':",):
        uploaded_tchica_file = st.file_uploader(
            "Upload a custom sound to replace 'tchica_tchica.m4a':",
            type=['mp3', 'wav', 'm4a'],
            label_visibility='hidden',
        )

    # Define sounds

    
    # Introductory section
    with st.expander('About this App', expanded=True, icon=':material/info:'):
        st.markdown("""
        ### :beer: Power Hour
        This app allows you to create a personalized Power Hour playlist by downloading and combining audio clips from YouTube.
        Follow these steps to create your playlist:
        1. Enter a name for your playlist.
        2. Specify the number of songs you want in the playlist.
        3. Provide YouTube links for each song and optionally set a custom start time for each clip.
        4. Click "Create Playlist file" to generate the MP3 file.
        5. Download your playlist and enjoy your personalized Power Hour!

        **Note:** Each song will be trimmed to 1 minute starting from the provided start time.
        """)

    # Get playlist name from user
    playlist_name = st.text_input("Enter Playlist Name:")
    if playlist_name:
        is_valid, warning_msg = validate_playlist_name(playlist_name)
        if not is_valid:
            st.error(warning_msg)
            return
    else:
        st.warning("Please enter a playlist name.")
        return
    
    # Initialize session state for song titles if not already done
    if "song_titles" not in st.session_state:
        st.session_state["song_titles"] = {}

    num_songs = st.number_input("Enter number of songs:", min_value=1, max_value=90, value=60)

    with st.container(height=500):

        # Initialize music_links and start_seconds dictionaries
        music_links = []
        start_seconds = {}
        
        for i in range(num_songs):
            col1, col2 = st.columns([4, 1])
            with col1:
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
                    st.write(f"{title}")
                
            with col2:
                seconds = st.number_input(f"Start time for song {i + 1}", min_value=0, value=0, key=f"start_{i}")
            
            if url:
                music_links.append(url)
                start_seconds[url] = seconds
        
    if len(music_links) < num_songs:
        st.warning("Please enter all the song links.")
        return
    
    # Adjust song order based on sidebar selection
    if order_option == "Random Order":
        music_links = random.sample(music_links, len(music_links))

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
    cm = ConfigManager('config.json')
    st.set_page_config(layout='wide', page_title='Power Hour', page_icon=':beer:')
    main()


# TODO

# Try dragging components: https://draggable-container-demo.streamlit.app/
# X. Try asynchronous processing 1 more time