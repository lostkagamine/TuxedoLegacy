import rethinkdb
import sys

print('== Rethink Watcher v1.0 ==')
print('by ry00001')

setup = "default"

db = "tuxedo"
table = "projects"

cfg = {} # insert details here. keys= user, password, host, port

conn = None

try:
    if setup == "default":
        conn = rethinkdb.connect(db=db)
    else:
        conn = rethinkdb.connect(username=cfg['user'], password=cfg['password'], host=cfg['host'], port=cfg['port'], db=db)
    print('Connected to RethinkDB')
except Exception as e:
    print(f'Oops, we had problems connecting. Details:\n{type(e).__name__}: {e}')

print('Starting watcher')
print('Details will be displayed below.')
feed = rethinkdb.table(table).changes().run(conn)
for change in feed:
    print(change)

