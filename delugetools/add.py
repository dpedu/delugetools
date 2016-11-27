#!/usr/bin/env python3
import logging
import argparse
logging.basicConfig(level=logging.INFO)
from delugetools.common import DelugeUri, decodedict, parse_torrent, GB
from deluge_client import DelugeRPCClient
from urllib.parse import urlparse
from hashlib import md5
from concurrent.futures import ThreadPoolExecutor
from tabulate import tabulate
import os
from base64 import b64encode
from collections import defaultdict


def add_torrent(client, torrent_path):
    logging.info("adding to %s:%s - %s", str(client.host), str(client.port), os.path.basename(torrent_path))
    with open(torrent_path, 'rb') as f:
        b64_contents = b64encode(f.read())
        torrent_id = decodedict(client.call('core.add_torrent_file', os.path.basename(torrent_path), b64_contents,
                                {"paused": False}))
        if not torrent_id:
            logging.info("%s was a dupe", str(torrent_path))
            return (client, 0, None)
        t_info = decodedict(client.call('core.get_torrent_status', torrent_id, ["name", "total_size"]))
        return (client, t_info["total_size"], t_info["name"])


def main():
    parser = argparse.ArgumentParser(description="Add torrents to one or more deluge instances")
    parser.add_argument("-s", "--server", action="append", type=DelugeUri, required=True,
                        help="Deluge host or IP addresses to connect to in the form of user:pass@hostname:port")
    parser.add_argument("torrents", nargs="+", help="torrent files to add")
    args = parser.parse_args()

    clients = []
    futures = []
    for server in args.server:
        uri = urlparse('deluge://{}'.format(server))
        client = DelugeRPCClient(uri.hostname, uri.port if uri.port else 58846, uri.username, uri.password)
        client.connect()
        clients.append(client)

    with ThreadPoolExecutor(max_workers=1) as pool:
        for torrent_path in args.torrents:
            t_data = parse_torrent(torrent_path)

            namehash = md5()
            t_name = t_data[b'info'][b'name']

            namehash.update(t_name)

            torrent_host = int(namehash.hexdigest(), 16) % len(args.server)
            futures += [pool.submit(add_torrent, clients[torrent_host], torrent_path)]

    added_by_host = defaultdict(list)

    for future in futures:
        client, size, name = future.result()
        if name:
            client_id = "{}:{}".format(client.host, client.port)
            added_by_host[client_id].append(size)

    added_by_host = dict(added_by_host)

    print(tabulate([(host,
                     len(added), round(sum(added) / GB, 2))
                    for host, added in added_by_host.items()],
                   ["host", "added", "size (gb)"]))


if __name__ == '__main__':
    main()

