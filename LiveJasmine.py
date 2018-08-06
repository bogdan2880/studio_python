import mysql.connector
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup as BSoup
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
downloadLocation_livecam = '/home/oracle/StudioScripts/jasmine_income'
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
            (studio_income,-1,display_name,'NEW', income_start_date_d, income_stop_date_d, 1 , currency , 'LV  JSM'))



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
        stopDay = datetime.datetime.today().day

    timestamp = datetime.datetime.now().replace(microsecond=0)
    start_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(startDay).zfill(2)
    stop_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(stopDay).zfill(2)
    start_date_d = datetime.datetime.strptime(start_date,"%Y-%m-%d")
    stop_date_d = datetime.datetime.strptime(stop_date,"%Y-%m-%d")
    currency = 'USD'

    #print(str(display_name_id), str(display_name), str(total_income), str(studio_income), str(timestamp), str(start_date_d), str(stop_date_d), str(currency))
    cur.execute('''INSERT into jasmin_performer_income (display_name_id,display_name,total_income,
    studio_income,timestamp,start_date,stop_date,currency)
                      values (%s,%s,%s,%s,%s,%s,%s,%s)''',
                (display_name_id, display_name, total_income, studio_income, timestamp, start_date_d, stop_date_d, currency))

def enable_download_in_headless_chrome(browser, download_dir):
    #add missing support for chrome "send_command"  to selenium webdriver
    browser.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')
    params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': download_dir}}
    browser.execute("send_command", params)

def download_csv_to_location(myConnection,dwld_location,startTime,stopTime,flag):
    try:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        prefs = {"download.default_directory" : dwld_location}
        chrome_options.add_experimental_option("prefs",prefs)
        browser = webdriver.Chrome(chrome_options=chrome_options)
        enable_download_in_headless_chrome(browser, dwld_location)
        # Debug
        #browser = webdriver.Chrome()
        # Login
        browser.get('https://modelcenter.jasmin.com/en/login')
        links = browser.find_elements_by_tag_name("input")
        username = links[1]
        username.send_keys('moneystef2018@gmail.com')
        password = links[2]
        password.send_keys('Catastef1984')
        submitButton = browser.find_element_by_xpath("//*[contains(@type, 'submit')]")
        submitButton.click()
        browser.get('https://modelcenter.jasmin.com/en/models')
        # End of Login
        browser.get('https://modelcenter.jasmin.com/en/payout/income-statistics?fromDate='+ str(startTime) + '&toDate=' + str(stopTime) +'&status=all&category=all')
    except:
        browser.close()
    print('https://modelcenter.jasmin.com/en/payout/income-statistics?fromDate='+ str(startTime) + '&toDate=' + str(stopTime) + '&status=all&category=all')
    bs_obj = BSoup(browser.page_source, 'html.parser')
    rows = bs_obj.find_all('table')[2].find_all('tr')

    if (flag == 0):
        counter = 0
        for row in rows:
            if ((counter > 0) and (counter < len(rows) -3)):
                cells = row.find_all('td')
                #print(cells[0].get_text().strip())
                #print(cells[1].get_text().strip()[1:].replace(',',''))
                insertQuery(myConnection, 0, cells[0].get_text().strip(),cells[1].get_text().strip()[1:].replace(',',''), -1)
            counter = counter + 1
        myConnection.commit()

    if (flag == 1):
        counter = 0
        for row in rows:
            if ((counter > 0) and (counter < len(rows) - 4)):
                cells = row.find_all('td')
                # print(cells[0].get_text().strip())
                # print(cells[1].get_text().strip()[1:].replace(',',''))
                insertQueryIncome(myConnection, cells[0].get_text().strip(),
                            cells[1].get_text().strip()[1:].replace(',', ''))
            counter = counter + 1
        myConnection.commit()
    browser.close()


# init time ranges calculations
currentDay = datetime.date.today().strftime("%d")
currentMonth = datetime.date.today().strftime("%m")
currentYear = datetime.date.today().strftime("%Y")
currentHour = datetime.datetime.now().hour
if (int(currentDay) > 15):
    startDay = 16
    # stopDay = calendar.mdays[datetime.date.today().month]
    stopDay = datetime.datetime.today().day
else:
    startDay = 1
    stopDay = datetime.datetime.today().day
start_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(startDay).zfill(2)
stop_date = str(currentYear) + '-' + str(currentMonth) + '-' + str(stopDay).zfill(2)
start_timestamp = calendar.timegm(time.strptime(start_date, '%Y-%m-%d'))
stop_timestamp = calendar.timegm(time.strptime(stop_date, '%Y-%m-%d'))
myConnection = mysql.connector.connect(host=hostname, user=username, passwd=password, db=database)
print('LiveJasmin on:' + currentDay + '-' + currentMonth + '-' + currentYear)
try:
    download_csv_to_location(myConnection,downloadLocation_livecam,start_date,stop_date,0)
except:
    myConnection.close()

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

        income_start_date = str(income_year) + '-' + str(income_month) + '-' + str(income_startDay).zfill(2)
        income_stop_date = str(income_year) + '-' + str(income_month) + '-' + str(income_stopDay).zfill(2)
        
        startdt = datetime.datetime.strptime(income_start_date, '%Y-%m-%d')
        stopdt = datetime.datetime.strptime(income_stop_date, '%Y-%m-%d')

        str_start_date = str(startdt)
        str_stop_date = str(stopdt)

        start_dt = str_start_date[:str_start_date.index(' ')]
        stop_dt = str_stop_date[:str_stop_date.index(' ')]
    
        print('LiveCam push to income:' + currentDay + '-' + currentMonth + '-' + currentYear)
        download_csv_to_location(myConnection,downloadLocation_income,start_dt,stop_dt,1)

myConnection.close()
