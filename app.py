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

from utils.validations import validate_playlist_name
from utils.youtube_handler import download_and_convert_audio, fetch_song_title
from utils.audio_processor import load_sound_clips, create_playlist

from utils.config_manager import ConfigManager


def _initialize_session_state():
    # Initialize session state for song titles if not already done
    if "song_titles" not in st.session_state:
        st.session_state["song_titles"] = {}

    if "uploaded_tchica" not in st.session_state:
        st.session_state["uploaded_tchica"] = None


def main():
    st.title(':beer: Power Hour Playlist Maker')

    # Initialize Session State
    _initialize_session_state()

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
        if uploaded_tchica_file:
            st.session_state["uploaded_tchica"] = uploaded_tchica_file
            st.success("Custom sound loaded successfully!")

    # Define sounds
    sound_clips = load_sound_clips(cm, st.session_state)
    
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
    

    num_songs = st.number_input("Enter number of songs:", min_value=1, max_value=cm.MAX_NUMBER_SONGS, value=cm.DEFAULT_NUMBER_SONGS)

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
        final_song = create_playlist(music_links, start_seconds, sound_clips, cm)
        
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
# 1. Improve 'About This App' and README

# Try dragging components: https://draggable-container-demo.streamlit.app/
# X. Try asynchronous processing 1 more time