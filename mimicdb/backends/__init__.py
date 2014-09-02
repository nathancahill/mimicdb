class Backend(object):
    """Base class for MimicDB backends. Extendable to support custom backends.
    A custom backend **must** implement each of the functions of the
    base class.

    .. code-block:: python

        from mimicdb.backends import Backend

        class MyAwesomeBackend(Backend):
            def __init__(self):

            etc.
    """
    def __init__(self):
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
