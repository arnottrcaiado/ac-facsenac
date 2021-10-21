#
# Faculdade SENAC - ADS
# Automação Comercial
# Desenvolvimento de APIs para coleta e tratamento de dados de IOT
# out/2021
#
# -*- coding: UTF-8 -*-

from flask import Flask, request, render_template
from flask import redirect
from datetime import datetime, date
import os
import time
import json
import tweepy   # biblioteca para envio de mensagens pelo twitter
import pandas as pd
from flask_mail import Mail, Message
from random import choice
import string

import sys
sys.path.insert(0,'/home/fac')
import ffac_headers as chaves



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

api_key_post = chaves.api_key_post
api_header_key = chaves.api_header_key

os.environ["TZ"] = "America/Recife"
time.tzset()

arquivos = {'A11': '/home/fac/mysite/dados/leituras_a11.csv', 'A22': '/home/fac/mysite/dados/leituras_a22.csv' }


app = Flask(__name__)

# configuracao para envio de email
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = chaves.mail_username
app.config['MAIL_PASSWORD'] = chaves.mail_password # senha de app https://support.google.com/accounts/answer/185833?hl=pt-BR
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


@app.route('/mostra', methods=['GET'])
def inicio():

    s1, d1, h1, t1, u1 = ultimosDados(arquivos['A11'])
    s2, d2, h2, t2, u2 = ultimosDados(arquivos['A22'])

    return render_template( 'dash_temp.html', s1= s1, s2=s2, t1=t1, t2=t2, u1=u1, u2=u2, d1=d1, d2=d2, h1=h1, h2=h2)

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

def ultimosDados( arq ) :
    df=pd.read_csv( arq )
    sensor = df.loc[len(df)-1, 'id']
    temp = df.loc[len(df)-1, 'temperatura']
    umid = df.loc[len(df)-1, 'umidade']
    data_leitura = df.loc[len(df)-1, 'data']
    hora_leitura = df.loc[len(df)-1, 'hora']
    return sensor, data_leitura, hora_leitura, str(temp), str(umid)

@app.route('/tuite')
def twitt():
    data_atual = str(date.today())
    hora_atual = str(datetime.time(datetime.now()))
    hora_atual = hora_atual[0:5]

    tweet = data_atual +" "+hora_atual+" Estamos prontos para recebe-lo"
    api.update_status(tweet)
    return "ok"


# Exemplo envio email de nova credencial

@app.route("/email")
def enviaMensagem():

    destino = request.args.get('destino')
    mensagem = request.args.get('mensagem')
    assunto = request.args.get('assunto')

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
    return json.dumps({'Mensagem':'Enviada'})


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

# end point para redirecionar site
@app.route("/redir/<string:dir>")
def redir( dir ) :
    sites = {
        'uol' : 'https://uol.com.br',
        'my' : 'https://i9i.solutions'
        }

    if dir in sites :
        return redirect (sites[dir])
    else :
        return str(dir)+" Não encontrado"

'''
# a partir de um codigo, redirecionar site
def redir_url( codigo ) :
    df = pd.read_csv( PATH_URL + "i9iapp-url.csv" , sep=";")
    localiza = df[df['sigla'] == codigo ]
    site=localiza['site-destino']
    if len(localiza) == 1 :
        return redirect ( site[1] )
    else:
        return redirect( 'https://i9isolutions.com' )
'''