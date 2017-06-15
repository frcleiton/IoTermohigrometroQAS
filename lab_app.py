from flask import Flask, request, render_template
import time
import datetime
import arrow
import sqlite3
import ConfigParser
from email.Utils import formatdate

app = Flask(__name__)
config = ConfigParser.RawConfigParser()
config.read('config.properties')
modo_debug  = config.getboolean('DebugSection','debug.value')
sensor      = config.getboolean('DebugSection','sensor.value')
equipamento = config.get('EquipSection','equip.name')
local       = config.get('EquipSection','equip.local')
app.debug   = modo_debug

@app.route("/")
@app.route("/lab_temp")
def lab_temp():
    if sensor:
        import sys
        import Adafruit_DHT
        humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, 17)
    else:
        import random
        humidity = random.randint(1,100)
        temperature = random.randint(10,30)
    rmin, rmax = get_parametros()
    if humidity is not None and temperature is not None:
        return render_template("lab_temp.html",temp=temperature,hum=humidity,equipname=equipamento,equipsite=local,min=rmin[0],max=rmax[0])
    else:
        return render_template("no_sensor.html")

@app.route("/lab_env_db", methods=['GET'])  #Add date limits in the URL #Arguments: from=2015-03-04&to=2015-03-05
def lab_env_db():
	temperatures, humidities, timezone, from_date_str, to_date_str = get_records()

	# Create new record tables so that datetimes are adjusted back to the user browser's time zone.
	time_adjusted_temperatures = []
	time_adjusted_humidities   = []

	for record in temperatures:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm")
		time_adjusted_temperatures.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])

	for record in humidities:
		local_timedate = arrow.get(record[0], "YYYY-MM-DD HH:mm")
		time_adjusted_humidities.append([local_timedate.format('YYYY-MM-DD HH:mm'), round(record[2],2)])

	print "rendering lab_env_db.html with: %s, %s, %s" % (timezone, from_date_str, to_date_str)

	return render_template("lab_env_db.html",
							timezone		= timezone,
							temp 			= time_adjusted_temperatures,
							hum 			= time_adjusted_humidities,
							from_date 		= from_date_str,
							to_date 		= to_date_str,
							temp_items 		= len(temperatures),
							query_string	= request.query_string, #This query string is used
							#by the Plotly link
							hum_items 		= len(humidities))

