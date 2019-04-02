import os
import time
import socket
import ipaddress
import base64
import cache_server
import sync_server

from urllib.request import Request, urlopen, HTTPError

"""
    Cache proxy

    Original concept from: https://alexanderell.is/posts/simple-cache-server-in-python/
"""

import config

"""
 Create necessary folders 
  Create an in memory storage in order to take advantage of the tree structure and performance
"""
try:
    os.mkdir(config.cache.folder)
    os.mkdir(config.cache.queue_folder)
except FileExistsError:
    pass


def setup():
    """ Create an unique id for this server and persist it."""
    print("... Set up ")
    try:
        id = open('resources/id', 'r').readline()[:-1]
    except (FileNotFoundError, IndexError):
        id = base64.b64encode(os.urandom(32))
        with open('resources/id', 'wb') as idfile:
            idfile.write(id)
    config.cache.id = id
    print("   cache server: "+str(id))



# Index will keep track of the updated time of each cached file
index = {}
known_indexes = []

servers = {}


def main():
    """ Start the cache and the sync servers

    The cache server will listen to requests, check if they are stored and answer them.
    The sync server will listen to cache updates from other cache servers and brodcast updates to this
    """
    cache = cache_server.CacheServer()
    cache.start()
    sync = sync_server.SyncServer()
    sync.start()
    cache.join()
    sync.join()

if __name__ == '__main__':
    setup()
    main()
