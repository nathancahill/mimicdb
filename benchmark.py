import os
import time

from boto.s3.connection import S3Connection as BotoS3Connection

from mimicdb import MimicDB
from mimicdb.s3.connection import S3Connection as MimicS3Connection

MimicDB()

AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

boto_conn = BotoS3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
mimic_conn = MimicS3Connection(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
mimic_conn.sync()

boto_bucket = boto_conn.get_bucket('mimicdb-benchmark')
mimic_bucket = mimic_conn.get_bucket('mimicdb-benchmark')

start = time.time()
list(boto_bucket.list())
boto_time = time.time() - start

start = time.time()
list(mimic_bucket.list())
mimic_time = time.time() - start

print 'Boto Time: ' + str(boto_time)
print 'MimicDB Time: ' + str(mimic_time)
print 'Factor: ' + str(int(boto_time / mimic_time)) + 'x faster'
