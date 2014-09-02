from . import Backend


class Memory(Backend):
    """In-Memory backend. A good example for building a custom backend.

    .. code-block:: python

        from mimicdb.backends.memory import Memory

        memory = Memory()
    """
    def __init__(self):
        self._data = dict()

    def keys(self, pattern='*'):
        pattern = pattern.replace('*', '')
        return [key for key in self._data if key.startswith(pattern)]

    def delete(self, *names):
        for name in names:
            self._data.pop(name, None)

    def sadd(self, name, *values):
        if name in self._data:
            self._data[name].update(values)
        else:
            self._data[name] = set(values)

    def srem(self, name, *values):
        if name in self._data:
            self._data[name].difference_update(values)

    def sismember(self, name, value):
        if name in self._data:
            return value in self._data[name]

        return False

    def smembers(self, name):
        return self._data.get(name, [])

    def hmset(self, name, mapping):
        self._data[name] = mapping

    def hgetall(self, name):
        return self._data.get(name, dict())
