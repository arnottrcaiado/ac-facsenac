#
# Faculdade SENAC - ADS
# IOT e Automação Comercial
# Desenvolvimento de APIs para coleta e tratamento de dados de IOT
#
# Prof. Arnott Ramos Caiado
#
# Criação inicial: out/2021 - abril/2022
# Data atual: fev/2023
# Criação inicial: out/2021
# Data atual: mar/2023
#
# -*- coding: UTF-8 -*-

from flask import Flask, request, render_template
from flask_mail import Mail, Message
from datetime import datetime, date
from random import choice

from flask_sqlalchemy import SQLAlchemy

import os
import time
import json
import tweepy   # biblioteca para envio de mensagens pelo twitter
import pandas as pd
import string
import sys

sys.path.insert(0,'/home/fac')  # define pasta default para arquivos e modulos complementares

import ffac_headers as chaves   # chaves de acesso e autenticação - externas para melhorar segurança

# configurações para uso do twitter
twitter_auth_keys = {
        "consumer_key"        : chaves.c_key,
        "consumer_secret"     : chaves.c_secret,
        "access_token"        : chaves.a_token,
        "access_token_secret" : chaves.a_token_secret
    }

auth = tweepy.OAuthHandler(
            twitter_auth_keys['consumer_key'],
            twitter_auth_keys['consumer_secret']
        )
auth.set_access_token(
            twitter_auth_keys['access_token'],
            twitter_auth_keys['access_token_secret']
        )
api = tweepy.API(auth)

# chaves de segurança para API
api_key_post = chaves.api_key_post
api_header_key = chaves.api_header_key

os.environ["TZ"] = "America/Recife"
time.tzset()

arquivos = {'A11': '/home/fac/mysite/dados/leituras_a11.csv', 'A22': '/home/fac/mysite/dados/leituras_a22.csv' }

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://prodlattes:lattes20@prodlattes.mysql.pythonanywhere-services.com/prodlattes$docentes'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://fac:acdadosfac@fac.mysql.pythonanywhere-services.com/fac$Dados'
db = SQLAlchemy(app)

class Dados(db.Model):
    seq = db.Column(db.Integer, primary_key=True)
    iden = db.Column( db.String(5) )
    data = db.Column( db.Date )
    hora = db.Column( db.String(5) )
    medida = db.Column( db.Float )


    def to_json(self):
        return {"seq": self.seq,
        "id": self.iden,
        "data": self.data,
        "hora": self.hora,
        "medida": self.medida}


# configuracao para envio de email
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = chaves.mail_username
app.config['MAIL_PASSWORD'] = chaves.mail_password # senha de app https://support.google.com/accounts/answer/185833?hl=pt-BR
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

# endpoint para visualizar ( HTML ) estado atual / ultima leitura de temperatura e umidade
# http://fac.pythonanywhere.com/mostra
@app.route('/mostra', methods=['GET'])
def inicio():
    s1, d1, h1, t1, u1 = ultimosDados(arquivos['A11'])
    s2, d2, h2, t2, u2 = ultimosDados(arquivos['A22'])
    return render_template( 'dash_temp.html', s1= s1, s2=s2, t1=t1, t2=t2, u1=u1, u2=u2, d1=d1, d2=d2, h1=h1, h2=h2)
# ------------------------------------------------------------------------------------------------------------------

# endpoint para visualizar ( HTML ) estado atual / ultima leitura de temperatura e umidade e banco de dados
# http://fac.pythonanywhere.com/mostradb
@app.route('/mostradb', methods=['GET'])
def mostradb():
    s1, d1, h1, t1, u1 = ultimosDadosdb(id='ID01')
    s2, d2, h2, t2, u2 = ultimosDadosdb(id='NTCK1')
    return render_template( 'dash_temp_db.html', s1= s1, s2=s2, t1=t1, t2=t2, u1=u1, u2=u2, d1=d1, d2=d2, h1=h1, h2=h2)
# ------------------------------------------------------------------------------------------------------------------


def ultimosDadosdb( id ):
    dadosSelect = Dados.query.filter( Dados.iden.like (id) )
    dados = []
    for d in dadosSelect :
        dados.append ({'N': d.seq, 'Id': d.iden, 'Dt': str(d.data), 'Hr': str(d.hora), 'M': d.medida})
    dRet= dados[-1]
    return dRet['Id'], dRet['Dt'], dRet['Hr'], dRet['M'], dRet['M']


#endpoint para receber dados do Arduino ( POST ) e inserir em banco de dados
# http://fac.pythonanywhere.com/dbinsert
@app.route('/dbinsert', methods=['GET','POST'])
def dbinsert():
    if request.method == 'POST' :
        p_id=request.form.get('id')
        p_temp=request.form.get('medida')
        p_stat=request.form.get('status')
        # p_umid=request.form.get('umidade')

        iden = p_id
        medida = p_temp
        data = str(date.today())
        hora_atual = str(datetime.time(datetime.now()))
        hora_atual = hora_atual[0:5]
        hora = hora_atual

        if int(p_stat)+1 != 0 :
            dadosRecebidos = Dados( iden = iden, medida = medida, data = data, hora = hora )
            db.session.add( dadosRecebidos )
            db.session.commit()
            return json.dumps( {'Id': iden, 'Medida': medida } )
        else :
            return json.dumps( {'Id': iden, 'Medida': medida , "Stat:" : "NoWrite"} )

    elif request.method == 'GET' :
        totalDados = Dados.query.all()
        dados = []
        for d in totalDados :
            dados.append ({'N': d.seq, 'Id': d.iden, 'Dt': str(d.data), 'Hr': str(d.hora), 'M': d.medida})
        if request.args.get('query') == 'all':
            return json.dumps( dados )
        elif request.args.get('query') == 'last' :
            return json.dumps ( dados[-1] )
        else :
            return json.dumps ({ "Leituras": len(dados)} )


