from redis import StrictRedis

class MimicDB(object):
    def __init__(self, *args, **kwargs):
        """
        Initialze the MimicDB object by passing the Redis connection parameters:

        :host='localhost'
        :port=6379
        :db=0

        The Redis connection is accessed elsewhere in the module by importing
        mimicdb, then calling mimicdb.redis
        """
        globals()['redis'] = StrictRedis(*args, **kwargs)
