from flask import request, render_template, Blueprint, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
from app import app, ALLOWED_EXTENSIONS
from urllib.parse import quote_plus
import os
import html5lib
from num2words import num2words

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
  r=requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"organization_name,custom_111","contact_sub_type":["Colegio_Lima","Colegio_Provincias"],"options":{"limit":0}}')
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


def get_cursos(nombre_programa,cursos):
    lst_cursos=[]
    for i in range(0,cursos['CURSO'].count()):
        if nombre_programa == cursos['PROGRAMA'][i]:
            lst_cursos.append(cursos['NOMBRE DEL CURSO'][i])
    return lst_cursos

def get_cursos_dictionary(nombre_programa,cursos):
    lst_cursos=[]
    curso={}
    for i in range(0,cursos['CURSO'].count()):
        if nombre_programa == cursos['PROGRAMA'][i]:
            curso={'codigo':cursos['CURSO'][i],'nombre':cursos['NOMBRE DEL CURSO'][i],'creditos':cursos['CRÉDITOS'][i]}
            lst_cursos.append(curso)
    return lst_cursos

@mod_main.route('/diccionario_posgrado',methods=['GET','POST'])
def diccionario_posgrado():
  if request.method == 'GET':
    errores = ['Descarga el formato de programas y cursos, <a href="/static/formato/'+ 'FORMATO_POSGRADO.xlsx' +'">Descargar el formato</a>']
    return render_template('diccionario_posgrado.tpl.html',messages=errores)
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
        nombre = 'DiccionarioPosgrado' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.txt' 
        if (file[file.find("."):] == ".xlsx") and (file == filename):

          posgrado = pd.read_excel(folder + '/' + file)

          lst = []
          for i in range(0,posgrado['DNI'].count()):
              #print(posgrado['DNI'][i])
              dictionary = {'DNI':posgrado['DNI'][i],'ApellidoPaterno':posgrado['PRIMER APELLIDO'][i],'ApellidoMaterno':posgrado['SEGUNDO APELLIDO'][i],
                            'Nombres':posgrado['NOMBRES'][i],'CORREO1':posgrado['EMAIL'][i],'CORREO2':posgrado['CORREO 1'][i] if posgrado['CORREO 1'][i] != '-' else '','CORREO3':posgrado['CORREO 2'][i] if posgrado['CORREO 2'][i] != '-' else '','Programa':posgrado['ETAPA CANDIDATO'][i] + ' EN ' +posgrado['ESPECIALIDAD'][i]};
              lst.append(dictionary)

          str_posgrado = json.dumps(lst, ensure_ascii=False)
          writer = 'static/bases/' + nombre
          #writer = '/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre 
          with open(writer, "w", encoding='utf8') as file:
            file.write(str_posgrado)

          errores.append('Desde aquí puede descargar el archivo con el diccionario, <a href="/static/bases/'+ nombre +'">Descargar archivo en TXT</a>')
        else:
          errores.append(file + ": No es un formato válido para la conversión")

    return render_template('diccionario_posgrado.tpl.html',messages=errores)



@mod_main.route('/diccionario_alumnoslibres',methods=['GET','POST'])
def diccionario_alumnoslibres():
  if request.method == 'GET':
    errores = ['Descarga el formato de programas y cursos, <a href="/static/formato/'+ 'FORMATO_AL.xlsx' +'">Descargar el formato</a>']
    return render_template('diccionario_alumnoslibres.tpl.html',messages=errores)
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
        nombre = 'DiccionarioAL' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.txt' 
        if (file[file.find("."):] == ".xlsx") and (file == filename):
          programas = pd.read_excel(folder + '/' + file,sheet_name='PROGRAMAS')
          cursos = pd.read_excel(folder + '/' + file,sheet_name='CURSOS')

          #Diccionario de programas
          lst_programas = []
          p={}
          for i in range(0,programas['CODIGO PROGRAMA'].count()):
              lst_cursos = get_cursos_dictionary(programas['PROGRAMA'][i],cursos)
              p={'codigo':programas['CODIGO PROGRAMA'][i],'nombre':programas['PROGRAMA'][i],'cursos':lst_cursos}
              lst_programas.append(p)
          #lst_programas contiene el diccionario completo
          str_programas = json.dumps(lst_programas, ensure_ascii=False)
          writer = 'static/bases/' + nombre
          #writer = '/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre 
          with open(writer, "w") as file:
            file.write(str_programas)

          errores.append('Desde aquí puede descargar el archivo con el diccionario, <a href="/static/bases/'+ nombre +'">Descargar archivo en TXT</a>')
        else:
          errores.append(file + ": No es un formato válido para la conversión")

    return render_template('diccionario_alumnoslibres.tpl.html',messages=errores)


