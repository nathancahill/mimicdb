=======
MimicDB
=======

S3 Metadata without the Latency or Costs

By maintaining a transactional record of every API call to S3, MimicDB provides
a local, isometric key-value store of data on S3. MimicDB stores everything
except the contents of objects locally. Tasks like listing, searching and
calculating storage usage on massive amounts of data are now fast and free.

On average, tasks like these are 2000x faster using MimicDB.

Boto:

    >>> c = S3Connection(KEY, SECRET)
    >>> bucket = c.get_bucket('bucket_name')
    >>> start = time.time()
    >>> bucket.get_all_keys()
    >>> print time.time() - start
    0.425064992905

Boto + MimicDB:

    >>> c = S3Connection(KEY, SECRET)
    >>> bucket = c.get_bucket('bucket_name')
    >>> start = time.time()
    >>> bucket.get_all_keys()
    >>> print time.time() - start
    0.000198841094971

Works with Python and Boto

MimicDB wraps every S3 API call made by boto and mimics the response locally. 
Additionally, if an API call can be fulfilled by MimicDB, it returns instantly 
without hitting the S3 API at all (although the API call can be forced). 
Python (including aws-cli) will be supported at launch, with Ruby support on 
the roadmap.

Built on Redis

All metadata is stored logically in Redis. Object keys and metadata values use
nomenclature that is identical to S3. This allows manually querying the database
and prevents being locked in to another database layer. It also allows the
database to be shared between multiple servers.

Force Synchronization and Key Population

For S3 objects that are updated independently of MimicDB, a complete or partial
synchronization can be forced by providing an iterable of outdated keys. This
keeps S3 API calls to a minimum and doesn't assume consistency.

Fork MimicDB on Github

MimicDB is already being used in production. However, additional testing and
documentation are being completed before launching a stable version.
Contribute to MimicDB on Github, or sign up below for updates.


Installation
=============

To install MimicDB, simply:

    $ pip install mimicdb

MimicDB requires boto.

After installing, change the boto imports from boto.s3.* to mimicdb.s3.*

Additionally, register the database at the begining of the script:

    >>> from mimicdb import MimicDB
    >>> MimicDB(host='localhost', port=6379, db=0)

MimicDB() takes the same parameters as the redis connection the data will be
stored in.
