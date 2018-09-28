from flask import request, render_template, Blueprint, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, ALLOWED_EXTENSIONS
import db
from accountController import validate_login
from urllib.parse import quote_plus
import os


from os import listdir
from os.path import isfile, join
from bs4 import BeautifulSoup
import requests
import json
from collections import OrderedDict
from requests import Session
from requests.auth import HTTPBasicAuth

import xml.etree.ElementTree as ET
import jinja2

mod_main = Blueprint('main',__name__)

@mod_main.route('/',methods=['GET','POST'])
def index():
  
  return render_template('index.tpl.html',messages=errores,ultima_act=uact)