@mod_main.route('/numero-texto',methods=['GET','POST'])
def convertir_numeros():
  if request.method == 'GET':
    return render_template('convertir_numeros.tpl.html')
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
        nombre = 'NumerosATextos' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx' 
        writer = pd.ExcelWriter('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre, engine='xlsxwriter')
        #writer = pd.ExcelWriter('static/bases/' + nombre, engine='xlsxwriter')
        workbook = writer.book
        if (file[file.find("."):] == ".xlsx") and (file == filename):
          numeros = pd.read_excel(folder + '/' + file)

          df = pd.DataFrame(columns=['nro','txt'])
          i=0

          for n in numeros[numeros.columns[0]]:
            df.loc[i] = [n,num2words(n,lang='es')]
            i = i + 1

          df.to_excel(writer,sheet_name='Hoja 1',index=False)  
          writer.save()
          workbook.close()

          errores.append('Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>')
        else:
          errores.append(file + ": No es un formato válido para la conversión")

    return render_template('convertir_numeros.tpl.html',messages=errores)

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
      archivo_subido = filename      
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

          r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id","custom_111":"' + codigoColegio + '"}')
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
          #print(cadena)
          r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)
          #print(r.text)
          try:
            idActividad = json.loads(r.text)['id']
          except KeyError:
            errores.append("La actividad seleccionada no es válida.")
            for file in files:
              if(file[file.find("."):] in [".xls",".xlsx",".csv"]):
                os.remove(folder + '/' + file) 
            return render_template('importar.tpl.html',messages=errores,colegios_provincia=colegios_provincia_data,colegios_lima=colegios_lima_data,tipo_actividades=tipo_actividad)

          for file in files:
            print(file + " -- " + archivo_subido)
            if ((file[file.find("."):] == ".xlsx") and (file == archivo_subido)):
              xls_data = pd.read_excel(folder + '/' + file)
              for i in range(0,xls_data.shape[0]):
                #Lo primero es crear al contacto (INICIO CREACION DE CONTACTO)
                try:
                  dni = xls_data['dni'][i]
                except KeyError:
                  if i == 0:
                    r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=delete&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"id":' + str(idActividad) + '}')
                    errores.append("Hay un error en el archivo importado: No es un archivo válido o no se encuentra el campo de DNI")
                  else:
                    errores.append("Hay un error en el archivo importado: No es correlativo desde el elemento " + str(i))
                  break

                try:
                  celular = '000000000' if pd.isnull(xls_data['celular'][i]) else str(xls_data['celular'][i]).replace('.0','')
                except KeyError:
                  errores.append("Hay un error en el archivo importado: No se encontró el campo 'celular'")
                  r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=delete&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"id":' + str(idActividad) + '}')
                  break

                try:
                  carreras = '-' if pd.isnull(xls_data['carrera'][i]) else xls_data['carrera'][i].split(',')
                except KeyError:
                  errores.append("Hay un error en el archivo importado: No se encontró el campo 'carrera'")
                  r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=delete&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"id":' + str(idActividad) + '}')
                  break

                try:
                  email = '-' if pd.isnull(xls_data['email'][i]) else xls_data['email'][i]
                except KeyError:
                  errores.append("Hay un error en el archivo importado: No se encontró el campo 'email'")
                  r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=delete&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"id":' + str(idActividad) + '}')
                  break

                try:
                  anho_estudios = '-' if pd.isnull(xls_data['soy_escolar'][i]) else xls_data['soy_escolar'][i]
                except KeyError:
                  errores.append("Hay un error en el archivo importado: No se encontró el campo 'soy_escolar'")
                  r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=delete&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"id":' + str(idActividad) + '}')
                  break

                try:
                  tipo_interesado = 'Escolar' if pd.isnull(xls_data['padre_familia'][i]) else 'Padre de Familia / Tutor'
                except KeyError:
                  errores.append("Hay un error en el archivo importado: No se encontró el campo 'padre_familia'")
                  r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=delete&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"id":' + str(idActividad) + '}')
                  break

                print(anho_estudios)
                if ('5' in anho_estudios):
                    anho_estudios = '5to'
                elif ('4' in anho_estudios):
                    anho_estudios = '4to'
                elif ('3' in anho_estudios):
                    anho_estudios = '3ero'
                print(anho_estudios)

                if(pd.isnull(xls_data['dni'][i])):
                  dni = '00000000'
                else:
                  try:
                    dni = str(int(dni))
                  except ValueError:
                    dni = dni  

                if (len(carreras) >= 2):
                  if (carreras[0].upper().lstrip().rstrip() == 'ARTE'):
                    if(len(carreras) == 2):
                      jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre 2","custom_103":dni,"custom_84":celular,"custom_57":"ARTE, MODA Y DISEÑO TEXTIL","custom_52":anho_estudios,"custom_50":tipo_interesado}
                    else:                    
                      jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre 2","custom_103":dni,"custom_84":celular,"custom_57":'ARTE, MODA Y DISEÑO TEXTIL',"custom_58":carreras[2].upper().lstrip().rstrip(),"custom_52":anho_estudios,"custom_50":tipo_interesado}
                  elif (carreras[1].upper().lstrip().rstrip() == 'ARTE'):
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre 2","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().lstrip().rstrip(),"custom_58":'ARTE, MODA Y DISEÑO TEXTIL',"custom_52":anho_estudios,"custom_50":tipo_interesado}
                  else:
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre 2","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().lstrip().rstrip(),"custom_58":carreras[1].upper().lstrip().rstrip(),"custom_52":anho_estudios,"custom_50":tipo_interesado}
                elif (len(carreras) == 1):
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre 2","custom_103":dni,"custom_84":celular,"custom_57":carreras[0].upper().lstrip().rstrip(),"custom_52":anho_estudios,"custom_50":tipo_interesado}
                else:
                    jotason = {"contact_type":"Individual","contact_sub_type":"Interesado_PUCP","display_name":"Interesado sin nombre 2","custom_103":dni,"custom_84":celular,"custom_52":anho_estudios,"custom_50":tipo_interesado}
                
                cadena=json.dumps(jotason, default=str)
                r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)    

                try:
                  id_contacto = json.loads(r.text)['id']
                except KeyError:
                  errores.append("El elemento #" + str(i) + " no se importará por tener un error. Revisar: " + r.text)
                  continue       

                if (email != '-'):
                    jotason = {"contact_id":id_contacto,"email":email}
                    cadena=json.dumps(jotason, default=str)
                    r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Email&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)    
                    print(r.text)

                jotason = {"activity_id":idActividad,"contact_id":id_contacto}
                cadena = json.dumps(jotason,default=str)
                r = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=ActivityContact&action=create&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json=' + cadena)
            else:
              errores.append('El formato del archivo ' + file + ' no es válido. Si no es el archivo que subió, contacte al administrador del sistema.')

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
          f.save(os.path.join(app.config['UPLOAD_FOLDER_CONVERTIR'], filename))

      errores = []
      log = []
      folder = app.config['UPLOAD_FOLDER_CONVERTIR']
      files = listdir(folder)

      for file in files:
        if (file[file.find("."):] == ".csv"):
          csv_data = pd.read_csv(folder + '/' + file)
          
          deleted_columns=['page1_captured','page1_processed','page1_image_file_name','form_page_1_is_scanned_page_number','publication_id',
                 'form_page_id_1','form_password','form_score','soy_escolar_score','celular_score','dni_score','resido_en_score',
                 'padre_familia_score','carrera_score']

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
          try:
            csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1',index=False)
            #csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Hoja 1',index=False)
          except KeyError:
            try:
              deleted_columns=['página1_capturado','page1_processed','page1_image_file_name','formulario_de_la_página_1_es_la_página_escaneada_número','publication_id', 'form_page_id_1','form_password','form_score','soy_escolar_score','celular_score','dni_score','resido_en_score','padre_familia_score','carrera_score']
              csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1',index=False)
              #csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Hoja 1',index=False)
            except KeyError:  
              try: 
                deleted_columns=['page1_captured','page1_processed','page1_image_file_name','form_page_1_is_scanned_page_number','publication_id',
                               'form_page_id_1','form_password','form_score','soy_escolar_score','soy_score','celular_score','dni_score','resido_en_score',
                               'soy_escolar_tipo_score','info_score','carrera_score']
                csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1',index=False)
                #csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Hoja 1',index=False)
              except KeyError:
                deleted_columns=['página1_capturado','page1_processed','page1_image_file_name','formulario_de_la_página_1_es_la_página_escaneada_número','publication_id', 'form_page_id_1','form_password','form_score','soy_escolar_score','soy_score','celular_score','dni_score','resido_en_score','soy_escolar_tipo_score','info_score','carrera_score']
                csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1',index=False)
                #csv_data.drop(labels=deleted_columns,axis=1).to_excel('static/bases/' + nombre,sheet_name='Hoja 1',index=False)

          errores.append('Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>')
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

def encontrar_colegio(id_colegio,lista_colegios):
  for c in lista_colegios:
    if id_colegio == c['contact_id']:
      return c['custom_111'],c['custom_112'],c['custom_113'],c['custom_117'],c['custom_114']  
  return -1,-1,-1,-1,-1

def obtenerDatosContacto(lista_contactos,id_contacto):
  for c in lista_contactos:
    if(c['contact_id'] == id_contacto):
      return c
  return {}

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
  ids_tipos = ['69','68','67','64','63','62','61','60','59','70']
  tipos = ['Charla para Padres','Visita de Investigación','Taller: Camino a la vocación','Una mañana en artes','Charla Institucional','Una mañana en ciencias','Descubre PUCP','Feria Vocacional','Charla informativa','Visita guiada']

  for i in range(0,len(ids_tipos)):
    if (id == ids_tipos[i]):
      return tipos[i]
  return ' '


def buscarEventosParticipante(id_contacto,participantes):
    eventos = []
    for p in participantes:
        if p['contact_id'] == id_contacto:
            eventos.append(p['event_title'])
    return eventos

def buscarActividadContacto(id_contacto,contactos_actividades):
    #actividades = []
    for a in contactos_actividades:
        if a['contact_id'] == id_contacto:
            return a['activity_id']
        
def buscarActividad(id_actividad,actividades):
    #actividades = []
    for a in actividades:
        if a['id'] == id_actividad:
            return a

def buscarColegioEvento(colegio_name,lista_colegios):
    codigo = colegio_name[0:8]
    for c in lista_colegios:
        if(c['custom_111'] == codigo):
            return c['custom_117']
    return ''

def buscarColegioActividad(id_colegio,lista_colegios):
    for c in lista_colegios:
        if(c['id'] == id_colegio):
            return c['organization_name'],c['custom_117']
    return c['id'],c['id']

def obtenerAnhoFin(grado):
    if grado == '5to':
        return '2019'
    if grado == '4to':
        return '2020'
    if grado == '3ero':
        return '2021'
    else:
        return 'Indeterminado'

