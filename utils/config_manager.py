import json
import os

class ConfigManager:
    CONFIG_PATH_DEFAULT = 'config.json'
    
    def __init__(self, config_path = CONFIG_PATH_DEFAULT) -> None:
        self.config = self.load_json(config_path)

        # Resolve absolute path for SOUND_CLIPS_PATH
        self.SOUND_CLIPS_PATH = os.path.abspath(self.config['SOUND_CLIPS_PATH'])
        self.DEFAULT_SONG_DURATION = self.config['DEFAULT_SONG_DURATION']
        self.DEFAULT_NUMBER_SONGS = self.config['DEFAULT_NUMBER_SONGS']
        self.MAX_NUMBER_SONGS = self.config['MAX_NUMBER_SONGS']

    def load_json(self, path: str, encoding: str = 'utf-8') -> dict:
        try:
            with open(path, 'r', encoding=encoding) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f'Error: The file {path} does not exist.')
            return {}
        except json.JSONDecodeError:
            logger.error(f'Error: The file {path} is not a valid JSON.')
            return {}

    def get(self, key, default=None):
        return self.config.get(key, default)