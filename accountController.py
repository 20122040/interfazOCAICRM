from flask import request, render_template, Blueprint, redirect, url_for, escape
import bcrypt
from app import app
from db import query_db

mod_account = Blueprint('account',__name__) 

@mod_account.route('/login',methods=['GET','POST'])
def login():
  if request.method == 'GET':
    return render_template('login.tpl.html')
  else:
    destination = request.args.get('dest', '/')
    username = request.form['username']
    password = request.form['password']

    user = query_db('SELECT * FROM account WHERE username = ?',[username],one=True)

    if user is not None:
      userSecret =(password + app.config['SECRET_KEY']).encode('utf-8')
      if bcrypt.checkpw(userSecret,user['password'].encode('utf-8')): 
        resp = redirect(destination)
        hashed = bcrypt.hashpw((username+ app.config['SECRET_KEY']).encode('utf-8'),bcrypt.gensalt())
        resp.set_cookie('username',username+'|'+ hashed.decode('utf-8'))
        return resp
    return render_template('login.tpl.html',messages=['El usuario y/o la contraseña son incorrectos'])

def validate_login(request):
  username_cookie = request.cookies.get('username')
  if (username_cookie is None) or (username_cookie == ''):
    return False
  
  userAndHash = username_cookie.split('|')
  if len(userAndHash) != 2:
    return False

  if not bcrypt.checkpw((userAndHash[0]+ app.config['SECRET_KEY']).encode('utf-8'),userAndHash[1].encode('utf-8')):
    return False

  return True

@mod_account.route('/logout',methods=['GET'])
def logout():
  resp = redirect('/login')
  resp.set_cookie('username','')
  return resp