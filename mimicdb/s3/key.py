from boto.s3.key import Key as boto_Key

import mimicdb


class Key(boto_Key):
    def __init__(self, *args, **kwargs):
        """
        Adds an attribute 'base' for key metadata. Stores the key in the bucket
        if the key name is already set, otherwise nothing is stored.
        """
        self.base = '%(bucket)s:%(key)s'
        self.bucket = kwargs.get('bucket', args[0] if args else None)
        self.name = kwargs.get('name', args[1] if len(args) > 1 else None)

        if self.name and self.bucket:
            mimicdb.redis.sadd(self.bucket.name, self.name)

        super(Key, self).__init__(*args, **kwargs)


    def _get_key(self):
        return super(Key, self).name


    def _set_key(self, *args, **kwargs):
        value = kwargs.get('value', args[0])

        mimicdb.redis.sadd(self.bucket.name, value)

        return super(Key, self)._set_key(*args, **kwargs)


    key = property(_get_key, _set_key)


    def _send_file_internal(self, *args, **kwargs):
        """
        Saves the file size when the key contents are set using:
         - set_contents_from_file
         - set_contents_from_filename
         - set_contents_from_string
        """
        key_size = super(Key, self)._send_file_internal(*args, **kwargs)
        mimicdb.redis.set((self.base + ':size') % dict(bucket=self.bucket.name, key=self.name), key_size)
        return key_size
