import config
import threading
import socket

class CacheServer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.name = "Cache Server"

    def run(self):
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
    changed_time = time.time()
    with open(config.cache.folder + filename, 'wb') as f:
        f.write(content)
    with open(config.cache.lastwritten, 'w') as f:
        f.write(changed_time)
    index[filename] = changed_time
