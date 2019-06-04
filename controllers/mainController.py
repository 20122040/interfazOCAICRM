from flask import request, render_template, Blueprint, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, ALLOWED_EXTENSIONS
from urllib.parse import quote_plus
import os
import html5lib

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
          tipoColegioFichas = request.form['tipo_colegio']
          if (tipoColegioFichas == 'colegio_lima'):
            f.save(os.path.join(app.config['UPLOAD_FOLDER_LIMA'], filename))
          elif (tipoColegioFichas == 'colegio_provincia'):
            f.save(os.path.join(app.config['UPLOAD_FOLDER_PROVINCIA'], filename))

      errores = []
      log = []
      
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
            folder = app.config['UPLOAD_FOLDER_LIMA']
            files = listdir(folder)
          elif (tipoColegioFichas == 'colegio_provincia'):
            codigoColegio = request.form['select_colegio_provincia2']
            folder = app.config['UPLOAD_FOLDER_PROVINCIA']
            files = listdir(folder)
          actividad = request.form['select_actividades2']
          fecha = request.form['fecha']

          print(fecha)

          fecha = datetime.datetime.strptime(fecha, '%m/%d/%Y').strftime('%m/%d/%y')

          r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id","custom_8":"' + codigoColegio + '"}')
          try:
            idColegio = json.loads(r.text)['id']
          except KeyError:
            errores.append("El colegio seleccionado no es válido.")
            for file in files:
              if(file[file.find("."):] in [".xls",".xlsx",".csv"]):
                os.remove(folder + '/' + file) 
            return render_template('importar.tpl.html',messages=errores,colegios_provincia=colegios_provincia_data,colegios_lima=colegios_lima_data,tipo_actividades=tipo_actividad)


          jotason = {"source_contact_id":idColegio,"activity_type_id":actividad,"activity_date_time":fecha,"subject":"Capturado por ficha de datos"}
          cadena = json.dumps(jotason,default=str)
          print(cadena)
          r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)
          print(r.text)

          try:
            idActividad = json.loads(r.text)['id']
          except KeyError:
            errores.append("La actividad seleccionada no es válida.")
            for file in files:
              if(file[file.find("."):] in [".xls",".xlsx",".csv"]):
                os.remove(folder + '/' + file) 
            return render_template('importar.tpl.html',messages=errores,colegios_provincia=colegios_provincia_data,colegios_lima=colegios_lima_data,tipo_actividades=tipo_actividad)


          for file in files:
            if ((file[file.find("."):] == ".xlsx") and (file == filename)):
              print(file + " = " + filename)
              xls_data = pd.read_excel(folder + '/' + file)
              for i in range(0,xls_data.shape[0]):
                #Lo primero es crear al contacto (INICIO CREACION DE CONTACTO)
                try:
                  dni = xls_data['dni'][i]
                except KeyError:
                 # r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=delete&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"id":' + idActividad + '}')
                  errores.append("Hay un error en el archivo importado. No es un archivo válido o no es correlativo desde el el elemento " + str(i))
                  break

                celular = xls_data['celular'][i]
                carreras = '-' if pd.isnull(xls_data['carrera'][i]) else xls_data['carrera'][i].split(',')
                email = '-' if pd.isnull(xls_data['email'][i]) else xls_data['email'][i]
                info = '-' if pd.isnull(xls_data['info'][i]) else xls_data['info'][i]
                tipo_interesado = '-'
                tipo_escolar = 'Otros'


                if(pd.isnull(xls_data['dni'][i])):
                  dni = '00000000'
                else:
                  dni = str(int(dni))

                if(pd.isnull(xls_data['celular'][i])):
                  celular = '000000000'
                else:
                  celular = str(celular).replace('.0','')
                
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
                    tipo_interesado = '-' if pd.isnull(xls_data['soy'][i]) else xls_data['soy'][i]

                if(tipo_interesado == 'Padre de familia'):
                    tipo_interesado = 'Padre de Familia / Tutor'

                print(carreras)
                    
                if (len(carreras) >= 2):
                  if (carreras[0].upper().lstrip().rstrip() == 'ARTE'):
                    if(len(carreras) == 2):
                      jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_57":"ARTE, MODA Y DISEÑO TEXTIL","custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_107":info}
                    else:                    
                      jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_57":'ARTE, MODA Y DISEÑO TEXTIL',"custom_58":carreras[2].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U').replace('Ü','U').lstrip().rstrip(),"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_107":info}
                  elif (carreras[1].upper().lstrip().rstrip() == 'ARTE'):
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U').replace('Ü','U').lstrip().rstrip(),"custom_58":'ARTE, MODA Y DISEÑO TEXTIL',"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_107":info}
                  else:
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U').replace('Ü','U').lstrip().rstrip(),"custom_58":carreras[1].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U').replace('Ü','U').lstrip().rstrip(),"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_105":tipo_escolar,"custom_107":info}
                elif (len(carreras) == 1):
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().replace('Á','A').replace('É','E').replace('Í','I').replace('Ó','O').replace('Ú','U').replace('Ü','U').lstrip().rstrip(),"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_105":tipo_escolar,"custom_107":info}
                else:
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre","custom_103":dni,"custom_84":celular,"custom_52":anho_estudios,"custom_50":tipo_interesado,"custom_107":info}

                cadena=json.dumps(jotason, default=str)
                print(cadena)
                print(json)
                
                r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)    
                print(r.text)

                try:
                  id_contacto = json.loads(r.text)['id']
                except KeyError:
                  errores.append("El elemento #" + str(i) + " no se importará por tener un error. Revisar: " + r.text)
                  continue

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
    else:
      errores.append('Corregir los errores y subir solo las filas corregidas.')

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
          try:
            sLength = len(csv_data['form_id'])
          except KeyError:
            errores.append(file + ': El archivo CSV no es un archivo obtenido del Form Return')
            break

          email=[]
          for i in range (0,sLength):
            email.append('')

          csv_data['email'] = Series(email, index=csv_data.index)      

          nombre = file.replace('.csv','.xlsx')
          #csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Hoja 1')
          try:
            #csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1')
            csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Sheet 1')
          except ValueError:
            deleted_columns=['página1_capturado','page1_processed','page1_image_file_name','formulario_de_la_página_1_es_la_página_escaneada_número','publication_id', 'form_page_id_1','form_password','form_score','soy_escolar_score','soy_score','celular_score','dni_score','resido_en_score','soy_escolar_tipo_score','info_score','carrera_score']
            #csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1')
            csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Hoja 1')

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

