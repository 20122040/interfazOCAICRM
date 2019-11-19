from __future__ import division,print_function,unicode_literals
from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus
#import flask_excel as excel
import bcrypt

UPLOAD_FOLDER = 'uploaded_files'
UPLOAD_FOLDER_LIMA = 'uploaded_files_lima'
UPLOAD_FOLDER_PROVINCIA = 'uploaded_files_provincia'
UPLOAD_FOLDER_CONVERTIR = 'uploaded_files_convertir'
DATABASE_PATH = 'database.db'

#UPLOAD_FOLDER = '/var/www/herramientas-ocai/interfazOCAICRM/uploaded_files'
#UPLOAD_FOLDER_LIMA = '/var/www/herramientas-ocai/interfazOCAICRM/uploaded_files_lima'
#UPLOAD_FOLDER_PROVINCIA = '/var/www/herramientas-ocai/interfazOCAICRM/uploaded_files_provincia'
#UPLOAD_FOLDER_CONVERTIR = '/var/www/herramientas-ocai/interfazOCAICRM/uploaded_files_convertir'

ALLOWED_EXTENSIONS = set(['xls','xlsx','csv'])

app = Flask(__name__)
#excel.init_excel(app)
app.config['DEBUG'] = True
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://asistencia:NGsg9iKG9VBwQDO@127.0.0.1/asistenciaControladores'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:admin@localhost:3306/evaluacionControlador'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:admin@localhost:5432/evaluacionControlador'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['DB_PATH'] = DATABASE_PATH
app.config['SECRET_KEY'] = 'W31zXmCNBX3LGonY'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_FOLDER_LIMA'] = UPLOAD_FOLDER_LIMA
app.config['UPLOAD_FOLDER_PROVINCIA'] = UPLOAD_FOLDER_PROVINCIA
app.config['UPLOAD_FOLDER_CONVERTIR'] = UPLOAD_FOLDER_CONVERTIR
app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)
#db = SQLAlchemy(app)

from controllers.mainController import mod_main as main_module
from accountController import mod_account
from db import get_db

app.register_blueprint(main_module)
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
