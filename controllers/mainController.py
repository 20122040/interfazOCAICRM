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
            if (file[file.find("."):] == ".xlsx"):
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
          #deleted_columns=['página1_capturado','page1_processed','page1_image_file_name','formulario_de_la_página_1_es_la_página_escaneada_número','publication_id', 'form_page_id_1','form_password','form_score','soy_escolar_score','soy_score','celular_score','dni_score','resido_en_score','soy_escolar_tipo_score','info_score','carrera_score']
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

def encontrar_colegio(id_colegio):
  print(id_colegio)
  r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"organization_name,contact_sub_type","id":'+ id_colegio +'}')
  print(r.text)
  datos_contacto = json.loads(r.text)['values']

  return datos_contacto[0]['organization_name'],datos_contacto[0]['contact_sub_type'][0]

def obtenerDatosContacto(lista_contactos1,lista_contactos2,id_contacto):
  dc1 = {}
  dc2 = {}
  for c1 in lista_contactos1:
    if(c1['contact_id'] == id_contacto):
      dc1 = c1
      break

  for c2 in lista_contactos2:
    if(c2['contact_id'] == id_contacto):
      dc2 = c2
      break

  return dc1,dc2



@mod_main.route('/exportar',methods=['GET','POST'])
def exportar():
  if request.method == 'GET':
    return render_template('exportar.tpl.html')
  else:
    carreras=['-','ANTROPOLOGIA','ARQUEOLOGIA','ARQUITECTURA','ARTE, MODA Y DISEÑO TEXTIL','CIENCIA POLITICA Y GOBIERNO','CIENCIAS DE LA INFORMACION','COMUNICACION AUDIOVISUAL','COMUNICACION PARA EL DESARROLLO','CONTABILIDAD','CREACION Y PRODUCCION ESCENICA','DANZA','DERECHO','DISEÑO GRAFICO','DISEÑO INDUSTRIAL','ECONOMIA','EDUCACION ARTISTICA','EDUCACION INICIAL','EDUCACION PRIMARIA','EDUCACION SECUNDARIA','ESCULTURA','ESTADISTICA','FILOSOFIA','FINANZAS','FISICA','GEOGRAFIA Y MEDIO AMBIENTE','GESTION','GRABADO','HISTORIA','HUMANIDADES','INGENIERIA BIOMEDICA','INGENIERIA CIVIL','INGENIERIA DE LAS TELECOMUNICACIONES','INGENIERIA DE MINAS','INGENIERIA ELECTRONICA','INGENIERIA GEOLOGICA','INGENIERIA INDUSTRIAL','INGENIERIA INFORMATICA','INGENIERIA MECANICA','INGENIERIA MECATRONICA','LINGUISTICA Y LITERATURA','MATEMATICAS','MUSICA','PERIODISMO','PINTURA','PSICOLOGIA','PUBLICIDAD','QUIMICA','RELACIONES INTERNACIONALES','SOCIOLOGIA','TEATRO','INGENIERIA AMBIENTAL Y SOSTENIBLE','GASTRONOMIA','OTROS','HOTELERIA','TURISMO']
    tiposEscolares=['-','1° o 2° puesto de la promoción','Tercio superior','Programa de bachillerato','Otros']

    nombre = 'InformacionInteresados' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx' 
    writer = pd.ExcelWriter('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre, engine='xlsxwriter')
    workbook = writer.book

    r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"source_contact_id","activity_type_id":{"IN":["Una mañana en ciencias","Una mañana en artes","Charla informativa","Charla Institucional","Descubre PUCP","Feria vocacional","Visita del representate PUCP al colegio","Taller: Camino a la vocación","Visita de Investigación"]},"options":{"limit":0}}')
    actividades = json.loads(r.text)['values']

    r_lista_contactos1 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,custom_103,custom_57,custom_58,custom_50,custom_84","options":{"limit":0}}')
    r_lista_contactos2 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,custom_105,custom_52,custom_107,contact_type,email","options":{"limit":0}}')

    lista_contactos1 = json.loads(r_lista_contactos1.text)['values']
    lista_contactos2 = json.loads(r_lista_contactos2.text)['values']

    df = pd.DataFrame(columns=['dni','soy_escolar','tipo_interesado','soy_escolar_tipo','celular', 'email','carrera_interes1','carrera_interes2','donde_desea_recibir_info','colegio','tipo_colegio'])
    #df = pd.DataFrame(columns=['dni','soy_escolar','tipo_interesado','soy_escolar_tipo','celular', 'email','carrera_interes1'])
    i=0
    for a in actividades:
        nombre_colegio,tipo_colegio = encontrar_colegio(a['source_contact_id'])
        r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=ActivityContact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"activity_id":' + a['id'] + ',"options":{"limit":0}}')
        contactos = json.loads(r.text)['values']
        for c in contactos:
          id_contacto = c['contact_id']
          #datos_contacto = 
            #r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"custom_84,email,contact_type,organization_name,custom_103,custom_50,custom_52,custom_57,custom_58,custom_105,custom_107","id":'+ c['contact_id'] +'}')
            #print (r.text)
          datos_contacto1,datos_contacto2 = obtenerDatosContacto(lista_contactos1,lista_contactos2,id_contacto)
            #print(datos_contacto[0]['custom_84'])
          print("Datos CONTACTO")
          print(datos_contacto1)
          print(datos_contacto2)

          if (datos_contacto2 == {}):
            continue

          if(datos_contacto2['contact_type'] == 'Individual'):
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

            df.loc[i] = [datos_contacto1['custom_103'],datos_contacto2['custom_52'],datos_contacto1['custom_50'],tiposEscolares[id_tipo_escolar],datos_contacto1['custom_84'],datos_contacto2['email'],carreras[id_carrera1],carreras[id_carrera2],datos_contacto2['custom_107'],nombre_colegio,tipo_colegio]
            print(df.loc[i])
            i = i + 1
    #print(df)
    df.to_excel(writer,sheet_name='Hoja 1',index=False)  

    writer.save()
    workbook.close()

    errores=['Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>']

    return render_template('exportar.tpl.html',messages=errores)


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
