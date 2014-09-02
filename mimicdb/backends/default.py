
from redis import StrictRedis

from . import Backend


class Redis(Backend):
    """Default backend for MimicDB. Initiated with identical parameters
    as ``redis.StrictRedis``.

    :param args \*args, \**kwargs: StrictRedis.__init__() parameters

    .. code-block:: python

        from mimicdb.backends.default import Redis

        redis = Redis(host='localhost', port=6379, db=0)
    """
    def __init__(self, *args, **kwargs):
        self._redis = StrictRedis(*args, **kwargs)

    def keys(self, pattern='*'):
        return self._redis.keys(pattern)

    def delete(self, *names):
        return self._redis.delete(*names)

    def sadd(self, name, *values):
        return self._redis.sadd(name, *values)

    def srem(self, name, *values):
        return self._redis.srem(name, *values)

    def sismember(self, name, value):
        return self._redis.sismember(name, value)

    def smembers(self, name):
        return self._redis.smembers(name)

    def hmset(self, name, mapping):
        return self._redis.hmset(name, mapping)

    def hgetall(self, name):
        return self._redis.hgetall(name)
