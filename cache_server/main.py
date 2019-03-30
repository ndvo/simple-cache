import os
import time
import socket
import ipaddress
import base64

from urllib.request import Request, urlopen, HTTPError

"""
    Cache proxy

    Original concept from: https://alexanderell.is/posts/simple-cache-server-in-python/
"""

import config


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
    config.cache.ip = get_ip()
    print("   cache ip = "+str(config.cache.ip))
    config.cache.country, config.cache.countrycode= ip2country(config.cache.ip)
    print("country ", config.cache.country or "country empty", config.cache.countrycode or "countrycode empty")



# Index will keep track of the updated time of each cached file
index = {}
known_indexes = []

servers = {}

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
        print("\n\n=====\nNew request from : "+str(client_address))
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


def register_cache_server(request):
    #TODO: register the cache servers
    pass

def share_data():
    #TODO when new data is save, broadcast it to other servers
    # Send hashed string of the index and the new data
    pass

def update_data():
    #TODO: when new data is received from other servers
    # check the hash, if different create a copy, add the new item and check the hash
    # if match, save it
    pass


def announce_new_server():
    #TODO: announce the new server to all others
    # when a new server is registered, annouce it's presence to all others
    my_ip = get_ip()
    for k,v in servers.items():
        s = socket.socket()
        s.bind((v.address, v.port))
        s.sendall(config.cache)



    pass

def replace_main_server():
    #TODO: if the main server is down, replace it
    #if 'main' not in servers:
    # loop through all servers voting on the server with more votes to be accepted as main server
    # log votes to be main server from other servers
    # If there is a tie, vote for the first.
    # If I am one of the tied, vote for me. 
    pass

def get_ip():
    """Returns the IP address of the current instance
    Public domain code from Jamieson Becker: https://stackoverflow.com/a/28950776/935645
    """
    if config.fakeip:
        return config.fakeip
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP
   
def ip2country(ip):
    iprange = ".".join(ip.split(".")[:-1])
    countrycode = None
    country = None
    with open(config.geoip.path, "r") as countryblocks:
        for line in countryblocks:
            if ( line.startswith(iprange)):
                line_data = line.split(',')
                if ipaddress.ip_address(ip) in ipaddress.ip_network(line_data[0]):
                    countrycode = line_data[2]
    if countrycode:
        with open(config.geoip.countries_path, "r") as countries:
            for line in countries:
                print(line, countrycode)
                if ( line.startswith(countrycode)):
                    line_data = line.split(',')
                    if (countrycode == line_data[0]):
                        country = line_data[4]
    return country, countrycode


        



if __name__ == '__main__':
    setup()
    main()
