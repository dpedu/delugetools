import argparse
import re
import bencodepy

GB = 1024 * 1024 * 1024


def decodedict(thing):
    """
    Recursively converts bytestrings to unicode
    """
    if type(thing) not in [list, dict, tuple]:
        if type(thing) == bytes:
            try:
                thing = thing.decode('utf-8')
            except:
                pass
        return thing
    elif isinstance(thing, list):
        return [decodedict(i) for i in thing]
    elif isinstance(thing, tuple):
        return tuple(decodedict(i) for i in thing)
    else:
        return dict((k.decode('utf-8'), decodedict(v))
                    for k, v in thing.items())


def DelugeUri(v):
    try:
        return re.match(r'(([^:]+):([^@]+)@([^:$]+)(:([0-9]+))?)', v).group(0)
    except:
        raise argparse.ArgumentTypeError("String '{}' does not match required format".format(v))


def parse_torrent(f_path):
    return bencodepy.decode_from_file(f_path)
