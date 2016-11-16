#!/usr/bin/env python3
import logging
import argparse
logging.basicConfig(level=logging.INFO)
from deluge_client import DelugeRPCClient
from delugetools.common import decodedict, GB
from urllib.parse import urlparse
import sys
import re
from concurrent.futures import ThreadPoolExecutor

def cull_unregistered(client):
    """
    Delete torrents with 'Unregistered torrent' error state
    """
    torrents = decodedict(client.call('core.get_torrents_status', {},
                                      ['name', 'tracker_status', 'total_size', 'time_added']))
    for torrent_id, torrent in torrents.items():
        if 'Unregistered torrent' in torrent["tracker_status"]:
            logging.warning("Deleting %s", torrent["name"])
            client.call('core.remove_torrent', torrent_id, True)


def cull_by_diskspace(client, want_free=150 * GB):
    freespace_bytes = decodedict(client.call('core.get_free_space'))

    to_free = want_free - freespace_bytes

    if to_free <= 0:
        logging.info("Already above disk free threshold (%sGB is free), aborting", round(freespace_bytes / GB, 2))
        return

    logging.warning("Need to delete %sGB of torrents", round(to_free / GB, 2))

    torrents = decodedict(client.call('core.get_torrents_status', {},
                                      ['name', 'hash', 'tracker_status', 'total_size', 'time_added']))

    # list of torrents, oldest to newest
    torrents = sorted([v for k, v in torrents.items()], key=lambda x: x["time_added"])

    deleted_bytes = 0
    deleted_torrents = 0

    while to_free > 0:
        victim = torrents.pop(0)

        to_free -= victim["total_size"]
        deleted_bytes += victim["total_size"]
        deleted_torrents += 1

        logging.warning("Deleting {} added {}".format(victim["name"], victim["time_added"]))
        client.call('core.remove_torrent', victim['hash'], True)
        logging.warning("Still need to free: {}GB".format(round(to_free / GB, 2)))

    logging.warning("Deleted %s torrents freeing %s GB", deleted_torrents, round(deleted_bytes / GB, 2))


def DelugeUri(v):
    try:
        return re.match(r'(([^:]+):([^@]+)@([^:$]+)(:([0-9]+))?)', v).group(0)
    except:
        raise argparse.ArgumentTypeError("String '{}' does not match required format".format(v))


def main():
    parser = argparse.ArgumentParser(description="Clean up deluge torrents")
    parser.add_argument("-s", "--server", action="append", type=DelugeUri, required=True,
                        help="Deluge host or IP addresses to connect to in the form of user:pass@hostname:port")

    subparser_action = parser.add_subparsers(dest='action', help='action to take')

    parser_unreg = subparser_action.add_parser('unreg', help='Delete torrents with "Unregistered torrent" error state')

    parser_free = subparser_action.add_parser('space', help='Delete oldest torrents to reach a free disk space quota')
    parser_free.add_argument("-f", "--free", help="Target free space in GB", type=int, required=True)

    args = parser.parse_args()
    print(args)

    if not args.action:
        print("No action specified")
        sys.exit(2)

    clients = []
    for server in args.server:
        uri = urlparse('deluge://{}'.format(server))
        client = DelugeRPCClient(uri.hostname, uri.port if uri.port else 58846, uri.username, uri.password)
        client.connect()
        clients.append(client)

    if args.action == "unreg":
        with ThreadPoolExecutor(max_workers=10) as pool:
            #pool.map(cull_unregistered, clients)
            for client in clients:
                print(client)
                pool.submit(cull_unregistered, client)

    elif args.action == "space":
        with ThreadPoolExecutor(max_workers=10) as pool:
            for client in clients:
                print(client)
                pool.submit(cull_by_diskspace, client, want_free=args.free * GB)


if __name__ == '__main__':
    main()
