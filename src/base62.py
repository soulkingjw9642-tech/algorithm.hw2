"""Base62 encoding for non-negative integers."""

ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_BASE = len(ALPHABET)


def encode(number: int) -> str:
    """Encode a non-negative integer as a base62 string."""
    if not isinstance(number, int) or isinstance(number, bool):
        raise TypeError("number must be an integer")
    if number < 0:
        raise ValueError("number must be non-negative")
    if number == 0:
        return ALPHABET[0]

    digits = []
    while number:
        number, remainder = divmod(number, _BASE)
        digits.append(ALPHABET[remainder])
    return "".join(reversed(digits))


def decode(value: str) -> int:
    """Decode a base62 string into a non-negative integer."""
    if not isinstance(value, str):
        raise TypeError("value must be a string")
    if not value:
        raise ValueError("value must not be empty")

    number = 0
    for character in value:
        digit = ALPHABET.find(character)
        if digit < 0:
            raise ValueError(f"invalid base62 character: {character!r}") from None
        number = number * _BASE + digit
    return number
