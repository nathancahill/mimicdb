"""Python implementation of MimicDB
"""


class MimicDB(object):
    def __init__(self, backend=None, namespace=None):
        """Initialze the MimicDB backend with an optional namespace.
        """
        if not backend:
            from .backends.default import Redis
            backend = Redis()

        globals()['backend'] = backend

        if namespace:
            from .backends import tpl
            tpl.set_namespace(namespace)
