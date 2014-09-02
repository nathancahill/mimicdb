## MimicDB

[![PyPI](http://img.shields.io/pypi/v/mimicdb.svg?style=flat)](https://pypi.python.org/pypi/mimicdb/)
[![Build Status](http://img.shields.io/travis/nathancahill/mimicdb/master.svg?style=flat)](https://travis-ci.org/nathancahill/mimicdb)
[![Coverage Status](http://img.shields.io/coveralls/nathancahill/mimicdb/master.svg?style=flat)](https://coveralls.io/r/nathancahill/mimicdb)


#### Python Implementation of MimicDB

Python works with the Boto library.

#### Installation

By default, MimicDB requires Redis (although other backends can be used instead).

```
$ pip install redis
$ pip install mimicdb
```

#### Quickstart

If you're using Boto already, replace ```boto``` imports with ```mimicdb``` imports.

Change:
```
from boto.s3.connection import S3Connection
from boto.s3.key import Key
```

To:
```
from mimicdb.s3.connection import S3Connection
from mimicdb.s3.key import Key
```

Additionally, import the MimicDB object itself, and initiate the backend:
```
from mimicdb import MimicDB
MimicDB()
```

After establishing a connection for the first time, sync the connection to save the metadata locally:
```
conn = S3Connection(KEY, SECRET)
conn.sync()
```

Or sync only a couple buckets from the connection:
```
conn.sync('bucket1', 'bucket2')
```

After that, upload, download and list as you usually would. API calls that can be responded to locally will return instantly without hitting S3 servers. API calls that are made to S3 using MimicDB will be mimicked locally to ensure consistency with the remote servers.

Pass ```force=True``` to most functions to force a call to the S3 API. This also updates the local database.

#### Alternate Backends

Besides the default Redis backend, MimicDB has SQLite and in-memory backends available.
```
from mimicdb.backends.sqlite import SQLite
MimicDB(SQLite())
```
```
from mimicdb.backends.memory import Memory
MimicDB(Memory())
```

#### Documentation

[mimicdb.readthedocs.org](http://mimicdb.readthedocs.org)

#### Contributing


1. Fork the repo.
2. Run tests to ensure a clean, working slate.
3. Improve/fix the code.
4. Add test cases if new functionality introduced or bug fixed (100% test coverage).
5. Ensure tests pass.
6. Push to your fork and submit a pull request to the develop branch.

#### Tests

Run tests after installing nose and coverage.

```
$ nosetests --with-coverage --cover-package=mimicdb
```

Integration testing is provided by Travis-CI at [travis-ci.org/nathancahill/mimicdb](https://travis-ci.org/nathancahill/mimicdb)

Test coverage reporting is provided by Coveralls at [coveralls.io/r/nathancahill/mimicdb](https://coveralls.io/r/nathancahill/mimicdb)

#### Benchmarks

Run ```benchmarks.py``` in the root of the repo:

```
$ python benchmarks.py
Boto Time: 0.338411092758
MimicDB Time: 0.00015789039612
Factor: 2143x faster
```

#### License

MimicDB is BSD licensed.
