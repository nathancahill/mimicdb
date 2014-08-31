### MimicDB: An Isomorphic Key-Value Store for S3

#### S3 Metadata without the Latency or Costs

MimicDB is a local database of the metadata of objects stored on S3. Many tasks like listing, searching keys and calculating storage usage can be completely handled locally, without the latency or costs of calling the S3 API.

On average, tasks like these are __2000x__ faster using MimicDB.

__Boto__
```python
>>> c = S3Connection(KEY, SECRET)
>>> bucket = c.get_bucket('bucket_name')
>>> start = time.time()
>>> bucket.get_all_keys()
>>> print time.time() - start
0.425064992905
```

__Boto + MimicDB__
```python
>>> c = S3Connection(KEY, SECRET)
>>> bucket = c.get_bucket('bucket_name')
>>> start = time.time()
>>> bucket.get_all_keys()
>>> print time.time() - start
0.000198841094971 
```

#### Key Value Store

MimicDB uses a Redis backend to stored S3 metadata. Data is stored in the following layout.

`mimicdb` A set of buckets

`mimicdb:bucket` A set of keys

`mimicdb:bucket:key` A hash of key metadata (size and MD5)

The `mimicdb` prefix can additionally use an optional `namespace` string, which allows multiple S3 connections to share the same backend. In that case, the layout looks like this:

`mimicdb:namespace`

`mimicdb:namespace:bucket`

`mimicdb:namespace:bucket:key`

#### Implementation

MimicDB is currently implemented in Python via Boto. If you're using Boto already, the MimicDB Python library works as a drop in replacement.
