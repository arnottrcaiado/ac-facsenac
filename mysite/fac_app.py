#
# Faculdade SENAC - ADS
# Automação Comercial
# Desenvolvimento de APIs para coleta e tratamento de dados de IOT
# out/2021
#
# -*- coding: UTF-8 -*-

from flask import Flask, request, render_template
from datetime import datetime, date
import os
import time
import json
import tweepy   # biblioteca para envio de mensagens pelo twitter
import ffac_headers as chaves
import pandas as pd

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

@app.route('/mostra', methods=['GET'])
def inicio():

    s1, d1, h1, t1, u1 = ultimosDados(arquivos['A11'])
    s2, d2, h2, t2, u2 = ultimosDados(arquivos['A22'])

    return render_template( 'dash_temp.html', s1= s1, s2=s2, t1=t1, t2=t2, u1=u1, u2=u2, d1=d1, d2=d2, h1=h1, h2=h2)


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