def get_records():
	from_date_str 	= request.args.get('from',time.strftime("%Y-%m-%d 00:00")) #Get the from date value from the URL
	to_date_str 	= request.args.get('to',time.strftime("%Y-%m-%d %H:%M"))   #Get the to date value from the URL
	timezone	    = request.args.get('timezone','America/Sao_Paulo')
	range_h_form	= request.args.get('range_h','');  #This will return a string, if field range_h exists in the request
	range_h_int 	= "nan"  #initialise this variable with not a number

	print "REQUEST:"
	print request.args

	try:
		range_h_int	= int(range_h_form)
	except:
		print "range_h_form not a number"


	print "Received from browser: %s, %s, %s, %s" % (from_date_str, to_date_str, timezone, range_h_int)

	if not validate_date(from_date_str):			# Validate date before sending it to the DB
		from_date_str 	= time.strftime("%Y-%m-%d 00:00")
	if not validate_date(to_date_str):
		to_date_str 	= time.strftime("%Y-%m-%d %H:%M")		# Validate date before sending it to the DB
	print '2. From: %s, to: %s, timezone: %s' % (from_date_str,to_date_str,timezone)
	# Create datetime object so that we can convert to UTC from the browser's local time
	from_date_obj       = datetime.datetime.strptime(from_date_str,'%Y-%m-%d %H:%M')
	to_date_obj         = datetime.datetime.strptime(to_date_str,'%Y-%m-%d %H:%M')

	# If range_h is defined, we don't need the from and to times
	if isinstance(range_h_int,int):
		arrow_time_from = arrow.now().replace(hours=-range_h_int)
		arrow_time_to   = arrow.now()
                from_date_utc   = arrow_time_from.strftime("%Y-%m-%d %H:%M")
		to_date_utc     = arrow_time_to.strftime("%Y-%m-%d %H:%M")
		from_date_str   = arrow_time_from.strftime("%Y-%m-%d %H:%M")
		to_date_str	= arrow_time_to.strftime("%Y-%m-%d %H:%M")
	else:
		#Convert datetimes to UTC so we can retrieve the appropriate records from the database
		from_date_utc   = arrow.get(from_date_obj, timezone).strftime("%Y-%m-%d %H:%M")
		to_date_utc     = arrow.get(to_date_obj, timezone).to('America/Sao_Paulo').strftime("%Y-%m-%d %H:%M")

	conn 	= sqlite3.connect('lab_app.db')
	curs 	= conn.cursor()
	curs.execute("SELECT * FROM temperatures WHERE rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	temperatures    = curs.fetchall()
	curs.execute("SELECT * FROM humidities WHERE rDateTime BETWEEN ? AND ?", (from_date_utc.format('YYYY-MM-DD HH:mm'), to_date_utc.format('YYYY-MM-DD HH:mm')))
	humidities 	= curs.fetchall()
	conn.close()
	return [temperatures, humidities, timezone, from_date_str, to_date_str]


@app.route("/lab_parametros", methods=['GET', 'POST'])
def lab_parametros():
    from flask import redirect
    conn2   = sqlite3.connect('lab_app.db')
    curs2   = conn2.cursor()
    if request.method == 'GET':
        curs2.execute("SELECT valor FROM parametros WHERE parametro = 'LIMITE_MIN_TEMP'");
        result_min = curs2.fetchone()
        curs2.execute("SELECT valor FROM parametros WHERE parametro = 'LIMITE_MAX_TEMP'");
        result_max = curs2.fetchone()
        return render_template("lab_parametros.html",min=result_min[0],max=result_max[0])
    if request.method == 'POST':
        set_min = request.form['temp_min']
        curs2.execute('UPDATE parametros SET valor = %d where parametro = %s' % (int(set_min),"'LIMITE_MIN_TEMP'"))
        set_max = request.form['temp_max']
        curs2.execute('UPDATE parametros SET valor = %d where parametro = %s' % (int(set_max),"'LIMITE_MAX_TEMP'"))
        conn2.commit()
        conn2.close()
        return redirect('/lab_parametros')

@app.route("/lab_medias", methods=['GET'])
def lab_medias():
    from flask import redirect
    conn 	= sqlite3.connect('lab_app.db')
    curs 	= conn.cursor()
    #qry = "SELECT strftime('%d%m%Y', rDatetime), avg(temp) as media, min(temp) as minimo, max(temp) as maxima from temperatures group by strftime('%d%m%Y',rDatetime)"
    qry = "SELECT strftime('%d%m%Y', rDatetime), avg(temp) as media from temperatures group by strftime('%d%m%Y',rDatetime)"
    curs.execute(qry)
    medias = curs.fetchall()
    conn.close()
    lmedias_date = []
    for record in medias:
        lmedias_date.append([arrow.get(record[0], "DDMMYYYY").strftime("%Y-%m-%d"), round(record[1],2)])
    lmedia_items = len(lmedias_date)
    return render_template("lab_medias.html",medias_date=lmedias_date,media_items=lmedia_items)
#lmedias_date.append(datetime.datetime.strptime(record[0], '%d%m%Y').date())
#return render_template("lab_temp.html",temp=temperature,hum=humidity,equipname=equipamento,equipsite=local,mini=rmin[0],maxi=rmax[0])
#return redirect('/lab_parametros')                            

def validate_date(d):
    try:
        datetime.datetime.strptime(d, '%Y-%m-%d %H:%M')
        return True
    except ValueError:
        return False

def get_parametros():
    conn=sqlite3.connect('lab_app.db')
    curs=conn.cursor()
    curs.execute("SELECT valor FROM parametros WHERE parametro = 'LIMITE_MIN_TEMP'");
    result_min = curs.fetchone()
    curs.execute("SELECT valor FROM parametros WHERE parametro = 'LIMITE_MAX_TEMP'");
    result_max = curs.fetchone()
    conn.close()
    return [result_min, result_max]

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
