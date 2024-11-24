from urllib.parse import urlparse
import re
from typing import Tuple

def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL format and return (is_valid, error_message)."""
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return False, "Invalid URL format"
        if result.scheme not in ['http', 'https']:
            return False, "URL must use HTTP or HTTPS"
        return True, ""
    except Exception as e:
        return False, f"Invalid URL: {str(e)}"

def validate_path(path: str) -> Tuple[bool, str]:
    """Validate file path format."""
    if not path:
        return False, "Path cannot be empty"
    if re.search(r'[<>:"|?*]', path):
        return False, "Path contains invalid characters"
    return True, ""