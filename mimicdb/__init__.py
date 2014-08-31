from redis import StrictRedis
from .s3 import tpl

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
        if kwargs and 'namespace' in kwargs:
            tpl.set_namespace(kwargs.pop('namespace'))

        globals()['redis'] = StrictRedis(*args, **kwargs)
