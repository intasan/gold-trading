from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import json, sqlite3
from .sources import validate

ROOT=Path(__file__).resolve().parents[1]
FIELDS=['source','series','frequency','observed_at','value','unit','retrieved_at','raw_sha256']

class Store:
    def __init__(self, url='data/gold.db'):
        self.postgres=url.startswith(('postgresql://','postgres://'))
        if self.postgres:
            import psycopg
            from psycopg.rows import dict_row
            self.conn=psycopg.connect(url,row_factory=dict_row)
        else:
            path=url.removeprefix('sqlite:///')
            if path!=':memory:': Path(path).parent.mkdir(parents=True,exist_ok=True)
            self.conn=sqlite3.connect(path)
            self.conn.row_factory=sqlite3.Row
            self.conn.execute('PRAGMA foreign_keys=ON')
            self.conn.execute('PRAGMA busy_timeout=5000')
        for statement in (ROOT/'sql/schema.sql').read_text().split(';'):
            if statement.strip(): self.execute(statement)
        self.conn.commit()

    def execute(self,sql,args=()):
        return self.conn.execute(sql.replace('?','%s') if self.postgres else sql,args)

    def query(self,sql,args=()): return [dict(x) for x in self.execute(sql,args).fetchall()]

    @contextmanager
    def transaction(self):
        try:
            yield
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise

    def upsert(self, rows):
        keys=set()
        for row in rows:
            validate(row)
            key=(row.source,row.series,row.frequency,row.observed_at)
            if key in keys: raise ValueError('Duplicate observation key in source batch')
            keys.add(key)
        if not rows: raise ValueError('No valid rows')
        inserted=0
        for row in rows:
            values=asdict(row)
            key=tuple(values[f] for f in FIELDS[:4])
            exists=self.execute('SELECT 1 FROM observations WHERE source=? AND series=? AND frequency=? AND observed_at=?',key).fetchone()
            inserted+=int(exists is None)
            self.execute('INSERT INTO observations('+','.join(FIELDS)+') VALUES('+','.join('?' for _ in FIELDS)+') ON CONFLICT(source,series,frequency,observed_at) DO UPDATE SET value=excluded.value,unit=excluded.unit,retrieved_at=excluded.retrieved_at,raw_sha256=excluded.raw_sha256',tuple(values[f] for f in FIELDS))
        return inserted,len(rows)-inserted

    def close(self): self.conn.close()
