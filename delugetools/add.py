#!/usr/bin/env python3
import logging
import argparse
logging.basicConfig(level=logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Add torrents to one or more deluge instances")

    args = parser.parse_args()
    print(args)
    return

    """
    @TODO
    - accept a list of deluge servers in arguments
    - accept list of .torrent files in arguments
    - add the torrents balanced across all servers in some balanced way
    - optional: min disk space flag (adds skipped if >=)
    """

if __name__ == '__main__':
    main()

