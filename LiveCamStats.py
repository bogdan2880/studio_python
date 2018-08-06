import mysql.connector
from selenium import webdriver
import time
import os
import glob
import csv
import datetime
import calendar

hostname = '78.47.135.133'
username = 'uni_business_dev'
password = 'Mysql123.'
database = 'run_business_dev'
downloadLocation_livecam = '/home/oracle/StudioScripts/livecam_income'
downloadLocation_income = '/home/oracle/StudioScripts/income'

def doQuery(conn):
    cur = conn.cursor()
    cur.execute("SELECT login FROM run_business_dev.jhi_user")
    for login in cur.fetchall():
        print(login)


def insertQueryIncome(conn,display_name,studio_income):
    cur = conn.cursor()
    
    currentDay = datetime.date.today().strftime("%d")
    currentMonth = datetime.date.today().strftime("%m")
    currentYear = datetime.date.today().strftime("%Y")

    income_startDay = 0
    income_stopDay = 0
    income_month = 0
    income_year = 0
    if (int(currentDay) == 16) :
        income_startDay = 1
        income_stopDay = 15
        income_month = int(currentMonth)
        income_year = int(currentYear)
    if (int(currentDay) == 1) :
        income_startDay = 16
        if (datetime.date.today().month -1 == 0) :
            income_stopDay = calendar.mdays[12]
            income_month = 12
            income_year = int(currentYear) -1
        else :
            income_stopDay = calendar.mdays[datetime.date.today().month -1]
            income_month = int(currentMonth) -1
            income_year = int(currentYear)

    income_start_date = str(income_year) + '-' + str(income_month) + '-' + str(income_startDay)
    income_stop_date = str(income_year) + '-' + str(income_month) + '-' + str(income_stopDay)

    income_start_date_d =datetime.datetime.strptime(income_start_date,"%Y-%m-%d")
    income_stop_date_d = datetime.datetime.strptime(income_stop_date,"%Y-%m-%d")
    currency = 'USD'

    print('Execute Insert Income')
    cur.execute('''INSERT INTO income (amount,user_id,param_1,status,create_date,event_date,room_id,currency,external_partner_id)
                  values (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
            (studio_income,-1,display_name,'NEW', income_start_date_d, income_stop_date_d, 1 , currency , 'livecammates'))



def insertQuery(conn,display_name_id,display_name,total_income,studio_income):
    cur = conn.cursor()

    currentDay = datetime.date.today().strftime("%d")
    currentMonth = datetime.date.today().strftime("%m")
    currentYear = datetime.date.today().strftime("%Y")

    if (int(currentDay) > 15) :
        startDay = 16
        stopDay = calendar.mdays[datetime.date.today().month]
    else :
        startDay = 1
        stopDay = 15

    timestamp = datetime.datetime.now().replace(microsecond=0)
    start_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(startDay)
    stop_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(stopDay)
    start_date_d = datetime.datetime.strptime(start_date,"%Y-%m-%d")
    stop_date_d = datetime.datetime.strptime(stop_date,"%Y-%m-%d")
    currency = 'USD'

    cur.execute('''INSERT into livecam_performer_income (display_name_id,display_name,total_income,
    studio_income,timestamp,start_date,stop_date,currency)
                      values (%s,%s,%s,%s,%s,%s,%s,%s)''',
                (display_name_id, display_name, total_income, studio_income, timestamp, start_date_d, stop_date_d, currency))

def enable_download_in_headless_chrome(browser, download_dir):
    #add missing support for chrome "send_command"  to selenium webdriver
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)

def download_csv_to_location(dwld_location,startTime,stopTime) :
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    prefs = {"download.default_directory" : dwld_location}
    chrome_options.add_experimental_option("prefs",prefs)
    browser = webdriver.Chrome(chrome_options=chrome_options)
    enable_download_in_headless_chrome(browser, dwld_location)
    browser.get('http://studio.livecammates.com/autologin/a79b459ab62d4648a997561d8dfed971')
    browser.get('https://studio.livecammates.com/report/studioIncome.csv?dateFrom='+ str(startTime) + '&dateTo=' + str(stopTime))
    time.sleep(1)
    browser.close()

#init time ranges calculations
currentDay = datetime.date.today().strftime("%d")
currentMonth = datetime.date.today().strftime("%m")
currentYear = datetime.date.today().strftime("%Y")
currentHour = datetime.datetime.now().hour
if (int(currentDay) > 15):
    startDay = 16
    stopDay = calendar.mdays[datetime.date.today().month]
else:
    startDay = 1
    stopDay = 15
start_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(startDay)
stop_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(stopDay)
start_timestamp = calendar.timegm(time.strptime(start_date, '%Y-%m-%d'))
stop_timestamp = calendar.timegm(time.strptime(stop_date, '%Y-%m-%d'))
myConnection = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
print('LiveCam on:' + currentDay + '-' + currentMonth + '-' + currentYear)
download_csv_to_location(downloadLocation_livecam,start_timestamp,stop_timestamp)

path = downloadLocation_livecam
extension = 'csv'
os.chdir(path)
result = [i for i in glob.glob('*.{}'.format(extension))]
for p in result:
    with open(downloadLocation_livecam + '/' + p) as csvfile:
        readCSV = csv.reader(csvfile, delimiter=',')
        row_num = 0;
        for row in readCSV:
            if (row_num > 0) :
                insertQuery(myConnection,row[0],row[1],row[2],row[3])
                myConnection.commit()
                row_num = row_num +1
            else :
                row_num = row_num +1
    print(p)
    csvfile.close()
    os.remove(downloadLocation_livecam + '/' + p)

if (int(currentDay) == 16 or int(currentDay) == 1):
    if currentHour == 10 :
        print('Populate income')
        income_startDay = 0
        income_stopDay = 0
        income_month = 0
        income_year = 0
        if (int(currentDay) >= 16) :
            income_startDay = 1
            income_stopDay = 15
            income_month = int(currentMonth)
            income_year = int(currentYear)
        if (int(currentDay) == 1) :
            income_startDay = 16
            if (datetime.date.today().month -1 == 0) :
                income_stopDay = calendar.mdays[12]
                income_month = 12
                income_year = int(currentYear) -1
            else :
                income_stopDay = calendar.mdays[datetime.date.today().month -1]
                income_month = int(currentMonth) -1
                income_year = int(currentYear)

        income_start_date = str(income_year) + '-' + str(income_month) + '-' + str(income_startDay)
        income_stop_date = str(income_year) + '-' + str(income_month) + '-' + str(income_stopDay)

        income_start_timestamp = calendar.timegm(time.strptime(income_start_date, '%Y-%m-%d'))
        income_stop_timestamp = calendar.timegm(time.strptime(income_stop_date, '%Y-%m-%d'))
        print('LiveCam push to income:' + currentDay + '-' + currentMonth + '-' + currentYear)
        download_csv_to_location(downloadLocation_income,income_start_timestamp,income_stop_timestamp)

        path = downloadLocation_income
        extension = 'csv'
        os.chdir(path)
        result = [i for i in glob.glob('*.{}'.format(extension))]
        for p in result:
            with open(downloadLocation_income + '/' + p) as csvfile:
                readCSV = csv.reader(csvfile, delimiter=',')
                row_num = 0;
                for row in readCSV:
                    if (row_num > 0) :
                        insertQueryIncome(myConnection,row[1],row[3])
                        myConnection.commit()
                        row_num = row_num +1
                    else :
                        row_num = row_num +1
            print(p)
            csvfile.close()
            os.remove(downloadLocation_income + '/' + p)


myConnection.close()
