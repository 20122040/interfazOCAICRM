from flask import request, render_template, Blueprint, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, ALLOWED_EXTENSIONS
from urllib.parse import quote_plus
import os

import math
import pandas as pd
from pandas import Series
import datetime
import time

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

def getColegios():
  r=requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"organization_name,custom_8","contact_sub_type":["Colegio_Lima","Colegio_Provincias"],"options":{"limit":0}}')
  colegios_data=json.loads(r.text)['values']

  colegios_lima_data = []
  colegios_provincia_data = []

  for c in colegios_data:
    if 'Colegio_Lima' in c['contact_sub_type']:
      colegios_lima_data.append(c)
    else:
      colegios_provincia_data.append(c)

  return colegios_provincia_data,colegios_lima_data

def getActivityType():
  r=requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=OptionValue&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"value,label","options":{"limit":0},"option_group_id":"activity_type"}')
  activity_data = json.loads(r.text)['values']

  return activity_data

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@mod_main.route('/importar',methods=['GET','POST'])
def importar():
  colegios_provincia_data,colegios_lima_data = getColegios()
  tipo_actividad = getActivityType()
  if request.method == 'GET':
    #GET solo muestra la pantalla
    
    return render_template('importar.tpl.html',colegios_provincia=colegios_provincia_data,colegios_lima=colegios_lima_data,tipo_actividades=tipo_actividad)
  else:
    if 'archivos' in request.files:
      files = request.files.to_dict(flat=False)['archivos']
      for f in files:
        if f and allowed_file(f.filename):
          filename = secure_filename(f.filename)
          f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

      errores = []
      log = []
      folder = app.config['UPLOAD_FOLDER']
      files = listdir(folder)

      optSelect = request.form['contacto']
      #print("Esta es la opción seleccionada: " + optSelect)
      #time.sleep(60)

      if (optSelect == "colegio"):
        tipoColegio = request.form['colegio']
      else:
        tipoActividad = request.form['actividad']
        if (tipoActividad == 'simulacro') or (tipoActividad == 'admision'):
          print("Código para Simulacro")
        else:
          tipoColegioFichas = request.form['tipo_colegio']
          if (tipoColegioFichas == 'colegio_lima'):
            codigoColegio = request.form['select_colegio_lima2']
          elif (tipoColegioFichas == 'colegio_provincia'):
            codigoColegio = request.form['select_colegio_provincia2']
          actividad = request.form['select_actividades2']
          fecha = request.form['fecha']

          fecha = datetime.datetime.strptime(fecha, '%d/%m/%Y').strftime('%m/%d/%y')

          r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id","custom_8":"' + codigoColegio + '"}')
          idColegio = json.loads(r.text)['id']

          jotason = {"source_contact_id":idColegio,"activity_type_id":actividad,"activity_date_time":fecha}
          cadena = json.dumps(jotason,default=str)
          print(cadena)
          r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)
          print(r.text)
          idActividad = json.loads(r.text)['id']

          for file in files:
            if (file[file.find("."):] == ".xlsx"):
              xls_data = pd.read_excel(folder + '/' + file)
              for i in range(0,xls_data.shape[0]):
                #Lo primero es crear al contacto (INICIO CREACION DE CONTACTO)
                dni = xls_data['dni'][i]
                celular = xls_data['celular'][i]
                carreras = xls_data['carrera'][i].split(',')
                email = '-' if pd.isnull(xls_data['email'][i]) else xls_data['email'][i]
                tipo_interesado = '-'
                tipo_escolar = 'Otros'
                
                if pd.isnull(xls_data['soy_escolar'][i]):
                    anho_estudios = '-'
                    tipo_escolar = '-'
                else:
                    anho_estudios = xls_data['soy_escolar'][i]
                    tipo_interesado = 'Escolar'
                    
                if('5' in anho_estudios) or ('4' in anho_estudios):
                    anho_estudios = anho_estudios.replace('° Sec','to')
                    tipo_escolar = 'Otros' if pd.isnull(xls_data['soy_escolar_tipo'][i]) or xls_data['soy_escolar_tipo'][i] == ' ' else xls_data['soy_escolar_tipo'][i]
                    tipo_interesado = 'Escolar'
                elif ('3' in anho_estudios):
                    anho_estudios = anho_estudios.replace('° Sec','ero')
                    tipo_escolar = 'Otros' if pd.isnull(xls_data['soy_escolar_tipo'][i]) or xls_data['soy_escolar_tipo'][i] == ' ' else xls_data['soy_escolar_tipo'][i]
                    tipo_interesado = 'Escolar'

                if(tipo_interesado == '-'):
                    tipo_interesado = xls_data['soy'][i]

                if(tipo_interesado == 'Padre de familia'):
                    tipo_interesado = 'Padre de Familia / Tutor'
                    
                if (len(carreras) >= 2):
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U'),"custom_58":carreras[1].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U'),"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_105":tipo_escolar}
                elif (len(carreras) == 1):
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U'),"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_105":tipo_escolar}
                else:
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_105":tipo_escolar}

                cadena=json.dumps(jotason, default=str)
                print(cadena)
                r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)    
                print(r.text)
                id_contacto = json.loads(r.text)['id']
                if (email != '-'):
                    #print(id_contacto)
                    jotason = {"contact_id":id_contacto,"email":email}
                    cadena=json.dumps(jotason, default=str)
                    r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Email&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)
                    print(r.text)
                
                jotason = {"activity_id":idActividad,"contact_id":id_contacto}
                cadena = json.dumps(jotason,default=str)
                r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=ActivityContact&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)
                print(r.text)
                #Lo primero es crear al contacto (FIN CREACION DE CONTACTO)
            else:
              errores.append('El formato del archivo ' + file + ' no es válido')

    for file in files:
      if(file[file.find("."):] in [".xls",".xlsx",".csv"]):
        os.remove(folder + '/' + file) 

    if len(errores) == 0:
      errores.append('Se importaron los contactos con éxito')

    return render_template('importar.tpl.html',messages=errores,colegios_provincia=colegios_provincia_data,colegios_lima=colegios_lima_data,tipo_actividades=tipo_actividad)

