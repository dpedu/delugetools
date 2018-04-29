delugetools
==========

Some scripts for managing multiple deluge instances.


*deluge-cull*

Delete oldest torrents until free space threshold (in GB) is met:

`deluge-cull space --free 150`

Delete all torrents with "Unregistered torrent" error status:

`deluge-cull unreg`


*deluge-add*

Add torrents in a balanced way across one or more deluge hosts:

`deluge-add -s <server> [-s <server> ...] <torrent> [<torrent> ...]`


*deluge-changetrack*

Change the tracker for torrents in bulk. Torrents who's current primary tracker contains `<substring>` will be updated.

`deluge-changetrack -s <server> -c <substring> -t <new_tracker_url>`