# enbdpoint para receber dados do ARDUINO ( POST ) e gravar em arquivo
# https://fac.pythonanywhere.com/datalog
@app.route('/datalog', methods=['GET','POST'])
def datalog():
    if request.headers.get('Authorization-Token') != api_header_key :
        # falha da autenticação do cabeçalho
        return json.dumps({'Datalog':'Erro de authenticação Header'}, ensure_ascii=False )
    else :
        p_chave=request.form.get('api_key')
        if p_chave != api_key_post :
            # falha da autenticação do cabeçalho
            return json.dumps({'Datalog':'Erro de authenticação modulo'}, ensure_ascii=False )
        else :
            p_id=request.form.get('id')
            p_temp=request.form.get('medida')
            p_stat=request.form.get('status')
            p_umid=request.form.get('umidade')
            if  int(p_stat) != 0 : # houve mudanças, gravar dados
                grava_dados( "/home/fac/mysite/dados/leituras.csv", p_id, p_temp, p_umid, p_stat )

            if str(p_id) in arquivos :
                grava_dados( arquivos[p_id], p_id, p_temp, p_umid, p_stat )

            return json.dumps({"Data":'ok', 'Id':str(p_id),'Temperatura': str(p_temp), 'Umidade':str(p_umid), 'Stat':str(p_stat)}, ensure_ascii=False )
# -----------------------------------------------------------------------------------------------------------------------------------------------------

# funcao para gravar dados.
# Parametros: id, temperatura estatus
def grava_dados( arq, ident , temp, umid,  stat ) :
    data_atual = str(date.today())
    hora_atual = str(datetime.time(datetime.now()))
    hora_atual = hora_atual[0:5]
    linha = str(ident)+","+data_atual+','+hora_atual+','+str(temp)+','+str(stat)+','+str(umid)+"\n"
    arquivo = open( arq , 'a' )
    arquivo.write( linha )
    arquivo.close()

# funcao para mostrar ultimos dados lidos
def ultimosDados( arq ) :
    df=pd.read_csv( arq )
    sensor = df.loc[len(df)-1, 'id']
    temp = df.loc[len(df)-1, 'temperatura']
    umid = df.loc[len(df)-1, 'umidade']
    data_leitura = df.loc[len(df)-1, 'data']
    hora_leitura = df.loc[len(df)-1, 'hora']
    return sensor, data_leitura, hora_leitura, str(temp), str(umid)
# --------------------------------------------------------------------

# endpoint para enviar um tuite
# https://fac.pythonanywhere.com.br/tuite?mensagem=sua mensagem
@app.route('/tuite')
def twitt():
    mensagem = request.args.get('mensagem')
    data_atual = str(date.today())
    hora_atual = str(datetime.time(datetime.now()))
    hora_atual = hora_atual[0:5]
    tweet = data_atual +" "+hora_atual+ mensagem
    api.update_status(tweet)
    return " Mensagem enviada para Twitter : "+ tweet
# ----------------------------------------------------------------------

# endpoint para enviar um email
# https://fac.pythonanywhere.com.br/email?destino=email@gmail.com&assunto=seu assunto&mensagem=sua mensagem
@app.route("/email")
def enviaMensagem():
    destino = request.args.get('destino')
    if destino == None :
        destino = request.form.get('destino')
    mensagem = request.args.get('mensagem')
    if mensagem == None :
        mensagem = request.form.get('mensagem')
    assunto = request.args.get('assunto')
    if assunto == None :
        assunto = request.form.get('assunto')

    if destino == None :
        return json.dumps({'Envia':'Erro - Sem destino'})
    if mensagem == None :
        return json.dumps({'Envia':'Erro - Sem Mensagem'})
    if assunto == None :
        return json.dumps({'Envia':'Erro - Sem Assunto'})

    # mensagem completa, enviar email
    msg = Message( assunto, sender = chaves.mail_username, recipients = [destino])
    msg.body = mensagem
    mail.send(msg)
    return json.dumps({'Mensagem':'Enviada email:'+mensagem})
# -------------------------------------------------------------------------------------------------------------

# endpoint para gerar nova credencial de acesso
# https://fac.pythonanywhere.com.br/credencial?destino=seuemail@gmail.com
@app.route("/credencial")
def geraCredencial():
    destino = request.args.get('destino')
    if destino != None :
        msg = Message('Atualização de Acesso', sender = chaves.mail_username, recipients = [destino])
        msg.body = "\n Olá - Mensagem gerada pelo i9iapp.\n Esta é sua nova credencial : \n\n"+" "+gerasenha()
        # neste ponto, deveriamos inserir uma funcao para guardar a credencial em um banco de dados
        # associado ao usuario
        mail.send(msg)
        return json.dumps({'Credencial':'Enviada'})
    else :
        return json.dumps({'Credencial':'Sem destino'})

def gerasenha():
    tamanho = 20
    valores = string.ascii_lowercase + string.digits +string.ascii_uppercase
    senha = ''
    for i in range(tamanho):
        senha += choice(valores)

    return senha
