import os
from binascii import hexlify


__all__ = ['random', 'armored_random',
    'new_user_key', 'new_salt', 'new_secret']

SECURE = os.getenv('ASSNET_FAST_TEST') != '1'


def random(n):
    """
    Get random bytes.
    Try to use the best random source or fall back to os.urandom.
    """
    source = "/dev/random" if SECURE else "/dev/urandom"
    try:
        with open(source, "r") as randomfd:
            bs = b""
            while n > len(bs):
                bs += randomfd.read(n - len(bs))
            return bs
    except (OSError, IOError):
        return os.urandom(n)


def armored_random(n):
    """
    Get a random string with no special characters.
    n is the number of source bytes, not the final string length.
    """
    return hexlify(random(n))


def new_user_key():
    return armored_random(16)


def new_salt():
    return armored_random(42)


def new_secret():
    """
    Replacement for hexlify(paste.auth.cookie.new_secret())
    Must return a string of 128.
    """
    return armored_random(64)
