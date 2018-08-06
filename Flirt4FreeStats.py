import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from xml.dom import minidom
import time
import os
import glob
import csv
import datetime
import calendar

#sa nu te mai benoclezi si tu la poza: https://studios.flirt4free.com
#S1623
#RLbs7494

hostname = '78.47.135.133'
username = 'uni_business_dev'
password = 'Mysql123.'
database = 'run_business_dev'
downloadLocation_flirt = '/home/oracle/StudioScripts/flirt_income'
downloadLocation_income = '/home/oracle/StudioScripts/income'
getStudioCredentials = 'SELECT username,jhi_password FROM studio_login_credentials'


def enable_download_in_headless_chrome(browser,download_dir) :
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
    # Debug
    #browser = webdriver.Chrome()
    # Login
    browser.get('https://studios.flirt4free.com')
    username = browser.find_element_by_xpath("//*[contains(@id, 'username_field')]")
    username.send_keys('S1623')
    password = browser.find_element_by_xpath("//*[contains(@id, 'password_field')]")
    password.send_keys('RLbs7494')
    user_type = browser.find_element_by_xpath("//*[contains(@id, 'user_type')]")
    user_type.send_keys('studio')
    submitButton = browser.find_element_by_xpath("//*[contains(@type, 'submit')]")
    submitButton.click()
    # End of Login
    time.sleep(1)
    browser.get('https://studios.flirt4free.com/broadcasters/stats.php?a=studio_overview&studio=LHQL&date_start=' + str(startTime) + '&date_end=' + str(stopTime))
    print('https://studios.flirt4free.com/broadcasters/stats.php?a=studio_overview&studio=LHQL&date_start=' + str(startTime) + '&date_end=' + str(stopTime))
    N = 65
    actions = webdriver.ActionChains(browser)
    for _ in range(N):
        #print("Send TAB" + str(N))
        actions = actions.send_keys(Keys.TAB)
        time.sleep(0.1)
    #actions.perform()
    actions.send_keys(Keys.ENTER)
    actions.perform()
    time.sleep(1)
    #https://studios.flirt4free.com/broadcasters/stats.php?a=studio_overview&studio=LHQL&date_start=2018-07-01&date_end=2018-07-11
    #https://studios.flirt4free.com/broadcasters/stats-export.php?a=studio_overview&studio=LHQL&date_start=2018-07-01&date_end=2018-07-11&format=csv
    time.sleep(10)
    browser.close()


def insertQuery(conn,display_name_id,display_name,total_income,studio_income):
    print('Insert')
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

    cur.execute('''INSERT into flirt4free_performer_income (display_name_id,display_name,total_income,
    studio_income,timestamp,start_date,stop_date,currency)
                      values (%s,%s,%s,%s,%s,%s,%s,%s)''',
                (display_name_id, display_name, total_income, studio_income, timestamp, start_date_d, stop_date_d, currency))


def insertQueryIncome(conn, display_name, studio_income):
    cur = conn.cursor()

    currentDay = datetime.date.today().strftime("%d")
    currentMonth = datetime.date.today().strftime("%m")
    currentYear = datetime.date.today().strftime("%Y")

    income_startDay = 0
    income_stopDay = 0
    income_month = 0
    income_year = 0
    if (int(currentDay) == 16):
        income_startDay = 1
        income_stopDay = 15
        income_month = int(currentMonth)
        income_year = int(currentYear)
    if (int(currentDay) == 1):
        income_startDay = 16
        if (datetime.date.today().month - 1 == 0):
            income_stopDay = calendar.mdays[12]
            income_month = 12
            income_year = int(currentYear) - 1
        else:
            income_stopDay = calendar.mdays[datetime.date.today().month - 1]
            income_month = int(currentMonth) - 1
            income_year = int(currentYear)

    income_start_date = str(income_year) + '-' + str(income_month) + '-' + str(income_startDay)
    income_stop_date = str(income_year) + '-' + str(income_month) + '-' + str(income_stopDay)

    income_start_date_d = datetime.datetime.strptime(income_start_date, "%Y-%m-%d")
    income_stop_date_d = datetime.datetime.strptime(income_stop_date, "%Y-%m-%d")
    currency = 'USD'

    print('Execute Insert Income')
    cur.execute('''INSERT INTO income (amount,user_id,param_1,status,create_date,event_date,room_id,currency,external_partner_id)
                  values (%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                (studio_income, -1, display_name, 'NEW', income_start_date_d, income_stop_date_d, 1, currency,
                 'flirtfree'))


#init time ranges calculations
currentDay = datetime.date.today().strftime("%d")
currentMonth = datetime.date.today().strftime("%m")
currentYear = datetime.date.today().strftime("%Y")
currentHour = datetime.datetime.now().hour
if (int(currentDay) > 15):
    startDay = 16
    #stopDay = calendar.mdays[datetime.date.today().month]
    stopDay = datetime.datetime.today().day
else:
    startDay = 1
    #stopDay = 15
    stopDay = datetime.datetime.today().day
start_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(startDay)
stop_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(stopDay)
start_timestamp = calendar.timegm(time.strptime(start_date, '%Y-%m-%d'))
stop_timestamp = calendar.timegm(time.strptime(stop_date, '%Y-%m-%d'))
myConnection = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
print('Flirt4Free on:' + currentDay + '-' + currentMonth + '-' + currentYear)
download_csv_to_location(downloadLocation_flirt,start_date,stop_date)

path = downloadLocation_flirt
extension = 'xml'
os.chdir(path)
result = [i for i in glob.glob('*.{}'.format(extension))]
for p in result:
    xmldoc = minidom.parse(downloadLocation_flirt + '/' + p)
    itemlist = xmldoc.getElementsByTagName('model')
    for s in itemlist:
        insertQuery(myConnection, s.attributes['id'].value,
                    s.attributes['stage_name'].value,
                    float(s.attributes['gross_sales'].value[1:]),
                    float(s.attributes['net_commission'].value[1:]))
        myConnection.commit()
os.remove(downloadLocation_flirt + '/' + p)

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
        print('Flirt4Free push to income:' + currentDay + '-' + currentMonth + '-' + currentYear)
        download_csv_to_location(downloadLocation_income,income_start_date,income_stop_date)

        path = downloadLocation_income
        extension = 'xml'
        os.chdir(path)
        result = [i for i in glob.glob('*.{}'.format(extension))]
        for p in result:
            xmldoc = minidom.parse(downloadLocation_income + '/' + p)
            itemlist = xmldoc.getElementsByTagName('model')
            for s in itemlist:
                insertQueryIncome(myConnection,s.attributes['stage_name'].value,
                            float(s.attributes['gross_sales'].value[1:]))
                myConnection.commit()
        os.remove(downloadLocation_income + '/' + p)

myConnection.close()