@mod_main.route('/convertir',methods=['GET','POST'])
def convertir():
  if request.method == 'GET':
    #GET solo muestra la pantalla
    return render_template('convertir.tpl.html')
  else:
    if 'archivos' in request.files:
      files = request.files.to_dict(flat=False)['archivos']
      for f in files:
        if f and allowed_file(f.filename):
          filename = secure_filename(f.filename)
          f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

      errores = []
      log = []
      folder = app.config['UPLOAD_FOLDER']
      files = listdir(folder)

      for file in files:
        if (file[file.find("."):] == ".csv"):
          csv_data = pd.read_csv(folder + '/' + file)
          deleted_columns=['page1_captured','page1_processed','page1_image_file_name','form_page_1_is_scanned_page_number','publication_id',
                 'form_page_id_1','form_password','form_score','soy_escolar_score','soy_score','celular_score','dni_score','resido_en_score',
                 'soy_escolar_tipo_score','info_score','carrera_score']
          sLength = len(csv_data['form_id'])
          email=[]
          for i in range (0,sLength):
            email.append('')

          csv_data['email'] = Series(email, index=csv_data.index)      

          nombre = file.replace('.csv','.xlsx')
          #csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Hoja 1')
          try:
            csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1')
          except ValueError:
            deleted_columns=['página1_capturado','page1_processed','page1_image_file_name','formulario_de_la_página_1_es_la_página_escaneada_número','publication_id', 'form_page_id_1','form_password','form_score','soy_escolar_score','soy_score','celular_score','dni_score','resido_en_score','soy_escolar_tipo_score','info_score','carrera_score']
            csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1')

          errores.append('Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>')
          #errores.append('Desde aquí puede descargar el archivo convertido, <a href="/var/www/herramientas-ocai/interfazOCAICRM/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>')
        else:
          errores.append( file + ": No es un formato válido para la conversión")

      for file in files:
        if(file[file.find("."):] in [".xls",".xlsx",".csv"]):
          os.remove(folder + '/' + file)

    return render_template('convertir.tpl.html',messages=errores)


@mod_main.route('/tools',methods=['GET','POST'])
def tools():

  return render_template('tools.tpl.html')

@mod_main.route('/',methods=['GET','POST'])
def index():
  
  return render_template('index.tpl.html')

@mod_main.route('/reportes',methods=['GET'])
def reportes():

  return render_template('reportes.tpl.html')

@mod_main.route('/reporte1',methods=['GET'])
def reporte1():

  return render_template('reporte1.tpl.html')

@mod_main.route('/reporte2',methods=['GET'])
def reporte2():

  return render_template('reporte2.tpl.html')

@mod_main.route('/reporte3',methods=['GET'])
def reporte3():

  return render_template('reporte3.tpl.html')
