import re

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