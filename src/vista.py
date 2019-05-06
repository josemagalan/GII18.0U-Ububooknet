# -*- coding: utf-8 -*-
import os
from flask import render_template, Flask, request, url_for, redirect, json, send_file, make_response, g
from src import modelo as mod
from src import config as cfg
from bs4 import BeautifulSoup
from flask_babel import Babel, gettext


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = cfg.upload_folder
app.config['BABEL_TRANSLATION_DIRECTORIES'] = cfg.translations_folder

babel = Babel(app)

m = mod.modelo.getInstance()

@babel.localeselector
def get_locale():
    if(m.getIdioma() == None):
        m.setIdioma(request.accept_languages.best_match(cfg.LANGUAGES.keys()))
    return m.getIdioma()

@app.before_request
def before_request():
    g.locale = get_locale()

@app.route('/', methods=["GET","POST"])
def index():
    error = ''
    if request.method == "POST":
        fich = request.files["btn btn-selepub"]
        fullpath = os.path.join(app.config['UPLOAD_FOLDER'], fich.filename)
        fich.save(fullpath)
        if(m.esEpub(fullpath)):
            m.setFichero(fullpath)
            m.obtTextoEpub()
            m.vaciarDiccionario()
            return redirect(url_for('dictaut'))
        else: 
            error = gettext("La ruta indicada no contiene un fichero epub")
            return render_template('index.html', error = error)
    return render_template('index.html')

@app.route('/Dicts-Automaticos/', methods=["GET", "POST"])
def dictaut():
    msg = ''
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        if("btn btn-vacdit"  in request.form):
            m.vaciarDiccionario()
        if("btn btn-creadict" in request.form):
            m.crearDict()
            msg = "Diccionario creado con éxito"
        elif("btn btn-impdict" in request.form):
            return redirect(url_for('impdict'))
        elif("btn btn-obtdict" in request.form):
            return redirect(url_for('obtdict'))
    return render_template('dictaut.html', msg = msg)

@app.route('/Dicts-Automaticos/Importar-Dict/', methods=["GET","POST"])
def impdict():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        fich = request.files["btn btn-selcsv"]
        fullpath = os.path.join(app.config['UPLOAD_FOLDER'], fich.filename)
        fich.save(fullpath)
        m.importDict(fullpath)
    return render_template('impdict.html')

@app.route('/Dicts-Automaticos/Obtener-Dict/', methods=["GET","POST"])
def obtdict():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        url = request.form['txt txt-url']
        m.scrapeWiki(url)
    return render_template('obtdict.html')

@app.route('/Modificar-Diccionario/', methods=["GET", "POST"])   
def moddict():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        ajax = request.get_json()
        if(ajax != None):
            m.prepararRed()
            return json.dumps("True")
        if("btn btn-newpers" in request.form):
            return redirect(url_for('newpers'))
        elif("btn btn-delpers" in request.form):
            return redirect(url_for('delpers'))
        elif("btn btn-joinpers" in request.form):
            return redirect(url_for('joinpers'))
        elif("btn btn-newrefpers" in request.form):
            return redirect(url_for('newrefpers'))
        elif("btn btn-delrefpers" in request.form):
            return redirect(url_for('delrefpers'))
        elif("btn btn-modid" in request.form):
            return redirect(url_for('modidpers'))
        elif("btn btn-expdict" in request.form):
            filename = app.config['UPLOAD_FOLDER']+"\\DiccionarioPersonajes.csv"
            m.exportDict(filename)
            return send_file(filename, mimetype='text/csv', attachment_filename=gettext("DiccionarioPersonajes.csv"), as_attachment=True)
    return render_template('moddict.html', pers = m.getPersonajes())

@app.route('/Modificar-Diccionario/Anadir-Personaje/', methods=["GET", "POST"])    
def newpers():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        idperso = request.form['txt txt-idpers']
        perso = request.form['txt txt-nombrepers']
        m.anadirPersonaje(idperso,perso)
    return render_template('newpers.html', pers = m.getPersonajes())

@app.route('/Modificar-Diccionario/Eliminar-Personaje/', methods=["GET", "POST"])    
def delpers():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        ajax = request.get_json()
        if(ajax != None):
            m.eliminarListPersonajes(ajax)
    return render_template('delpers.html', pers = m.getPersonajes())

@app.route('/Modificar-Diccionario/Juntar-Personajes/', methods=["GET", "POST"])    
def joinpers():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        ajax = request.get_json()
        if(ajax != None):
            m.juntarListPersonajes(ajax)
    return render_template('joinpers.html', pers = m.getPersonajes())
   
@app.route('/Modificar-Diccionario/Nueva-Referencia/', methods=["GET", "POST"])    
def newrefpers():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        idp = request.form['txt txt-idpers']
        ref = request.form['txt txt-refpers']
        m.anadirReferenciaPersonaje(idp,ref)
    return render_template('newrefpers.html', pers = m.getPersonajes())

