#!/usr/bin/env python3
import logging
import argparse
logging.basicConfig(level=logging.INFO)
from deluge_client import DelugeRPCClient
from delugetools.common import decodedict, GB, DelugeUri
from urllib.parse import urlparse
import sys
from concurrent.futures import ThreadPoolExecutor
from tabulate import tabulate


def cull_unregistered(client):
    """
    Delete torrents with 'Unregistered torrent' error state
    """
    torrents = decodedict(client.call('core.get_torrents_status', {},
                                      ['name', 'tracker_status', 'total_size', 'time_added']))
    tors_deleted = 0
    size_deleted = 0
    for torrent_id, torrent in torrents.items():
        if 'Unregistered torrent' in torrent["tracker_status"]:
            logging.warning("Deleting %s", torrent["name"])
            client.call('core.remove_torrent', torrent_id, True)
            size_deleted += torrent["total_size"]
            tors_deleted += 1
    return (tors_deleted, size_deleted)


def cull_by_diskspace(client, want_free=150 * GB):
    freespace_bytes = decodedict(client.call('core.get_free_space'))

    to_free = want_free - freespace_bytes

    if to_free <= 0:
        logging.info("Already above disk free threshold (%sGB is free), aborting", round(freespace_bytes / GB, 2))
        return (0, 0)

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

    return (deleted_torrents, deleted_bytes)


def main():
    parser = argparse.ArgumentParser(description="Clean up deluge torrents")
    parser.add_argument("-s", "--server", action="append", type=DelugeUri, required=True,
                        help="Deluge host or IP addresses to connect to in the form of user:pass@hostname:port")

    subparser_action = parser.add_subparsers(dest='action', help='action to take')

    parser_unreg = subparser_action.add_parser('unreg', help='Delete torrents with "Unregistered torrent" error state')

    parser_free = subparser_action.add_parser('space', help='Delete oldest torrents to reach a free disk space quota')
    parser_free.add_argument("-f", "--free", help="Target free space in GB", type=int, required=True)

    args = parser.parse_args()

    if not args.action:
        print("No action specified")
        sys.exit(2)

    clients = []
    futures = []
    for server in args.server:
        uri = urlparse('deluge://{}'.format(server))
        client = DelugeRPCClient(uri.hostname, uri.port if uri.port else 58846, uri.username, uri.password)
        client.connect()
        clients.append(client)

    if args.action == "unreg":
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures += [pool.submit(cull_unregistered, c) for c in clients]

    elif args.action == "space":
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures += [pool.submit(cull_by_diskspace, c, want_free=args.free * GB) for c in clients]

    print(tabulate([["{}:{}".format(clients[i].host, clients[i].port),
                     "{} GB".format(round(decodedict(clients[i].call('core.get_free_space')) / GB, 2)),
                     futures[i].result()[0],
                     "{} GB".format(round(futures[i].result()[1] / GB, 2))]
                    for i in range(0, len(clients))],
                   headers=["server", "space free", "rm'd", "newly freed"]))

if __name__ == '__main__':
    main()
