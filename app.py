from __future__ import division,print_function,unicode_literals
from flask import Flask
#from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus
#import flask_excel as excel

UPLOAD_FOLDER = 'uploaded_files'
#UPLOAD_FOLDER = '/var/www/herramientas-ocai/interfazOCAICRM/uploaded_files'
ALLOWED_EXTENSIONS = set(['xls','xlsx','csv'])

app = Flask(__name__)
#excel.init_excel(app)
app.config['DEBUG'] = True
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://asistencia:NGsg9iKG9VBwQDO@127.0.0.1/asistenciaControladores'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:admin@localhost:3306/evaluacionControlador'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:admin@localhost:5432/evaluacionControlador'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SECRET_KEY'] = 'W31zXmCNBX3LGonY'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)
#db = SQLAlchemy(app)

from controllers.mainController import mod_main as main_module

app.register_blueprint(main_module)