def encontrar_colegio(id_colegio):
  print(id_colegio)
  r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"organization_name,contact_sub_type","id":'+ id_colegio +'}')
  print(r.text)
  datos_contacto = json.loads(r.text)['values']

  return datos_contacto[0]['organization_name'],datos_contacto[0]['contact_sub_type'][0]

def obtenerDatosContacto(lista_contactos1,lista_contactos1_5,lista_contactos2,lista_contactos3,id_contacto):
  dc1 = {}
  dc2 = {}
  dc3 = {}
  dc1_5 = {}

  for c1 in lista_contactos1:
    if(c1['contact_id'] == id_contacto):
      dc1 = c1
      break

  for c1_5 in lista_contactos1_5:
    if(c1_5['contact_id'] == id_contacto):
      dc1_5 = c1_5
      break

  for c2 in lista_contactos2:
    if(c2['contact_id'] == id_contacto):
      dc2 = c2
      break

  for c3 in lista_contactos3:
    if(c3['contact_id'] == id_contacto):
      dc3 = c3
      break

  return dc1,dc1_5,dc2,dc3

def getContactosActividades(actividades):
  id_actividades = []
  for a in actividades:
    id_actividades.append(a['id'])

  cadena = json.dumps(id_actividades,default=str)
  r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=ActivityContact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"activity_id":{"IN":'+ cadena +'},"options":{"limit":0}}')  

  contactos = json.loads(r.text)['values']
  return contactos

def getContactosEnActividad(contactos_actividad,id_actividad):
  lst = []
  for c in contactos_actividad:
    if c['activity_id'] == id_actividad:
      lst.append(c)
  return lst