@mod_main.route('/exportar_menu',methods=['GET'])
def exportar_menu():
  return render_template('exportar_menu.tpl.html')

@mod_main.route('/exportar_general',methods=['GET','POST'])
def exportar_general():
  #Obtener todos los colegios
  r_colegios = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,organization_name,custom_112,custom_111,custom_114,custom_113,custom_117,custom_119","contact_sub_type":["Colegio_Lima","Colegio_Provincias"],"custom_113":["PUCP","No PUCP"],"options":{"limit":0}}')
  lista_colegios = json.loads(r_colegios.text)['values']

  r_carreras = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=OptionValue&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"label,value","option_group_id":"carrera_de_inter_s_4_20180815103733","options":{"limit":0}}')
  lista_carreras = json.loads(r_carreras.text)['values']

  if request.method == 'GET':
    return render_template('exportar_general.tpl.html',colegios=lista_colegios,carreras=lista_carreras)
  else:
    print("Empezó la exportación")

    carrerasSeleccionadas = request.form.getlist('select_carreras')
    print(carrerasSeleccionadas)

    print("Obtendremos a todos los contactos")
    if (len(carrerasSeleccionadas) == 0):
      ###Esta parte se debe actualizar si aumenta la cantidad de Interesados PUCP
      r1 = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_58,custom_52,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":0}}')
      contactos1 = json.loads(r1.text)['values']
      r2 = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":8000}}')
      contactos2 = json.loads(r2.text)['values']
      r3= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":16000}}')
      contactos3 = json.loads(r3.text)['values']
      r4= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":24000}}')
      contactos4 = json.loads(r4.text)['values']
      r5= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":32000}}')
      contactos5 = json.loads(r5.text)['values']
      r6= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":40000}}')
      contactos6 = json.loads(r6.text)['values']
      contactos = contactos1 + contactos2 + contactos3 + contactos4 + contactos5 + contactos6
    else:
      r1_1 = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_58,custom_52,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":0},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos1_1 = json.loads(r1_1.text)['values']
      r1_2 = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":8000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos1_2 = json.loads(r1_2.text)['values']
      r1_3= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":16000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos1_3 = json.loads(r1_3.text)['values']
      r1_4= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":24000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos1_4 = json.loads(r1_4.text)['values']
      r1_5= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":32000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos1_5 = json.loads(r1_5.text)['values']
      r1_6= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":40000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos1_6 = json.loads(r1_6.text)['values']

      r2_1 = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_58,custom_52,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":0},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos2_1 = json.loads(r2_1.text)['values']
      r2_2 = requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":8000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos2_2 = json.loads(r2_2.text)['values']
      r2_3= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":16000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos2_3 = json.loads(r2_3.text)['values']
      r2_4= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":24000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos2_4 = json.loads(r2_4.text)['values']
      r2_5= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":32000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos2_5 = json.loads(r2_5.text)['values']
      r2_6= requests.post('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"first_name,last_name,custom_103,custom_82,custom_81,custom_57,custom_52,,custom_58,email,custom_84","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":8000,"offset":40000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      contactos2_6 = json.loads(r2_6.text)['values']

      contactos = contactos1_1 + contactos1_2 + contactos1_3 + contactos1_4 + contactos1_5 + contactos1_6 + contactos2_1 + contactos2_2 + contactos2_3 + contactos2_4 + contactos2_5 + contactos2_6

    ###Aquí obtenemos a todos los participantes de algún evento PUCP
    r1 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Participant&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"event_id","options":{"limit":15000,"offset":0}}')
    participantes1 = json.loads(r1.text)['values']
    r2 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Participant&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"event_id","options":{"limit":15000,"offset":15000}}')
    participantes2 = json.loads(r2.text)['values']
    r3 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Participant&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"event_id","options":{"limit":15000,"offset":30000}}')
    participantes3 = json.loads(r3.text)['values']
    participantes = participantes1 + participantes2 + participantes3

    ###Aquí obtenemos a todos los interesados en alguna actividad PUCP
    r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"source_contact_id,activity_type_id,activity_date_time,created_date","activity_type_id":{"IN":["Una mañana en ciencias","Una mañana en artes","Charla informativa","Charla Institucional","Visita de Investigación","Taller: Camino a la vocación","Descubre PUCP","Feria vocacional","Charla para padres","Visita Guiada"]},"options":{"limit":0}}')
    actividades = json.loads(r.text)['values']
    id_actividades = []
    for a in actividades:
        id_actividades.append(a['id'])
    cadena = json.dumps(id_actividades,default=str)
    rc = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=ActivityContact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"activity_id":{"IN":'+ cadena +'},"options":{"limit":0}}')  
    contactos_actividades = json.loads(rc.text)['values']

    r_colegios = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,organization_name,custom_112,custom_111,custom_114,custom_113,custom_117,custom_119","contact_sub_type":["Colegio_Lima","Colegio_Provincias"],"options":{"limit":0}}')
    lista_colegios = json.loads(r_colegios.text)['values']

    i=0
    df = pd.DataFrame(columns=['dni','nombres','apellidos','email','celular','carrera1','carrera2','colegio','departamento','anho_fin','evento'])
    for c in contactos:
        #if (str(c['custom_57']) in lst_carreras) or (str(c['custom_58']) in lst_carreras):
            eventos = buscarEventosParticipante(c['id'],participantes)
            if (len(eventos) != 0):
                colegio = buscarColegioEvento(c['custom_81'],lista_colegios)
                df.loc[i] = [c['custom_103'],c['first_name'],c['last_name'],c['email'],c['custom_84'],c['custom_57'],c['custom_58'],c['custom_81'],colegio,c['custom_82'],eventos]
            else:
                id_actividad = buscarActividadContacto(c['id'],contactos_actividades)
                actividad = buscarActividad(id_actividad,actividades)
                if actividad is None:
                    tipo_actividad = '-'
                    colegio = '-'
                    anho_fin = '-'
                    departamento = '-'
                else:
                    id_tipo_actividad = actividad["activity_type_id"]
                    tipo_actividad = cadenaTipoActividad(id_tipo_actividad)
                    colegio,departamento = buscarColegioActividad(actividad['source_contact_id'],lista_colegios)
                    anho_fin = obtenerAnhoFin(c['custom_52'])
                df.loc[i] = [c['custom_103'],c['first_name'],c['last_name'],c['email'],c['custom_84'],c['custom_57'],c['custom_58'],colegio,departamento,anho_fin,tipo_actividad]
            i = i + 1

    nombre = 'outputInteresadosGeneral' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx' 
    #writer = pd.ExcelWriter('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre, engine='xlsxwriter')
    writer = pd.ExcelWriter('static/bases/' + nombre, engine='xlsxwriter')
    workbook = writer.book

    df.to_excel(writer,sheet_name='Hoja 1',index=False,na_rep='')  

    writer.save()
    workbook.close()

    errores=['Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>']

    return render_template('exportar_general.tpl.html',colegios=lista_colegios,carreras=lista_carreras,messages=errores)



