


cache = type('cache', (), {})()
cache.host = '0.0.0.0'
cache.port = 3000
cache.role = 'main'
cache.folder = '/dev/shm/simplecache'
# set the cache.maxtime in seconds
# seconds * minutes * hours
cache.maxtime = 60*3*1

server = type('server', (), {})()
server.host =  'localhost'
server.port = 3001




