connection = 'mimicdb'
bucket = 'mimicdb:%s'
key = 'mimicdb:%s:%s'

def set_namespace(namespace=None):
    if namespace:
        globals()['connection'] = 'mimicdb:' + namespace
        globals()['bucket'] = 'mimicdb:' + namespace + ':%s'
        globals()['key'] = 'mimicdb:' + namespace + ':%s:%s'