@mod_main.route('/exportar',methods=['GET','POST'])
def exportar():
  #Obtener todos los colegios
  r_colegios = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,organization_name,custom_112,custom_111,custom_114,custom_113,custom_117,custom_119","contact_sub_type":["Colegio_Lima","Colegio_Provincias"],"custom_113":["PUCP","No PUCP"],"options":{"limit":0}}')
  #print(r_colegios.text)
  lista_colegios = json.loads(r_colegios.text)['values']

  r_carreras = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=OptionValue&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"label,value","option_group_id":"carrera_de_inter_s_4_20180815103733","options":{"limit":0}}')
  lista_carreras = json.loads(r_carreras.text)['values']

  tipo_actividad = getActivityType()

  if request.method == 'GET':

    return render_template('exportar.tpl.html',colegios=lista_colegios,carreras=lista_carreras,tipo_actividades=tipo_actividad)
  else:
    print("Empezó la exportación")

    fechas = request.form['reservation']
    fechas = fechas.split(' - ')
    fecha1 = fechas[0]
    fecha2 = fechas[1]
    print("La primera fecha es: " + fecha1)
    print("La segunda fecha es: " + fecha2)

    carrerasSeleccionadas = request.form.getlist('select_carreras')
    print(carrerasSeleccionadas)

    actividadesSeleccionadas = request.form.getlist('select_actividades')
    print(actividadesSeleccionadas)

    carreras=['-','ANTROPOLOGÍA','ARQUEOLOGÍA','ARQUITECTURA','ARTE, MODA Y DISEÑO TEXTIL','CIENCIA POLÍTICA Y GOBIERNO','CIENCIAS DE LA INFORMACIÓN','COMUNICACIÓN AUDIOVISUAL','COMUNICACIÓN PARA EL DESARROLLO','CONTABILIDAD','CREACIÓN Y PRODUCCIÓN ESCÉNICA','DANZA','DERECHO','DISEÑO GRÁFICO','DISEÑO INDUSTRIAL','ECONOMÍA','EDUCACIÓN ARTÍSTICA','EDUCACIÓN INICIAL','EDUCACIÓN PRIMARIA','EDUCACIÓN SECUNDARIA','ESCULTURA','ESTADÍSTICA','FILOSOFÍA','FINANZAS','FÍSICA','GEOGRAFÍA Y MEDIO AMBIENTE','GESTIÓN','GRABADO','HISTORIA','HUMANIDADES','INGENIERIA BIOMÉDICA','INGENIERÍA CIVIL','INGENIERÍA DE LAS TELECOMUNICACIONES','INGENIERÍA DE MINAS','INGENIERÍA ELECTRÓNICA','INGENIERÍA GEOLÓGICA','INGENIERÍA INDUSTRIAL','INGENIERÍA INFORMÁTICA','INGENIERÍA MECÁNICA','INGENIERÍA MECATRÓNICA','LINGÜÍSTICA Y LITERATURA','MATEMÁTICAS','MÚSICA','PERIODISMO','PINTURA','PSICOLOGÍA','PUBLICIDAD','QUÍMICA','RELACIONES INTERNACIONALES','SOCIOLOGÍA','TEATRO','INGENIERÍA AMBIENTAL Y SOSTENIBLE','GASTRONOMÍA','OTROS','HOTELERÍA','TURISMO']

    nombre = 'InformacionInteresados' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx' 
    #writer = pd.ExcelWriter('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre, engine='xlsxwriter')
    writer = pd.ExcelWriter('static/bases/' + nombre, engine='xlsxwriter')
    workbook = writer.book

    df = pd.DataFrame(columns=['SEGMENTO','CONDICIÓN','DEPARTAMENTO DE COLEGIO','CÓDIGO DE COLEGIO','NOMBRE COLEGIO','PERFIL','DNI','CORREO ELECTRÓNICO','CELULAR','CARRERA DE INTERÉS 1','CARRERA DE INTERÉS 2','AÑO FIN DE COLEGIO','ACTIVIDAD','FECHA DE ACTIVIDAD'])
    i=0

    ######Aquí empezamos a jalar la info del CRM
    print("Obtendremos todas las actividades")
    if (len(actividadesSeleccionadas) == 0):
      r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"source_contact_id,activity_type_id,activity_date_time,created_date","activity_type_id":{"IN":["Una mañana en ciencias","Una mañana en artes","Charla informativa","Charla Institucional","Visita de Investigación","Taller: Camino a la vocación","Descubre PUCP","Feria vocacional","Charla para padres","Visita Guiada"]},"options":{"limit":0}}')
    else:
      r = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Activity&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"source_contact_id,activity_type_id,activity_date_time,created_date","activity_type_id":{"IN":' + json.dumps(actividadesSeleccionadas) + '},"options":{"limit":0}}')      
    actividades = json.loads(r.text)['values']
    if (len(actividades) == 0):
      errores = ["No hay actividades con los datos seleccionados"]
      return render_template('exportar.tpl.html',colegios=lista_colegios,carreras=lista_carreras,tipo_actividades=tipo_actividad,messages=errores)


    print("Obtendremos a todos los contactos")
    if (len(carrerasSeleccionadas) == 0):
      r_lista_contactos1 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":0}}')
      r_lista_contactos2 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":9000}}')
      r_lista_contactos3 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":18000}}')
      r_lista_contactos4 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":27000}}')
      r_lista_contactos5 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":36000}}')

      lista_contactos1 = json.loads(r_lista_contactos1.text)['values']
      lista_contactos2 = json.loads(r_lista_contactos2.text)['values']
      lista_contactos3 = json.loads(r_lista_contactos3.text)['values']
      lista_contactos4 = json.loads(r_lista_contactos4.text)['values']
      lista_contactos5 = json.loads(r_lista_contactos5.text)['values']

      lista_contactos = lista_contactos1 + lista_contactos2 + lista_contactos3 + lista_contactos4 + lista_contactos5
    else:
      r_lista_contactos1_1 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":0},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos1_2 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":9000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos1_3 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":18000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos1_4 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":27000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos1_5 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":36000},"custom_57":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')

      r_lista_contactos2_1 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":0},"custom_58":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos2_2 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":9000},"custom_58":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos2_3 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":18000},"custom_58":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos2_4 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":27000},"custom_58":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')
      r_lista_contactos2_5 = requests.get('http://ocaicrm.pucp.net/sites/default/modules/civicrm/extern/rest.php?entity=Contact&action=get&api_key=qq2CCwZjhG7fHHKYeH2aYw7F&key=ea6123e5a509396d49292e4d8d522f85&json={"sequential":1,"return":"id,contact_type,custom_103,custom_50,custom_84,email,custom_57,custom_58,custom_52,custom_82","contact_type":"Individual","contact_sub_type":"Interesado_PUCP","options":{"limit":9000,"offset":36000},"custom_58":{"IN":' + json.dumps(carrerasSeleccionadas) + '}}')

      lista_contactos1_1 = json.loads(r_lista_contactos1_1.text)['values']
      lista_contactos1_2 = json.loads(r_lista_contactos1_2.text)['values']
      lista_contactos1_3 = json.loads(r_lista_contactos1_3.text)['values']
      lista_contactos1_4 = json.loads(r_lista_contactos1_4.text)['values']
      lista_contactos1_5 = json.loads(r_lista_contactos1_5.text)['values']

      lista_contactos2_1 = json.loads(r_lista_contactos2_1.text)['values']
      lista_contactos2_2 = json.loads(r_lista_contactos2_2.text)['values']
      lista_contactos2_3 = json.loads(r_lista_contactos2_3.text)['values']
      lista_contactos2_4 = json.loads(r_lista_contactos2_4.text)['values']
      lista_contactos2_5 = json.loads(r_lista_contactos2_5.text)['values']


      lista_contactos = lista_contactos1_1 + lista_contactos1_2 + lista_contactos1_3 + lista_contactos1_4 + lista_contactos1_5 + lista_contactos2_1 + lista_contactos2_2 + lista_contactos2_3 + lista_contactos2_4 + lista_contactos2_5


    print("Obtendremos todos los contactos que están en una actividad")
    contactos_todos = getContactosActividades(actividades)
    for a in actividades:
        fecha = datetime.datetime.strptime(a['activity_date_time'], "%Y-%m-%d %H:%M:%S").strftime('%d/%m/%y')

        fechaF = datetime.datetime.strptime(fecha,"%d/%m/%y")
        fecha1F = datetime.datetime.strptime(fecha1,"%m/%d/%Y")
        fecha2F = datetime.datetime.strptime(fecha2,"%m/%d/%Y")

        if (fechaF >= fecha1F) and (fechaF <= fecha2F):
          print("Cumple con el rango de fechas")
        else:
          continue
          #print("No cumple")

        id_tipo_actividad = a["activity_type_id"]

        try:
          filtro_colegio = request.form['filtro_colegio']
        except KeyError:
          filtro_colegio = '-'

        if filtro_colegio == 'nombre':
          colegiosSeleccionados = request.form.getlist('select_colegios')
          print(colegiosSeleccionados)

          if(len(colegiosSeleccionados) == 0):
            codigo_pucp,nombre_colegio,condicion,dpto_colegio,segmentacion = encontrar_colegio(a['source_contact_id'],lista_colegios)
          else:
            if (a['source_contact_id'] in colegiosSeleccionados):
              codigo_pucp,nombre_colegio,condicion,dpto_colegio,segmentacion = encontrar_colegio(a['source_contact_id'],lista_colegios)
            else:
              continue
        elif filtro_colegio == 'tipo':
          segmentacionSeleccionados = request.form.getlist('select_segmentacion')
          tipo_colegioSeleccionados = request.form.getlist('select_tipo_colegio')
          departamentoSeleccionados = request.form.getlist('select_departamento')

          codigo_pucp,nombre_colegio,condicion,dpto_colegio,segmentacion = encontrar_colegio(a['source_contact_id'],lista_colegios)

          if (len(segmentacionSeleccionados) != 0):
            if (segmentacion not in segmentacionSeleccionados):
              continue

          if (len(tipo_colegioSeleccionados) != 0):
            if(condicion not in tipo_colegioSeleccionados):
              continue

          if (len(departamentoSeleccionados) != 0):
            if(dpto_colegio not in departamentoSeleccionados):
              continue
        else:
          codigo_pucp,nombre_colegio,condicion,dpto_colegio,segmentacion = encontrar_colegio(a['source_contact_id'],lista_colegios)


        if (codigo_pucp == -1):
          print("No se encontró el colegio con id " + a['source_contact_id'])
          continue

        print("Obtendremos a los contactos de la actividad " + a['id'] +" en el colegio: " + nombre_colegio)       
        contactos = getContactosEnActividad(contactos_todos,a['id'])
        for c in contactos:
          id_contacto = c['contact_id']
          print("Obtener los datos de este contacto: " + id_contacto)
          #datos_contacto1,datos_contacto1_5,datos_contacto2,datos_contacto3,datos_contacto4 = obtenerDatosContacto(lista_contactos1,lista_contactos1_5,lista_contactos2,lista_contactos3,lista_contactos4,id_contacto)
          datos_contacto = obtenerDatosContacto(lista_contactos,id_contacto)
          if (datos_contacto == {}):
            print("No hay datos")
            continue

          if(datos_contacto['contact_type'] == 'Individual'):
            id_carrera1 = datos_contacto['custom_57']
            id_carrera2 = datos_contacto['custom_58']
            
            if datos_contacto['custom_52'] == '5to':
              anho_estudios = '2019'
            elif datos_contacto['custom_52'] == '4to':
              anho_estudios = '2020'
            elif datos_contacto['custom_52'] == '3ero':
              anho_estudios = '2021'
            else:
              anho_estudios = '-'

            df.loc[i] = [segmentacion,condicion,dpto_colegio,codigo_pucp,nombre_colegio,datos_contacto['custom_50'],datos_contacto['custom_103'],datos_contacto['email'],datos_contacto['custom_84'],id_carrera1,id_carrera2,anho_estudios,cadenaTipoActividad(id_tipo_actividad),fecha]
            print(df.loc[i])
            i = i + 1
    df.to_excel(writer,sheet_name='Hoja 1',index=False)  

    writer.save()
    workbook.close()

    errores=['Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>']
  
    return render_template('exportar.tpl.html',colegios=lista_colegios,carreras=lista_carreras,tipo_actividades=tipo_actividad,messages=errores)

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


