

# cache.id will be automatically generated
cache = type('cache', (), {})()
cache.host = '0.0.0.0'
cache.port = 3000
cache.role = 'secondary'
cache.folder = '/dev/shm/simplecache'
# set the cache.maxtime in seconds
# seconds * minutes * hours
cache.maxtime = 60*3*1

server = type('server', (), {})()
server.host =  'localhost'
server.port = 3001

geoip = type('geoip', (), {})()
geoip.path = "resources/GeoLite2-Country-CSV_20190326/GeoLite2-Country-Blocks-IPv4.csv"
geoip.countries_path = "resources/GeoLite2-Country-CSV_20190326/GeoLite2-Country-Locations-en.csv"


fakeip = "2.18.67.32"
