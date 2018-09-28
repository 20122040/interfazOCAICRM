from flask import Flask
from urllib.parse import quote_plus
import bcrypt

UPLOAD_FOLDER = 'uploaded_files'
DATABASE_PATH = 'database.db'
LOGS_FOLDER = 'static/logs'
XML_TEMPLATES_PATH = 'xml_templates'
ALLOWED_EXTENSIONS = set(['xls','xlsx'])

app = Flask(__name__)
app.config['DEBUG'] = True
app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = 'W31zXmCNBX3LGonY'
app.config['DB_PATH'] = DATABASE_PATH
app.config['XML_TEMPLATES_PATH'] = XML_TEMPLATES_PATH
app.config['LOGS_FOLDER'] = LOGS_FOLDER
#app.config['ENV'] = 'test'
app.config['ENV'] = 'prod'

from mainController import mod_main
from accountController import mod_account
from db import get_db

app.register_blueprint(mod_main)
app.register_blueprint(mod_account)

def init_db():
  with app.app_context():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
      db.cursor().executescript(f.read())
    db.commit()
  create_user('administrador','ocaipucp')

def create_user(username,password):
  hashed_pw = bcrypt.hashpw((password + app.config['SECRET_KEY']).encode('utf-8'),bcrypt.gensalt()).decode('utf-8')
  with app.app_context():
    cur = get_db()
    cur.execute('INSERT INTO account values (?,?);',[username,hashed_pw])
    cur.commit()

def update_password(username,password):
  hashed_pw = bcrypt.hashpw((password + app.config['SECRET_KEY']).encode('utf-8'),bcrypt.gensalt()).decode('utf-8')
  with app.app_context():
    cur = get_db()
    cur.execute('UPDATE account set password = ? WHERE username = ?;',[hashed_pw,username])
    cur.commit()