def encontrar_area(especialidad,etapa):
    nombre = etapa + ' EN ' + especialidad
    areas = {'DOCTORADOS':['DOCTORADO EN ANTROPOLOGÍA','DOCTORADO EN ANTROPOLOGÍA, ARQUEOLOGÍA, HISTORIA Y LINGÜÍSTICA ANDINAS','DOCTORADO EN CIENCIA POLÍTICA Y GOBIERNO','DOCTORADO EN CIENCIAS DE LA EDUCACIÓN','DOCTORADO EN ECONOMÍA','DOCTORADO EN ESTUDIOS PSICOANALÍTICOS','DOCTORADO EN FILOSOFÍA','DOCTORADO EN FÍSICA','DOCTORADO EN GESTIÓN ESTRATÉGICA','DOCTORADO EN HISTORIA','DOCTORADO EN LITERATURA HISPANOAMERICANA','DOCTORADO EN INGENIERÍA','DOCTORADO EN MATEMÁTICAS','DOCTORADO EN PSICOLOGÍA','DOCTORADO EN SOCIOLOGÍA'],'ARTES':['MAESTRÍA EN ARTES ESCÉNICAS','MAESTRÍA EN MUSICOLOGÍA'],'ARQUITECTURA':['MAESTRÍA EN ARQUITECTURA Y PROCESOS PROYECTUALES','MAESTRÍA EN ARQUITECTURA, URBANISMO Y DESARROLLO TERRITORIAL SOSTENIBLE'],'CIENCIAS BÁSICAS':['MAESTRÍA EN ESTADÍSTICA','MAESTRÍA EN FÍSICA','MAESTRÍA EN FÍSICA APLICADA','MAESTRÍA EN MATEMÁTICAS','MAESTRÍA EN MATEMÁTICAS APLICADAS','MAESTRÍA EN QUÍMICA'],'CIENCIAS CONTABLES':['MAESTRÍA EN CONTABILIDAD',],'CIENCIAS SOCIALES ':['MAESTRÍA EN ANTROPOLOGÍA','MAESTRÍA EN ANTROPOLOGÍA VISUAL','MAESTRÍA EN CIENCIA POLÍTICA Y RELACIONES INTERNACIONALES','MAESTRÍA EN ECONOMÍA','MAESTRÍA EN GOBIERNO Y POLÍTICAS PÚBLICAS','MAESTRÍA EN SOCIOLOGÍA'],'DERECHO':['MAESTRÍA EN DERECHO BANCARIO Y FINANCIERO','MAESTRÍA EN DERECHO CIVIL','MAESTRÍA EN DERECHO CON MENCIÓN EN POLÍTICA JURISDICCIONAL (PRESENCIAL Y SEMIPRESENCIAL)','MAESTRÍA EN DERECHO CONSTITUCIONAL','MAESTRÍA EN DERECHO DE LA PROPIEDAD INTELECTUAL Y DE LA COMPETENCIA','MAESTRÍA EN DERECHO DE LA EMPRESA','MAESTRÍA EN DERECHO DEL TRABAJO Y DE LA SEGURIDAD SOCIAL','MAESTRÍA EN DERECHO INTERNACIONAL ECONÓMICO','MAESTRÍA EN DERECHO PENAL','MAESTRÍA EN DERECHO PROCESAL','MAESTRÍA EN DERECHO TRIBUTARIO','MAESTRÍA EN INVESTIGACIÓN JURÍDICA'],'EDUCACIÓN':['MAESTRÍA EN DOCENCIA UNIVERSITARIA','MAESTRÍA EN EDUCACIÓN','MAESTRÍA EN ENSEÑANZA DE LA MATEMÁTICAS','MAESTRÍA EN GESTIÓN DE POLÍTICAS Y PROGRAMAS PARA EL DESARROLLO INFANTIL TEMPRANO','MAESTRÍA EN INTEGRACIÓN E INNOVACIÓN EDUCATIVA DE LAS TECNOLOGÍAS DE LA INFORMACIÓN Y LA COMUNICACIÓN (TIC)'],'ESTUDIOS AMBIENTALES':['MAESTRÍA EN BIOCOMERCIO Y DESARROLLO SOSTENIBLE','MAESTRÍA EN DESARROLLO AMBIENTAL','MAESTRÍA EN GESTIÓN DE LOS RECURSOS HÍDRICOS'],'HUMANIDADES':['MAESTRÍA EN ESCRITURA CREATIVA','MAESTRÍA EN FILOSOFÍA','MAESTRÍA EN HISTORIA','MAESTRÍA EN HISTORIA DEL ARTE Y CURADURÍA','MAESTRÍA EN LINGÜÍSTICA','MAESTRÍA EN LITERATURA HISPANOAMERICANA'],'INGENIERÍA':['MAESTRÍA EN ENERGÍA','MAESTRÍA EN GESTIÓN DE LA INGENIERÍA','MAESTRÍA EN INFORMÁTICA','MAESTRÍA EN INGENIERÍA BIOMÉDICA','MAESTRÍA EN INGENIERÍA CIVIL','MAESTRÍA EN INGENIERÍA DE CONTROL Y AUTOMATIZACIÓN','MAESTRÍA EN INGENIERÍA DE LAS TELECOMUNICACIONES','MAESTRÍA EN INGENIERÍA DE SOLDADURA','MAESTRÍA EN INGENIERÍA INDUSTRIAL','MAESTRÍA EN INGENIERÍA MECÁNICA','MAESTRÍA EN INGENIERÍA MECATRÓNICA','MAESTRÍA EN INGENIERÍA Y CIENCIA DE LOS MATERIALES','MAESTRÍA EN INGENIERÍA Y GESTIÓN DE LAS CADENAS DE SUMINISTROS','MAESTRÍA EN PROCESAMIENTO DE SEÑALES E IMÁGENES DIGITALES'],'INTERDISCIPLINARIAS':['MAESTRÍA EN ALTOS ESTUDIOS AMAZÓNICOS','MAESTRÍA EN ANTROPOLOGÍA CON MENCIÓN EN ESTUDIOS ANDINOS','MAESTRÍA EN ARQUEOLOGÍA CON MENCIÓN EN ESTUDIOS ANDINOS','MAESTRÍA EN COMUNICACIONES','MAESTRÍA EN DERECHOS HUMANOS (PRESENCIAL Y SEMIPRESENCIAL)','MAESTRÍA EN DESARROLLO HUMANO: ENFOQUES Y POLÍTICAS','MAESTRÍA EN ESTUDIOS DE GÉNERO','MAESTRÍA EN GERENCIA SOCIAL  (PRESENCIAL Y SEMIPRESENCIAL)','MAESTRÍA EN GESTIÓN Y POLÍTICA DE LA INNOVACIÓN Y LA TECNOLOGÍA','MAESTRÍA EN HISTORIA CON MENCIÓN EN ESTUDIOS ANDINOS','MAESTRÍA EN LINGÜÍSTICA CON MENCIÓN EN ESTUDIOS ANDINOS','MAESTRÍA EN POLÍTICA Y GESTIÓN UNIVERSITARIA','MAESTRÍA EN REGULACIÓN DE LOS SERVICIOS PÚBLICOS','MAESTRÍA EN REGULACIÓN, GESTIÓN Y ECONOMÍA MINERA'],'PSICOLOGÍA':['MAESTRÍA EN COGNICIÓN, DESARROLLO Y APRENDIZAJE','MAESTRÍA EN INTERVENCIÓN CLÍNICA DEL PSICOANÁLISIS','MAESTRÍA EN PSICOLOGÍA','MAESTRÍA EN PSICOLOGÍA COMUNITARIA']}

    for a in areas:
        if (nombre in areas[a]):
            return a
            #print(nombre + "Se encontró en:" + a)
    return "-"


