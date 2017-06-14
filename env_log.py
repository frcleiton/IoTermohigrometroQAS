#!/usr/bin/env python

import sqlite3
import sys
import ConfigParser
import smtplib
from datetime import date, datetime, timedelta

#from datetime import datetime
from email import Encoders
from email.MIMEBase import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email.Utils import formatdate

#from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def log_values(sensor_id, temp, hum):
    conn=sqlite3.connect('lab_app.db')
    curs=conn.cursor()
    curs.execute("""INSERT INTO temperatures values(datetime(CURRENT_TIMESTAMP, 'localtime'),(?), (?))""", (sensor_id,temp))
    curs.execute("""INSERT INTO humidities values(datetime(CURRENT_TIMESTAMP, 'localtime'),(?), (?))""", (sensor_id,hum))
    conn.commit()
    conn.close()

def alerta():
    conn=sqlite3.connect('lab_app.db')
    curs=conn.cursor()
    curs.execute("SELECT valor FROM parametros WHERE parametro = 'LIMITE_MIN_TEMP'");
    result_min = curs.fetchone()
    curs.execute("SELECT valor FROM parametros WHERE parametro = 'LIMITE_MAX_TEMP'");
    result_max = curs.fetchone()
    print temperature
    print result_min[0]
    print result_max[0]
    if (temperature < result_min[0]) or (temperature > result_max[0]):
        send_mail(temperature)

def send_mail(temp):
    HOST    = "smtp.grupocimed.com.br"
    server  = smtplib.SMTP(HOST)
    server.ehlo(HOST)
    server.login('cleiton.ferreira@grupocimed.com.br', senha_email)
    mensagem = 'Alerta de temperatura\n\nEquipamento: ' + str(equipamento) \
        + '\nTemperatura: ' + str(round(temperature, 2)) + ' C' + '\n' + formatdate(localtime=True)
    msg = MIMEText(mensagem)
    mail_from = 'cleiton.ferreira@grupocimed.com.br'
    mail_to = ['cleiton.ferreira@grupocimed.com.br','lista-ti-infraestrutura@grupocimed.com.br']
    msg['From'] = mail_from
    msg['To'] = ", ".join(mail_to)
    msg['Subject'] = 'Alerta de temperatura'
    server.sendmail( mail_from, mail_to, msg.as_string() )


config = ConfigParser.RawConfigParser()
config.read('config.properties')
sensor = config.getboolean('DebugSection','sensor.value')
equipamento = config.get('EquipSection','equip.name')
senha_email = config.get('MailSection','mail.passwd')

if sensor:
    import Adafruit_DHT
    humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)
else:
    import random
    humidity = random.randint(1,100)
    temperature = random.randint(10,30)

#grava os valores em um banco local sqlite
log_values(equipamento, temperature, humidity)

#envia email de alerta de temperatura
alerta()