def cadenaTipoActividad(id):
  ids_tipos = ['69','68','67','64','63','62','61','60','59']
  tipos = ['Charla para Padres','Visita de Investigación','Taller: Camino a la vocación','Una mañana en artes','Charla Institucional','Una mañana en ciencias','Descubre PUCP','Feria Vocacional','Charla informativa']

  for i in range(0,len(ids_tipos)):
    if (id == ids_tipos[i]):
      return tipos[i]
  return ' '

@mod_main.route('/exportar',methods=['GET','POST'])
def exportar():
  if request.method == 'GET':
    return render_template('exportar.tpl.html')
  else:
    print("Empezó la exportación")
    carreras=['-','ANTROPOLOGIA','ARQUEOLOGIA','ARQUITECTURA','ARTE, MODA Y DISEÑO TEXTIL','CIENCIA POLITICA Y GOBIERNO','CIENCIAS DE LA INFORMACION','COMUNICACION AUDIOVISUAL','COMUNICACION PARA EL DESARROLLO','CONTABILIDAD','CREACION Y PRODUCCION ESCENICA','DANZA','DERECHO','DISEÑO GRAFICO','DISEÑO INDUSTRIAL','ECONOMIA','EDUCACION ARTISTICA','EDUCACION INICIAL','EDUCACION PRIMARIA','EDUCACION SECUNDARIA','ESCULTURA','ESTADISTICA','FILOSOFIA','FINANZAS','FISICA','GEOGRAFIA Y MEDIO AMBIENTE','GESTION','GRABADO','HISTORIA','HUMANIDADES','INGENIERIA BIOMEDICA','INGENIERIA CIVIL','INGENIERIA DE LAS TELECOMUNICACIONES','INGENIERIA DE MINAS','INGENIERIA ELECTRONICA','INGENIERIA GEOLOGICA','INGENIERIA INDUSTRIAL','INGENIERIA INFORMATICA','INGENIERIA MECANICA','INGENIERIA MECATRONICA','LINGUISTICA Y LITERATURA','MATEMATICAS','MUSICA','PERIODISMO','PINTURA','PSICOLOGIA','PUBLICIDAD','QUIMICA','RELACIONES INTERNACIONALES','SOCIOLOGIA','TEATRO','INGENIERIA AMBIENTAL Y SOSTENIBLE','GASTRONOMIA','OTROS','HOTELERIA','TURISMO']
    tiposEscolares=['-','1° o 2° puesto de la promoción','Tercio superior','Programa de bachillerato','Otros']

    nombre = 'InformacionInteresados' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx' 
    #writer = pd.ExcelWriter('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre, engine='xlsxwriter')
    writer = pd.ExcelWriter('static/bases/' + nombre, engine='xlsxwriter')
    workbook = writer.book

    print("Obtendremos todas las actividades")
    r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"source_contact_id,activity_type_id","activity_type_id":{"IN":["Una mañana en ciencias","Una mañana en artes","Charla informativa","Charla Institucional","Visita de Investigación","Taller: Camino a la vocación","Descubre PUCP","Feria vocacional","Charla para padres"]},"options":{"limit":0}}')
    actividades = json.loads(r.text)['values']                                                                                                                                                                                                                                     

    print("Obtendremos a todos los contactos")
    r_lista_contactos1 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,custom_103,custom_57,custom_58","options":{"limit":0}}')
    r_lista_contactos1_5 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,custom_50,custom_84","options":{"limit":0}}')
    r_lista_contactos2 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,custom_105,custom_52,custom_107","options":{"limit":0}}')
    r_lista_contactos3 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,email","options":{"limit":0}}')

    lista_contactos1 = json.loads(r_lista_contactos1.text)['values']
    lista_contactos1_5 = json.loads(r_lista_contactos1_5.text)['values']
    lista_contactos2 = json.loads(r_lista_contactos2.text)['values']
    lista_contactos3 = json.loads(r_lista_contactos3.text)['values']

    df = pd.DataFrame(columns=['dni','soy_escolar','tipo_interesado','soy_escolar_tipo','celular', 'email','carrera_interes1','carrera_interes2','donde_desea_recibir_info','colegio','tipo_colegio','tipo_actividad'])
    i=0

    print("Obtendremos todos los contactos que están en una actividad")
    contactos_todos = getContactosActividades(actividades)
    for a in actividades:
        id_tipo_actividad = a["activity_type_id"]
        nombre_colegio,tipo_colegio = encontrar_colegio(a['source_contact_id'])
        print("Obtendremos a los contactos de la actividad en el colegio: " + nombre_colegio)       
        contactos = getContactosEnActividad(contactos_todos,a['id'])
        for c in contactos:
          id_contacto = c['contact_id']
          print("Obtener los datos de este contacto: " + id_contacto)
          datos_contacto1,datos_contacto1_5,datos_contacto2,datos_contacto3 = obtenerDatosContacto(lista_contactos1,lista_contactos1_5,lista_contactos2,lista_contactos3,id_contacto)

          if (datos_contacto2 == {}):
            continue

          if(datos_contacto3['contact_type'] == 'Individual'):
            id_tipo_escolar = datos_contacto2['custom_105'] 
            id_carrera1 = datos_contacto1['custom_57']
            id_carrera2 = datos_contacto1['custom_58']

            if (id_tipo_escolar == '') or (id_tipo_escolar == ' ') or (id_tipo_escolar =='-'):
              id_tipo_escolar = 0
            else:
              id_tipo_escolar = int(id_tipo_escolar)

            if (id_carrera1 == '') or (id_carrera1 == ' ') or (id_carrera1 =='-'):
              id_carrera1 = 0
            else:
              id_carrera1 = int(id_carrera1)

            if (id_carrera2 == '') or (id_carrera2 == ' ') or (id_carrera2 =='-'):
              id_carrera2 = 0
            else:
              id_carrera2 = int(id_carrera2)
            df.loc[i] = [datos_contacto1['custom_103'],datos_contacto2['custom_52'],datos_contacto1_5['custom_50'],tiposEscolares[id_tipo_escolar],datos_contacto1_5['custom_84'],datos_contacto3['email'],carreras[id_carrera1],carreras[id_carrera2],datos_contacto2['custom_107'],nombre_colegio,tipo_colegio,cadenaTipoActividad(id_tipo_actividad)]
            print(df.loc[i])
            i = i + 1
    df.to_excel(writer,sheet_name='Hoja 1',index=False)  

    writer.save()
    workbook.close()

    errores=['Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>']

    return render_template('exportar.tpl.html',messages=errores)

