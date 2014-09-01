
import sqlite3

from . import Backend


class SQLite(Backend):
    def __init__(self, *args, **kwargs):
        if not args and not kwargs:
            args = [':memory:']

        self._sqlite = sqlite3.connect(*args, **kwargs)

    def keys(self, pattern='*'):
        c = self._sqlite.cursor()
        pattern = pattern.replace('*', '%')
        c.execute('SELECT name FROM sqlite_master WHERE type="%s" AND name LIKE "%s"' % ('table', pattern))

        return [row[0] for row in c.fetchall()]

    def delete(self, *names):
        c = self._sqlite.cursor()

        for name in names:
            c.execute('DROP TABLE IF EXISTS "%s"' % (name,))

        self._sqlite.commit()

    def sadd(self, name, *values):
        c = self._sqlite.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS "%s" (member text)' % (name,))

        for value in values:
            c.execute('INSERT INTO "%s" VALUES ("%s")' % (name, value))

        self._sqlite.commit()

    def srem(self, name, *values):
        c = self._sqlite.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS "%s" (member text)' % (name,))

        for value in values:
            c.execute('DELETE FROM "%s" WHERE member="%s"' % (name, value))

        self._sqlite.commit()

    def sismember(self, name, value):
        c = self._sqlite.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS "%s" (member text)' % (name,))
        c.execute('SELECT * FROM "%s" WHERE member="%s"' % (name, value))

        return c.fetchone() != None

    def smembers(self, name):
        c = self._sqlite.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS "%s" (member text)' % (name,))
        c.execute('SELECT * FROM "%s"' % (name,))

        return [row[0] for row in c.fetchall()]

    def hmset(self, name, mapping):
        c = self._sqlite.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS "%s" (size text, md5 text)' % (name,))
        c.execute('INSERT INTO "%s" VALUES ("%s", "%s")' % (name, mapping['size'], mapping['md5']))

        self._sqlite.commit()

    def hgetall(self, name):
        c = self._sqlite.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS "%s" (size text, md5 text)' % (name,))
        c.execute('SELECT * FROM "%s"' % (name,))

        row = c.fetchone()

        if row:
            return dict(size=row[0], md5=row[1])

        return dict()
