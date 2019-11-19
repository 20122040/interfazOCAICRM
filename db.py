import sqlite3
from app import app
from flask import g

def get_db():
  db = getattr(g,'_database',None)
  if db is None:
    db = g._database = sqlite3.connect(app.config['DB_PATH'])
    db.row_factory = sqlite3.Row
  return db

@app.teardown_appcontext
def close_connection(exception):
  db = getattr(g,'_database',None)
  if db is not None:
    db.close()

def query_db(query,args=(),one=False):
  cur = get_db().execute(query,args)
  rv = cur.fetchall()
  cur.close()
  return (rv[0] if rv else None) if one else rv