@mod_main.route('/reportes',methods=['GET'])
def reportes():

  return render_template('reportes.tpl.html')

@mod_main.route('/reporte1',methods=['GET','POST'])
def reporte1():
  if request.method == 'GET':
    return render_template('reporte1.tpl.html')
  else:
    errores=[]
    anho_reporte = request.form['anho']
    if (anho_reporte == '2018'):
      time.sleep(100)
      errores.append("Puede descargar su reporte aquí: <a href='/static/fake_folder/ReporteCRM_2018.xlsx'>Descargar archivo</a>")
    elif (anho_reporte == '2019'):
      time.sleep(50)
      errores.append("Puede descargar su reporte aquí: <a href='/static/fake_folder/ReporteCRM_2019.xlsx'>Descargar archivo</a>")
  return render_template('reporte1.tpl.html',messages=errores)

@mod_main.route('/reporte2',methods=['GET'])
def reporte2():

  return render_template('reporte2.tpl.html')

@mod_main.route('/reporte3',methods=['GET','POST'])
def reporte3():

  if request.method == 'GET':
    return render_template('reporte3.tpl.html')
  else:
    errores=[]
    proceso = request.form['proceso']
    
    if (proceso == '1'):
      time.sleep(20)
      errores.append("Puede descargar su reporte aquí: <a href='/static/fake_folder/Reporte3_2019_06_04.xlsx'>Descargar archivo</a>")
    return render_template('reporte3.tpl.html',messages=errores)

