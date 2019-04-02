import os
import config
import socket


import threading

couldnt_read_lastwritten = "... couldn't read lastwritten"

class SyncServer(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.name = "Sync Server"
        print("Starting "+self.name)
        config.cache.ip = get_ip()
        print("   cache ip = "+str(config.cache.ip))
        config.cache.country, config.cache.countrycode= ip2country(config.cache.ip)
        print("   country ", config.cache.country or "country empty", config.cache.countrycode or "countrycode empty")

    def run(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((config.cache.host, int(config.cache.sync_port)))
        s.listen(1)
        print('Cache sync is listening on port %s ...' % config.cache.sync_port)
        while True:
            queue = os.listdir(config.cache.queue_folder)
            if len(queue):
                share_data(queue)
            client_connection, client_address = s.accept()
            print("\n\n=====\nNew update from : "+str(client_address))
            # Get the client request
            request = client_connection.recv(1024).decode()
            if not request:
                continue
            update_data(request)



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
    country = None
    countrycode = None
    if (not os.path.isfile(config.geoip.path)):
        return country, countrycode
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

def register_cache_server(request):
    #TODO: register the cache servers
    pass

def share_data(files_to_send):
    for i in files_to_send:
        #TODO when new data is save, broadcast it to other servers
        # Send hashed string of the index and the new data
        print("broadcasting {}".format(i))
        os.remove(i)

def update_data(files_to_update):
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
