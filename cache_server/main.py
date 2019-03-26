import os
import time
import socket
from urllib.request import Request, urlopen, HTTPError

"""
    Cache proxy

    This 
    https://alexanderell.is/posts/simple-cache-server-in-python/
"""

import config

# Index will keep track of the updated time of each cached file
index = {}

# Create an in memory storage in order to take advantage of the tree structure and performance
try:
    os.mkdir(config.cache.folder)
except FileExistsError:
    pass


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((config.cache.host, int(config.cache.port)))

    s.listen(1)

    print('Cache proxy is listening on port %s ...' % config.cache.port)

    while True:
        # Wait for client connection
        client_connection, client_address = s.accept()
        print("\n\n=====\nNew request:")

        # Get the client request
        request = client_connection.recv(1024).decode()
        print(request)
        if not request:
            continue

        # Parse HTTP headers
        headers = request.split('\n')
        top_header = headers[0].split()
        method = top_header[0]
        filename = top_header[1]

        # Index check
        if filename == '/':
            filename = '/index.html'

        # Get the file
        try:
            content = fetch_file(filename)
        except FileNotFoundError:
            parts = filename.split('/')
            parts = [ii for ii in filename.split('/') if ii]
            n = len(parts)
            print(parts)
            for i in range(len(parts)-1):
                newdir = os.path.join(config.cache.folder, *parts[:i+1])
                print("creating new dir", newdir)
                os.mkdir(newdir)
            content = False
        # If we have the file, return it, otherwise 404
        if content:
            try:
                response = 'HTTP/1.0 200 OK\n\n' + content.decode("utf-8")
                response = response.encode()
                print("   ... utf-8 content")
            except AttributeError:
                response = 'HTTP/1.0 200 OK\n\n' + content
                response = response.encode()
                print("   ... string content")
            except UnicodeDecodeError:
                response = content
                print("   ... binary content")

        else:
            response = b'HTTP/1.0 404 NOT FOUND\n\n File Not Found'
            print("  ... not found")
        # Send the response and close the connection
        client_connection.sendall(response)
        client_connection.close()

    # Close socket
    s.close()


def fetch_file(filename):
    """ Retrieve a file from cache or server

    If a cached version exists and it is newer than now - config.cache.maxtime seconds, use it.
    Otherwise fetch new version from the server.
    """
    file_from_cache = fetch_from_cache(filename)
    if file_from_cache:
        print('   cached')
        if filename not in index:
            print('        invalid cache')
        elif index[filename] > time.time()-config.cache.maxtime:
            print('        valid!')
            return file_from_cache
        else:
            print('         expired.')
            print(index[filename], time.time(), config.cache.maxtime)
    else:
        print('Not in cache. Fetching from server.')
    file_from_server = fetch_from_server(filename)
    if file_from_server:
        save_in_cache(filename, file_from_server)
        return file_from_server
    else:
        return None


def fetch_from_cache(filename):
    try:
        print("checking to see if "+filename+" is in cache")
        # Check if we have this file locally
        fin = open(config.cache.folder + filename, 'rb')
        content = fin.read()
        fin.close()
        # If we have it, let's send it
        return content
    except IOError:
        return None


def fetch_from_server(filename):
    url = 'http://{}:{}{}'.format(config.server.host, config.server.port, filename)
    print(url)
    q = Request(url)
    try:
        response = urlopen(q)
        # Grab the header and content from the server req
        response_headers = response.info()
        print(response)
        content = response.read()
        return content
    except HTTPError:
        return None


def save_in_cache(filename, content):
    print('Saving a copy of {} in the cache'.format(filename))
    cached_file = open(config.cache.folder + filename, 'wb')
    cached_file.write(content)
    cached_file.close()
    index[filename] = time.time()
    

if __name__ == '__main__':
    main()