def yaFueRevisado(contDni,num,dni,lista):
    if contDni==0:
        return False
    
    #print("Esta es la opción elegida" + str(num))
    if num==1:
        for i in range(1,contDni):
            #print(dni + lista['DNI3'][i] +"Cuadro1")
            if dni==lista['DNI1'][i]:
                return True
    if num==2:
        for i in range(1,contDni):
            #print(dni + lista['DNI3'][i] +"Cuadro2")
            if dni==lista['DNI2'][i]:
                return True
    if num==3:
        for i in range(1,contDni):
            #print(dni + lista['DNI3'][i] +"Cuadro3")
            if dni==lista['DNI3'][i]:
                return True
            
    if num==5:
        for i in range(1,contDni):
            #print(dni + lista['DNI3'][i] +"Cuadro3")
            if dni==lista['DNI5'][i]:
                return True
            
    if num==6:
        for i in range(1,contDni):
            #print(dni + lista['DNI3'][i] +"Cuadro3")
            if dni==lista['DNI6'][i]:
                return True
    
    if num==7:
        for i in range(1,contDni):
            #print(dni + lista['DNI3'][i] +"Cuadro3")
            if dni==lista['DNI7'][i]:
                return True
    
    if num==8:
        for i in range(1,contDni):
            #print(dni + lista['DNI3'][i] +"Cuadro3")
            if dni==lista['DNI8'][i]:
                return True


