"""Base class for MimicDB backends
"""

class Backend(object):
    def __init__(self, *args, **kwargs):
        pass

    def delete(self, *names):
        pass

    def sadd(self, name, *values):
        pass

    def srem(self, name, *values):
        pass

    def sismember(self, name, value):
        pass

    def smembers(self, name):
        pass

    def hmset(self, name, mapping):
        pass

    def hgetall(self, name):
        pass
