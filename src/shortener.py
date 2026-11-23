"""In-memory URL shortening backed by custom hash tables."""

from urllib.parse import urlsplit

from src.base62 import ALPHABET, encode
from src.hash_table import HashTable


class URLShortener:
    """Shorten HTTP(S) URLs and expand issued base62 codes."""

    def __init__(self):
        self._url_to_code = HashTable()
        self._code_to_url = HashTable()
        self._next_id = 0

    def shorten(self, url):
        """Return a stable base62 code for a valid HTTP(S) URL."""
        if not isinstance(url, str):
            raise ValueError("URL must be a string")

        try:
            parsed = urlsplit(url)
            hostname = parsed.hostname
        except ValueError as error:
            raise ValueError("invalid URL") from error

        if (
            parsed.scheme.lower() not in ("http", "https")
            or not hostname
            or any(character.isspace() for character in parsed.netloc)
        ):
            raise ValueError("URL must have an HTTP(S) scheme and host")

        existing_code = self._url_to_code.get(url)
        if existing_code is not None:
            return existing_code

        code = encode(self._next_id)
        self._next_id += 1
        self._url_to_code.put(url, code)
        self._code_to_url.put(code, url)
        return code

    def expand(self, code):
        """Return the original URL for an issued code."""
        if not isinstance(code, str):
            raise ValueError("code must be a string")

        if not code or any(ALPHABET.find(character) < 0 for character in code):
            raise ValueError("invalid base62 code")

        url = self._code_to_url.get(code)
        if url is None:
            raise ValueError(f"unknown code: {code!r}")
        return url