@mod_main.route('/verificaciones',methods=['GET','POST'])
def verificaciones():
  lisSedesProv=['LIMA','PUNO']
  if request.method == 'GET':
    return render_template('verificaciones.tpl.html')
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
      print(files)

      for file in files:
        print(file)
        if (file[file.find("."):] == ".xls") and (file == filename):
          #print(file)
          #soup = BeautifulSoup(requests.get(file).text)
          #print(pd.__version__)
          print(folder+"/"+file)
          tablas=pd.read_html(folder+"/"+file)
          tabla=tablas[1]
          tabla.columns = tabla.iloc[0]
          tabla = tabla[1:]
          tam=tabla['CANDIDATO'].count()
          tabla.loc[:,'FECHA REGISTRO']=pd.to_datetime(tabla['FECHA REGISTRO'])
          tabla.loc[:,'FECHA REGISTRO']=tabla['FECHA REGISTRO'].dt.strftime('%m/%d/%Y')

          ##Creamos tabla para exportar excel

          cuadro1=pd.DataFrame(columns=['CODIGO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','ANHO_FIN','COLEGIO']) ###AÑO FIN
          cuadro2=pd.DataFrame(columns=['CODIGO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','EDAD','ANHO_NACIMIENTO']) ###EDAD
          cuadro3=pd.DataFrame(columns=['CODIGO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','SEDE','DPTO_RESIDENCIA']) ###SEDE
          cuadro5=pd.DataFrame(columns=['CODIGO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','DISCAPACIDAD','DESCR_DISCAPACIDAD']) ###DISCAPACIDAD
          cuadro6=pd.DataFrame(columns=['CODIGO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','COD_COLEGIO','COLEGIO']) ###SIN INFO DE COLEGIO
          cuadro7=pd.DataFrame(columns=['CODIGO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','PAGO']) ###POSTULANTES PAGO NO
          cuadro8=pd.DataFrame(columns=['CODIGO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','PAGO']) ###CANDIDATOS PAGO SI

          cuadro4=pd.DataFrame(columns=['DNI1','DNI2','DNI3','DNI5','DNI6','DNI7','DNI8'])

          cont1=1 ###AÑO FIN
          cont2=1 ###EDAD
          cont3=1 ###SEDE
          cont5=1 ###DISCAPACIDAD
          cont6=1 ###SIN INFO DE COLEGIO
          cont7=1 ###POSTULANTES PAGO NO
          cont8=1 ###CANDIDATOS PAGO SI

          if not (os.path.isfile('Lista.xlsx')):
            writer=pd.ExcelWriter('Lista.xlsx',engine='xlsxwriter')
            cuadro4.to_excel(writer,sheet_name='Hoja 1')
            workbook1=writer.book
            writer.save()

          lista=pd.read_excel('Lista.xlsx')
          #print(lista)
          contDni1=lista["DNI1"].count()
          contDni2=lista['DNI2'].count()
          contDni3=lista['DNI3'].count()
          contDni5=lista['DNI5'].count()
          contDni6=lista['DNI6'].count()
          contDni7=lista['DNI7'].count()
          contDni8=lista['DNI8'].count()

          contDni1Or = contDni1
          contDni2Or = contDni2
          contDni3Or = contDni3
          contDni5Or = contDni5
          contDni6Or = contDni6
          contDni7Or = contDni7
          contDni8Or = contDni8

          for i in range(1, tam+1):
              #print(tabla['ANO FIN'][i])
              if pd.isnull(tabla['ANO FIN'][i]):
                  yearFin='-'
              else:
                  yearFin=str(tabla['ANO FIN'][i])
              edad=int(tabla['EDAD'][i])
              sede=tabla['SEDE'][i]
              depResidencia=tabla['DEPARTAMENTO COLEGIO'][i]
              discapacidad=tabla['CUENTA CON ALGUNA DISCAPACIDAD'][i]
              estado = tabla['ESTADO CANDIDATO'][i]
              dni=tabla['DNI'][i]
              #print()
              #print(dni)
              ##Modificamos la sede para hacer las comparaciones a nivel departamento
              if sede=='TRUJILLO':
                  sede='LA LIBERTAD'
              elif sede=='HUANCAYO':
                  sede='JUNIN'
              elif sede=='IQUITOS':
                  sede='LORETO'
              
              if depResidencia == 'CALLAO':
                  depResidencia = 'LIMA'
              
              ##Verificamos Año fin
              if len(yearFin)!=4 and yearFin != '-':
                  if yaFueRevisado(contDni1Or,1,dni,lista)==False:
                      print("Se agregó a columna 1 y cuadro 1")
                      cuadro1.at[cont1,'DNI']=dni
                      cuadro1.at[cont1,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro1.at[cont1,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro1.at[cont1,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro1.at[cont1,'PROCESO']=tabla['PROCESO'][i]
                      cuadro1.at[cont1,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro1.at[cont1,'ANHO_FIN']=yearFin
                      cuadro1.at[cont1,'COLEGIO']=tabla['DESCRIPCION COLEGIO'][i]
                      lista.at[contDni1,'DNI1']=dni
                      contDni1+=1
                      cont1+=1
                      ##Hacer que el programa bote como resultado que se debe verificar año fin

              ##Verificamos edad
              if edad>19 and edad<=13:
                  if yaFueRevisado(contDni2Or,2,dni,lista)==False:
                      #print("Se agregó a columna 2 y cuadro 2")
                      cuadro2.at[cont2,'DNI']=tabla['DNI'][i]
                      cuadro2.at[cont2,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro2.at[cont2,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro2.at[cont2,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro2.at[cont2,'PROCESO']=tabla['PROCESO'][i]
                      cuadro2.at[cont2,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro2.at[cont2,'EDAD']=edad
                      cuadro2.at[cont2,'ANHO_NACIMIENTO']=tabla['FECHA NACIMIENTO'][i]
                      lista.at[contDni2,'DNI2']=dni
                      contDni2+=1
                      cont2+=1
                  ##Hacer que el programa bote como resultado que se debe verificar edad
                  
              ##Verificamos discapacidad
              if discapacidad=='Si' or discapacidad=='SI':
                  if yaFueRevisado(contDni5Or,5,dni,lista)==False:
                      #print("Se agregó a columna 5 y cuadro 5")
                      cuadro5.at[cont5,'DNI']=tabla['DNI'][i]
                      cuadro5.at[cont5,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro5.at[cont5,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro5.at[cont5,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro5.at[cont5,'PROCESO']=tabla['PROCESO'][i]
                      cuadro5.at[cont5,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro5.at[cont5,'DISCAPACIDAD']=discapacidad
                      cuadro5.at[cont5,'DESCR_DISCAPACIDAD']=tabla['DESCRIPCIÓN DE DISCAPACIDAD'][i]
                      lista.at[contDni5,'DNI5']=dni
                      contDni5+=1
                      cont5+=1
                  ##Hacer que el programa bote como resultado que se debe verificar la discapacidad

              ##Verificamos sede  
              if sede != depResidencia and depResidencia in lisSedesProv and sede != "-":
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if yaFueRevisado(contDni3Or,3,dni,lista)==False:
                      #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 3 y cuadro 3")
                      cuadro3.at[cont3,'DNI']=tabla['DNI'][i]
                      cuadro3.at[cont3,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro3.at[cont3,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro3.at[cont3,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro3.at[cont3,'PROCESO']=tabla['PROCESO'][i]
                      cuadro3.at[cont3,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro3.at[cont3,'SEDE']=tabla['SEDE'][i]
                      cuadro3.at[cont3,'DPTO_RESIDENCIA']=tabla['DEPARTAMENTO COLEGIO'][i]
                      lista.at[contDni3,'DNI3']=dni
                      contDni3+=1
                      cont3+=1
                  ##hacer que el programa bote como resultado que se debe hacer cambio de sede     
                  
              ##Verificamos información escolar  
              if estado == 'POSTULANTE' and pd.isnull(tabla['COLEGIO'][i]):
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if yaFueRevisado(contDni6Or,6,dni,lista)==False:
                      #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 6 y cuadro 6")
                      cuadro6.at[cont6,'DNI']=tabla['DNI'][i]
                      cuadro6.at[cont6,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro6.at[cont6,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro6.at[cont6,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro6.at[cont6,'PROCESO']=tabla['PROCESO'][i]
                      cuadro6.at[cont6,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro6.at[cont6,'COD_COLEGIO']=tabla['COLEGIO'][i]
                      cuadro6.at[cont6,'COLEGIO']=tabla['DESCRIPCION COLEGIO'][i]
                      lista.at[contDni6,'DNI6']=dni
                      contDni6+=1
                      cont6+=1
                  ##hacer que el programa bote como resultado que se debe hacer verificacion de informacion escolar
                  
              ##Verificamos si es POSTULANTE con pago NO  
              if estado == 'POSTULANTE' and tabla['¿PAGO?'][i] == 'No':
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if yaFueRevisado(contDni7Or,7,dni,lista)==False:
                      #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 7 y cuadro 7")
                      cuadro7.at[cont7,'DNI']=tabla['DNI'][i]
                      cuadro7.at[cont7,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro7.at[cont7,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro7.at[cont7,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro7.at[cont7,'PROCESO']=tabla['PROCESO'][i]
                      cuadro7.at[cont7,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro7.at[cont7,'PAGO']=tabla['¿PAGO?'][i]
                      lista.at[contDni7,'DNI7']=dni
                      contDni7+=1
                      cont7+=1
                  ##hacer que el programa bote como resultado que se debe hacer una verificacion de pago
              
              ##Verificamos si es CANDIDATO con pago SI  
              if estado == 'CANDIDATO' and tabla['¿PAGO?'][i] == 'SI':
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if yaFueRevisado(contDni8Or,8,dni,lista)==False:
                      #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 7 y cuadro 7")
                      cuadro8.at[cont8,'DNI']=tabla['DNI'][i]
                      cuadro8.at[cont8,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro8.at[cont8,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro8.at[cont8,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro8.at[cont8,'PROCESO']=tabla['PROCESO'][i]
                      cuadro8.at[cont8,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro8.at[cont8,'PAGO']=tabla['¿PAGO?'][i]
                      lista.at[contDni8,'DNI8']=dni
                      contDni8+=1
                      cont8+=1
                  ##hacer que el programa bote como resultado que se debe hacer una verificacion de pago
              
      nombre_reporte = 'ReporteValidacion' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx'
      writer1=pd.ExcelWriter('static/validacion/'+nombre_reporte,engine='xlsxwriter')
      cuadro1.to_excel(writer1,sheet_name='Año Fin Incorrecto')
      cuadro2.to_excel(writer1,sheet_name='Edades')
      cuadro3.to_excel(writer1,sheet_name='Sede')
      cuadro5.to_excel(writer1,sheet_name='Discapacidad')
      cuadro6.to_excel(writer1,sheet_name='Sin información Escolar')
      cuadro7.to_excel(writer1,sheet_name='POSTULANTES pago NO')
      cuadro8.to_excel(writer1,sheet_name='CANDIDATOS pago SI')
      workbook1=writer1.book
      writer1.save()
      writer=pd.ExcelWriter('Lista.xlsx',engine='xlsxwriter')
      lista.to_excel(writer,sheet_name='Hoja 1')
      writer.save()        
      errores.append('Desde aquí puede descargar el archivo revisado, <a href="/static/validacion/'+ nombre_reporte +'">Descargar archivo en XLSX</a>')
  return render_template('verificaciones.tpl.html',messages=errores)