@mod_main.route('/procesarPosgrado',methods=['GET','POST'])
def procesar():
  if request.method == 'GET':
    return render_template('procesar.tpl.html')
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
        if (file[file.find("."):] == ".xls") and (file == filename):
          tablas=pd.read_html(folder+"/"+file)
          tabla=tablas[1]
          tabla.columns = tabla.iloc[0]
          tabla = tabla[1:]
          tam=tabla['CANDIDATO'].count()

          #Eliminar columnas innecesarias
          tabla = tabla.drop('MODALIDAD DE ESPECIALIDAD', 1).drop('INSTRUMENTO QUE PRACTICA', 1).drop('UNIDAD', 1)
          tabla = tabla.drop('SEGUNDA ESPECIALIDAD', 1).drop('SEGUNDA ETAPA', 1).drop('SEGUNDA UNIDAD', 1).drop('ESTADO EXAMEN',1)
          tabla = tabla.drop('DESCRIPCIÓN DE DISCAPACIDAD', 1).drop('CORREO ELECTRÓNICO APODERADO', 1).drop('TELÉFONO APODERADO', 1)

          for i in range(1, tam+1):
            #Homogeneizar con mayúsculas
            try:
              tabla.loc[i, 'DESCRIPCION INSTITUCION'] = tabla['DESCRIPCION INSTITUCION'][i].upper()
            except AttributeError:
              tabla.loc[i, 'DESCRIPCION INSTITUCION'] = '-'

            apellido_p = tabla['PRIMER APELLIDO'][i]
            apellido_m = tabla['SEGUNDO APELLIDO'][i]
            nombres = tabla['NOMBRES'][i]
            tabla.loc[i, 'PRIMER APELLIDO'] = apellido_p + " " + apellido_m + ", " + nombres

          tabla = tabla.drop('SEGUNDO APELLIDO', 1).drop('NOMBRES', 1)
          tabla.rename(columns = {'PRIMER APELLIDO':'NOMBRES COMPLETOS'}, inplace = True)

          aux = tabla.columns.values
          aux[0] = "#"
          aux[9] = "ESPECIALIDAD_REAL"
          aux[51] = "ESPECIALIDAD DE EGRESO"
          tabla.columns = aux

          areas_tematicas=[]
          for i in range(1, tam+1):
              especialidad = tabla['ESPECIALIDAD_REAL'][i]
              etapa = tabla['ETAPA CANDIDATO'][i]
              area_tematica = encontrar_area(especialidad,etapa)
              areas_tematicas.append(area_tematica)  
          tabla['AREA TEMATICA'] = Series(areas_tematicas, index=tabla.index)   

          columns = tabla.columns.values
          aux = []
          i=0
          
          for a in columns:
            if (i == 10):
              aux.append("AREA TEMATICA")
            if (a != "AREA TEMATICA"):
              aux.append(a)
            i = i + 1
          tabla = tabla[aux]
          
          #tabla.to_excel('static/bases/' + file + '.xlsx',sheet_name='Hoja 1')
          tabla.to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + file + '.xlsx',sheet_name='Hoja 1',index=False)

          errores.append('Desde aquí puede descargar el archivo revisado, <a href="/static/bases/'+ file +'.xlsx">Descargar archivo en XLSX</a>')

    return render_template('procesar.tpl.html',messages=errores)


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
  lisSedesProv=['LIMA','AREQUIPA','AYACUCHO','CAJAMARCA','CUSCO','LAMBAYEQUE','JUNIN','HUANUCO','ANCASH','ICA','LA LIBERTAD','UCAYALI','SAN MARTIN','LORETO','PUNO']
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

          cuadro1=pd.DataFrame(columns=['CODIGO','FECHA_REGISTRO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','ANHO_FIN','COLEGIO']) ###AÑO FIN
          cuadro2=pd.DataFrame(columns=['CODIGO','FECHA_REGISTRO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','EDAD','ANHO_NACIMIENTO']) ###EDAD
          cuadro3=pd.DataFrame(columns=['CODIGO','FECHA_REGISTRO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','SEDE','DPTO_RESIDENCIA']) ###SEDE
          cuadro5=pd.DataFrame(columns=['CODIGO','FECHA_REGISTRO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','DISCAPACIDAD','DESCR_DISCAPACIDAD']) ###DISCAPACIDAD
          cuadro6=pd.DataFrame(columns=['CODIGO','FECHA_REGISTRO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','COD_COLEGIO','COLEGIO']) ###SIN INFO DE COLEGIO
          cuadro7=pd.DataFrame(columns=['CODIGO','FECHA_REGISTRO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','PAGO']) ###POSTULANTES PAGO NO
          cuadro8=pd.DataFrame(columns=['CODIGO','FECHA_REGISTRO','DNI','NOMBRES','APELLIDOS','PROCESO','ESTADO','PAGO']) ###CANDIDATOS PAGO SI

          cuadro4=pd.DataFrame(columns=['DNI1','DNI2','DNI3','DNI5','DNI6','DNI7','DNI8'])

          cont1=1 ###AÑO FIN
          cont2=1 ###EDAD
          cont3=1 ###SEDE
          cont5=1 ###DISCAPACIDAD
          cont6=1 ###SIN INFO DE COLEGIO
          cont7=1 ###POSTULANTES PAGO NO
          cont8=1 ###CANDIDATOS PAGO SI

          """if not (os.path.isfile('Lista.xlsx')):
            writer=pd.ExcelWriter('Lista.xlsx',engine='xlsxwriter')
            cuadro4.to_excel(writer,sheet_name='Hoja 1')
            workbook1=writer.book
            writer.save()
          
          lista=pd.read_excel('Lista.xlsx')
          print(lista)
         """
          contDni1= 0#lista["DNI1"].count()
          contDni2= 0#lista['DNI2'].count()
          contDni3= 0#lista['DNI3'].count()
          contDni5= 0#lista['DNI5'].count()
          contDni6= 0#lista['DNI6'].count()
          contDni7= 0#lista['DNI7'].count()
          contDni8= 0#lista['DNI8'].count()
        
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
              elif sede=='HUARAZ':
                  sede='ANCASH'
              elif sede=='CHICLAYO':
                  sede='LAMBAYEQUE'
              elif sede=='PUCALLPA':
                  sede='UCAYALI'
              elif sede=='TARAPOTO':
                  sede='SAN MARTIN'
              
              if depResidencia == 'CALLAO':
                  depResidencia = 'LIMA'
              
              ##Verificamos Año fin
              if len(yearFin)!=4 and yearFin != '-':
                 # if yaFueRevisado(contDni1Or,1,dni,lista)==False:
                 if 1:
                      print("Se agregó a columna 1 y cuadro 1")
                      cuadro1.at[cont1,'DNI']=dni
                      cuadro1.at[cont1,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro1.at[cont1,'FECHA_REGISTRO'] = tabla['FECHA REGISTRO'][i]

                      cuadro1.at[cont1,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro1.at[cont1,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro1.at[cont1,'PROCESO']=tabla['PROCESO'][i]
                      cuadro1.at[cont1,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro1.at[cont1,'ANHO_FIN']=yearFin
                      cuadro1.at[cont1,'COLEGIO']=tabla['DESCRIPCION COLEGIO'][i]
                      #lista.at[contDni1,'DNI1']=dni
                      contDni1+=1
                      cont1+=1
                      ##Hacer que el programa bote como resultado que se debe verificar año fin

              ##Verificamos edad
              try:
                edad=int(tabla['EDAD'][i])
                if (edad>19 and edad<=13):
                  flag_edad = True;
              except ValueError:
                edad = '-'
                flag_edad = True;
              
              if flag_edad:
                #print("Se agregó a columna 2 y cuadro 2")
                cuadro2.at[cont2,'DNI']=tabla['DNI'][i]
                cuadro2.at[cont2,'CODIGO']=tabla['CANDIDATO'][i]
                cuadro2.at[cont2,'FECHA_REGISTRO'] = tabla['FECHA REGISTRO'][i]
                cuadro2.at[cont2,'NOMBRES']=tabla['NOMBRES'][i]
                cuadro2.at[cont2,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                cuadro2.at[cont2,'PROCESO']=tabla['PROCESO'][i]
                cuadro2.at[cont2,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                cuadro2.at[cont2,'EDAD']=edad
                cuadro2.at[cont2,'ANHO_NACIMIENTO']=tabla['FECHA NACIMIENTO'][i]
                #lista.at[contDni2,'DNI2']=dni
                contDni2+=1
                cont2+=1
                #Hacer que el programa bote como resultado que se debe verificar edad
                  
              ##Verificamos discapacidad
              if discapacidad=='Si' or discapacidad=='SI':
                  if 1:
                      #print("Se agregó a columna 5 y cuadro 5")
                      cuadro5.at[cont5,'DNI']=tabla['DNI'][i]
                      cuadro5.at[cont5,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro5.at[cont5,'FECHA_REGISTRO'] = tabla['FECHA REGISTRO'][i]
                      cuadro5.at[cont5,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro5.at[cont5,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro5.at[cont5,'PROCESO']=tabla['PROCESO'][i]
                      cuadro5.at[cont5,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro5.at[cont5,'DISCAPACIDAD']=discapacidad
                      cuadro5.at[cont5,'DESCR_DISCAPACIDAD']=tabla['DESCRIPCIÓN DE DISCAPACIDAD'][i]
                      #lista.at[contDni5,'DNI5']=dni
                      contDni5+=1
                      cont5+=1
                  ##Hacer que el programa bote como resultado que se debe verificar la discapacidad

              ##Verificamos sede  
              if sede != depResidencia and depResidencia in lisSedesProv and sede != "-":
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if int(yearFin)>=2019:                     #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 3 y cuadro 3")
                      cuadro3.at[cont3,'DNI']=tabla['DNI'][i]
                      cuadro3.at[cont3,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro3.at[cont3,'FECHA_REGISTRO'] = tabla['FECHA REGISTRO'][i]
                      cuadro3.at[cont3,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro3.at[cont3,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro3.at[cont3,'PROCESO']=tabla['PROCESO'][i]
                      cuadro3.at[cont3,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro3.at[cont3,'SEDE']=tabla['SEDE'][i]
                      cuadro3.at[cont3,'DPTO_RESIDENCIA']=tabla['DEPARTAMENTO COLEGIO'][i]
                      #lista.at[contDni3,'DNI3']=dni
                      contDni3+=1
                      cont3+=1
                  ##hacer que el programa bote como resultado que se debe hacer cambio de sede     
                  
              ##Verificamos información escolar  
              if estado == 'POSTULANTE' and pd.isnull(tabla['COLEGIO'][i]):
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if 1:
                      #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 6 y cuadro 6")
                      cuadro6.at[cont6,'DNI']=tabla['DNI'][i]
                      cuadro6.at[cont6,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro6.at[cont6,'FECHA_REGISTRO'] = tabla['FECHA REGISTRO'][i]
                      cuadro6.at[cont6,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro6.at[cont6,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro6.at[cont6,'PROCESO']=tabla['PROCESO'][i]
                      cuadro6.at[cont6,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro6.at[cont6,'COD_COLEGIO']=tabla['COLEGIO'][i]
                      cuadro6.at[cont6,'COLEGIO']=tabla['DESCRIPCION COLEGIO'][i]
                      #lista.at[contDni6,'DNI6']=dni
                      contDni6+=1
                      cont6+=1
                  ##hacer que el programa bote como resultado que se debe hacer verificacion de informacion escolar
                  
              ##Verificamos si es POSTULANTE con pago NO  
              if estado == 'POSTULANTE' and tabla['¿PAGO?'][i] == 'No':
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if 1:
                      #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 7 y cuadro 7")
                      cuadro7.at[cont7,'DNI']=tabla['DNI'][i]
                      cuadro7.at[cont7,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro7.at[cont7,'FECHA_REGISTRO'] = tabla['FECHA REGISTRO'][i]
                      cuadro7.at[cont7,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro7.at[cont7,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro7.at[cont7,'PROCESO']=tabla['PROCESO'][i]
                      cuadro7.at[cont7,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro7.at[cont7,'PAGO']=tabla['¿PAGO?'][i]
                      #lista.at[contDni7,'DNI7']=dni
                      contDni7+=1
                      cont7+=1
                  ##hacer que el programa bote como resultado que se debe hacer una verificacion de pago
              
              ##Verificamos si es CANDIDATO con pago SI  
              if estado == 'CANDIDATO' and tabla['¿PAGO?'][i] == 'SI':
                  #print("El dni " + dni + " será grabado en cuadro 3 si no está en lista")
                  if 1:
                      #print("El dni " + dni + " no está en la lista. Agregar al cuadro 3")
                      #print("Se agregó a columna 7 y cuadro 7")
                      cuadro8.at[cont8,'DNI']=tabla['DNI'][i]
                      cuadro8.at[cont8,'CODIGO']=tabla['CANDIDATO'][i]
                      cuadro8.at[cont8,'FECHA_REGISTRO'] = tabla['FECHA REGISTRO'][i]
                      cuadro8.at[cont8,'NOMBRES']=tabla['NOMBRES'][i]
                      cuadro8.at[cont8,'APELLIDOS']=tabla['PRIMER APELLIDO'][i] + ' ' + tabla['SEGUNDO APELLIDO'][i]
                      cuadro8.at[cont8,'PROCESO']=tabla['PROCESO'][i]
                      cuadro8.at[cont8,'ESTADO']=tabla['ESTADO CANDIDATO'][i]
                      cuadro8.at[cont8,'PAGO']=tabla['¿PAGO?'][i]
                      #lista.at[contDni8,'DNI8']=dni
                      contDni8+=1
                      cont8+=1
                  ##hacer que el programa bote como resultado que se debe hacer una verificacion de pago
              
          nombre_reporte = 'ReporteValidacion' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx'
          #writer1=pd.ExcelWriter('static/validacion/'+nombre_reporte,engine='xlsxwriter')
          writer1=pd.ExcelWriter('/var/www/herramientas-ocai/interfazOCAICRM/static/validacion/' + nombre_reporte,engine='xlsxwriter')
          cuadro1.to_excel(writer1,sheet_name='Año Fin Incorrecto')
          cuadro2.to_excel(writer1,sheet_name='Edades')
          cuadro3.to_excel(writer1,sheet_name='Sede')
          cuadro5.to_excel(writer1,sheet_name='Discapacidad')
          cuadro6.to_excel(writer1,sheet_name='Sin información Escolar')
          cuadro7.to_excel(writer1,sheet_name='POSTULANTES pago NO')
          cuadro8.to_excel(writer1,sheet_name='CANDIDATOS pago SI')
          workbook1=writer1.book
          writer1.save()
          # writer=pd.ExcelWriter('Lista.xlsx',engine='xlsxwriter')
          # lista.to_excel(writer,sheet_name='Hoja 1')
          # writer.save()        
  errores.append('Desde aquí puede descargar el archivo revisado, <a href="/static/validacion/'+ nombre_reporte +'">Descargar archivo en XLSX</a>')
  return render_template('verificaciones.tpl.html',messages=errores)


def inicializar_arreglo(tam,value):
    arr = [value] * tam
    return arr

def imprimir_aulas(arr):
    x = len(arr)
    count = 0
    for a in arr:
        count = count + 1
        if(count == x):
            print(str(a))
        else:
            print(str(a) +  " + ", end = '')
            
def cadena_aulas(arr):
    x = len(arr)
    count = 0
    string=''
    for a in arr:
        count = count + 1
        if(count == x):
            string = string + str(a)
            #print(string)
        else:
            string = string + str(a) +  " + "
            #print(string)
    return string


@mod_main.route('/simulacion-aulas',methods=['GET','POST'])
def simulacion_aulas():
  if request.method == 'GET':
    errores = ['Descarga el formato de postulantes, <a href="/static/formato/'+ 'FORMATO_AULAS.xlsx' +'">Descargar el formato</a>']

    return render_template('simulador_aulas.tpl.html',messages=errores)
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
        if (file[file.find("."):] == ".xlsx") and (file == filename):
          postulantes_data = pd.read_excel(folder + '/' + file)
          columns = list(postulantes_data.columns.values) 
          for i in range(4,len(postulantes_data.index)):
            if (postulantes_data[columns[1]][i] == 'TOTAL'):
              break
            else:
              flag=0
              print("Trabajando en sede: " + postulantes_data['Unnamed: 1'][i] + "...")
              total_ciencias = int(postulantes_data['Unnamed: 2'][i]) + (postulantes_data['Unnamed: 3'][i])
              total_letras = int(postulantes_data['Unnamed: 4'][i])
              cap_aula_ciencias = int(postulantes_data['Unnamed: 8'][i]) 
              cap_aula_letras = int(postulantes_data['Unnamed: 9'][i]) 
                      
              aux_ciencias = int(round(total_ciencias / cap_aula_ciencias,0))
              if(aux_ciencias == 0):
                aux_ciencias = 1
              rest = total_ciencias - (aux_ciencias * cap_aula_ciencias)
              if( rest >= 12 ):
                aux_ciencias = aux_ciencias + 1
                flag = 1
                        
              dist = total_ciencias // aux_ciencias
              arr_ciencias = inicializar_arreglo(aux_ciencias,dist)
              rest = total_ciencias % aux_ciencias
                      
              if(rest > 0):
                arr_ciencias[aux_ciencias - 1] = arr_ciencias[aux_ciencias - 1] + rest   
                
              aux_letras = int(round(total_letras / cap_aula_letras,0))
              if(aux_letras == 0):
                aux_letras = 1
              rest = total_letras - (aux_letras * cap_aula_letras)
              if( rest >= 12 ):
                aux_letras = aux_letras + 1
                flag = 1
                      
              dist = total_letras // aux_letras
              arr_letras = inicializar_arreglo(aux_letras,dist)
              rest = total_letras % aux_letras
                      
              if(rest > 0):
                arr_letras[aux_letras - 1] = arr_letras[aux_letras - 1] + rest   
                
              postulantes_data[columns[10]][i] = cadena_aulas(arr_ciencias)
              postulantes_data[columns[11]][i] = cadena_aulas(arr_letras)
              postulantes_data[columns[12]][i] = str(len(arr_letras) + len(arr_ciencias))

                #csv_data.drop(labels=deleted_columns,axis=1).to_excel('/var/www/herramientas-ocai/interfazOCAICRM/static/bases/' + nombre,sheet_name='Hoja 1',index=False)

          nombre = 'SimuladorDeAulas' + datetime.datetime.now().strftime('%d_%m_%y_%H_%M_%S') + '.xlsx'
          #postulantes_data.to_excel("static/bases/" + nombre,header=False,index=False,na_rep='')
          postulantes_data.to_excel("/var/www/herramientas-ocai/interfazOCAICRM/static/bases/" + nombre,header=False,index=False,na_rep='')
          errores.append('Desde aquí puede descargar el archivo convertido, <a href="/static/bases/'+ nombre +'">Descargar archivo en XLSX</a>')

    return render_template('simulador_aulas.tpl.html',messages=errores)