@app.route('/Modificar-Diccionario/Eliminar-Referencia/', methods=["GET", "POST"])    
def delrefpers():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        ajax = request.get_json()
        if(ajax != None):
            if(ajax == 'id'):
                return orden(render_template('delrefpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0])}))
            elif(ajax == 'idrev'):
                return orden(render_template('delrefpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0] ,reverse=True)}))
            elif(ajax == 'apa'):
                return orden(render_template('delrefpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones())}))
            elif(ajax == 'aparev'):
                return orden(render_template('delrefpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones(), reverse=True)}))
            else:
                m.eliminarListRefs(ajax)
    return render_template('delrefpers.html', pers = m.getPersonajes())

@app.route('/Modificar-Diccionario/Cambiar-Identificador/', methods=["GET", "POST"])
def modidpers():
    if(not m.hayFichero() ):
        return redirect(url_for('index'))
    if request.method == "POST":
        idact = request.form['txt txt-idact']
        newid = request.form['txt txt-newid']
        m.modificarIdPersonaje(idact,newid)
    return render_template('modidpers.html', pers = m.getPersonajes())
    
@app.route('/Parametros/', methods=["GET", "POST"])
def params():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        apar = request.form['txt txt-apar']
        dist = request.form['txt txt-dist']
        caps = False
        if("cbx cbx-capitulos"  in request.form):
            caps = True
        m.generarGrafo(int(dist),int(apar),caps)           
        return redirect(url_for('red'))
    return render_template('params.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones(), reverse=True)})

@app.route('/Red/', methods=["GET", "POST"])
def red():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    jsonred = m.visualizar()
    if request.method == "POST":
        if("btn btn-expgml" in request.form):
            filename = app.config['UPLOAD_FOLDER']+"\\GrafoGenerado.gml"
            m.exportGML(filename)
            return send_file(filename, mimetype='text/gml', attachment_filename=gettext("GrafoGenerado.gml"), as_attachment=True)
        elif("btn btn-expgexf" in request.form):
            filename = app.config['UPLOAD_FOLDER']+"\\GrafoGenerado.gexf"
            m.exportGEXF(filename)
            return send_file(filename, mimetype='text/gexf', attachment_filename=gettext("GrafoGenerado.gexf"), as_attachment=True)
        elif("btn btn-expnet" in request.form):
            filename = app.config['UPLOAD_FOLDER']+"\\GrafoGenerado.net"
            m.exportPajek(filename)
            return send_file(filename, mimetype='text/net', attachment_filename=gettext("GrafoGenerado.net"), as_attachment=True)
    return render_template('red.html', jsonred = jsonred, config = m.getConfigVis())

@app.route('/Informe/', methods=["GET", "POST"])
def informe():
    if(not m.hayFichero()):
        return redirect(url_for('index'))
    if request.method == "POST":
        print()
    return render_template('informe.html')

@app.route('/Ordenar/', methods=["GET", "POST"])
def ordenar():
    if request.method == "POST":
        ajax = request.get_json()
        if(ajax != None):
            if(ajax == 'id'):
                return orden(render_template('moddict.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0])}))
            elif(ajax == 'idrev'):
                return orden(render_template('moddict.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0] ,reverse=True)}))
            elif(ajax == 'apa'):
                return orden(render_template('moddict.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones())}))
            elif(ajax == 'aparev'):
                return orden(render_template('moddict.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones(), reverse=True)}))

@app.route('/Ordenar-Id-Cbx-Del/', methods=["GET", "POST"])
def ordenaridcbxdel():
    if request.method == "POST":
        ajax = request.get_json()
        if(ajax != None):
            if(ajax == 'id'):
                return orden(render_template('delpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0])}))
            elif(ajax == 'idrev'):
                return orden(render_template('delpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0] ,reverse=True)}))
            elif(ajax == 'apa'):
                return orden(render_template('delpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones())}))
            elif(ajax == 'aparev'):
                return orden(render_template('delpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones(), reverse=True)}))      

@app.route('/Ordenar-Id-Cbx-Join/', methods=["GET", "POST"])
def ordenaridcbxjoin():
    if request.method == "POST":
        ajax = request.get_json()
        if(ajax != None):
            if(ajax == 'id'):
                return orden(render_template('joinpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0])}))
            elif(ajax == 'idrev'):
                return orden(render_template('joinpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[0] ,reverse=True)}))
            elif(ajax == 'apa'):
                return orden(render_template('joinpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones())}))
            elif(ajax == 'aparev'):
                return orden(render_template('joinpers.html', pers = {k: v for k, v in sorted(m.getPersonajes().items(), key=lambda x: x[1].getNumApariciones(), reverse=True)}))      

def orden(html):
    cont = BeautifulSoup(html, "html.parser")
    return json.dumps(str(cont.find(id="Personajes")))

@app.route('/Idioma/', methods=["GET", "POST"])
def idioma():
    if request.method == "POST":
        ajax = request.get_json()
        m.setIdioma(ajax)
        return "true"
    
@app.route('/Guardar-Config/', methods=["GET", "POST"])
def guardarConfig():
    if request.method == "POST":
        config = request.get_json()
        m.setConfigVis(config['config'])