from pydub import AudioSegment
import os
import streamlit as st

from utils.youtube_handler import  download_and_convert_audio

@st.cache_resource(show_spinner=False)
def load_sound_clips(_config_manager, _session_state):
    """
    Load the sound clips necessary for the playlist.

    Args:
        _config_manager (ConfigManager): Instance of ConfigManager for paths and configurations.
        _session_state (dict): Streamlit session state to check for uploaded files.

    Returns:
        dict: A dictionary containing personal_tag, tchica, and horn AudioSegments.
    """
    # Intro sound
    personal_tag = AudioSegment.from_file(_config_manager.get('SOUND_CLIPS_PATH') + 'signature_tag.m4a')

    # In-between sounds
    if _session_state.get('uploaded_tchica'):
        uploaded_tchica_file = _session_state['uploaded_tchica']
        with open('temp_tchica.m4a', 'wb') as temp_file:
            temp_file.write(uploaded_tchica_file.read())
        tchica = AudioSegment.from_file('temp_tchica.m4a')
    else:
        tchica = AudioSegment.from_file(
            _config_manager.get('SOUND_CLIPS_PATH') + 'tchica_tchica.m4a'
        )[:-300]

    # Load horn and trim it
    horn = AudioSegment.from_file(_config_manager.get('SOUND_CLIPS_PATH') + 'horn.m4a')[:-1300]

    return {
        'personal_tag': personal_tag,
        'tchica': tchica,
        'horn': horn,
    }

def create_playlist(music_links, start_seconds, sound_clips, config_manager):
    """
    Creates a playlist by processing music from YouTube links.

    Args:
        music_links (list): List of YouTube links to process.
        start_seconds (dict): Dictionary mapping URLs to start times.
        sound_clips (dict): Preloaded sound clips (horn, tchica, personal_tag).
        config_manager (ConfigManager): Instance of ConfigManager for configurations.

    Returns:
        AudioSegment: The final compiled audio playlist.
    """
    final_song = AudioSegment.empty()

    # Load sound clips
    horn = sound_clips['horn']
    tchica = sound_clips['tchica']
    personal_tag = sound_clips['personal_tag']

    total_songs = len(music_links)
    progress_bar = st.progress(0)

    with st.spinner('Downloading songs...'):
        for i, url in enumerate(music_links):
            # Download each song and get file path
            audio_file_path = download_and_convert_audio(url)

            # Load the song directly from the file path
            sound = AudioSegment.from_file(audio_file_path, format='mp3')

            # Get start time for the song (in milliseconds)
            start_time = start_seconds.get(url, 0) * 1000  # Convert seconds to milliseconds

            # Trim the song to the specified start time and duration
            duration = config_manager.get('DEFAULT_SONG_DURATION', 60) * 1000
            sound = sound[start_time : start_time + duration]

            # Add personal tag for the first song and sound bites in between songs
            if i == 0:
                final_song += personal_tag + sound
            else:
                final_song += tchica + horn + sound

            # Cleanup the temporary file
            os.remove(audio_file_path)

            # Update progress bar
            progress_bar.progress((i + 1) / total_songs)

    return final_song