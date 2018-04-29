#!/usr/bin/env python3
import logging
import argparse
logging.basicConfig(level=logging.INFO)
from deluge_client import DelugeRPCClient
from delugetools.common import decodedict, DelugeUri
from urllib.parse import urlparse


def main():
    parser = argparse.ArgumentParser(description="Change torrent trackers")
    parser.add_argument("-s", "--server", type=DelugeUri, required=True,
                        help="Deluge host or IP addresses to connect to in the form of user:pass@hostname:port")

    parser.add_argument("-c", "--src-substr", help="Tracker to replace", required=True)
    parser.add_argument("-t", "--tracker", help="URL of new tracker", required=True)
    parser.add_argument("-n", "--dry-run", action="store_true", help="Only print changed torrents")

    args = parser.parse_args()

    uri = urlparse('deluge://{}'.format(args.server))
    client = DelugeRPCClient(uri.hostname, uri.port if uri.port else 58846, uri.username, uri.password)
    client.connect()

    torrents = decodedict(client.call('core.get_torrents_status', {},
                                      ['name', 'trackers']))
    for torrent_id, torrent in torrents.items():
        tracker = torrent['trackers'][0]
        if args.src_substr in tracker["url"]:
            print("Updating '{}' on '{}' ({})".format(tracker["url"], torrent['name'], torrent_id))
            if not args.dry_run:
                client.call('core.set_torrent_trackers', torrent_id, [{"url": args.tracker, "tier": 0}])
