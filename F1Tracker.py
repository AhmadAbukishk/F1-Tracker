from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.message import EmailMessage
from pytz import timezone
import requests
import schedule
import time
import re
import smtplib
import os 
import pytz

load_dotenv()

def formatDate(dt, tm):
    cleanedDate = re.sub(r'\w{2}\s', "-", dt) + f'-{datetime.now().year}'
    mergedDate = f'{cleanedDate} {tm}'
    formatedDate = datetime.strptime(mergedDate, '%d-%b-%Y %H:%M')
    dateWithTimezone = formatedDate + timedelta(hours=3)

    return dateWithTimezone


def fetchRaceDatetime(race, raceType):
    raceRow = race.find('td', string=re.compile(f'{raceType}'))
    if(not raceRow):
        return None
    
    raceRow = raceRow.parent
    raceDT = raceRow.find('td', string=re.compile(r'\w{3}'))
    raceOnAirTM = raceRow.find('td', string=re.compile(':'))
    raceStartTM = raceOnAirTM.find_next_sibling('td')
    
    return formatDate(raceDT.text.strip(), raceStartTM.text.strip())    


def fetchData():
    res = requests.get(f"https://www.skysports.com/f1/schedule-results")
    soup = BeautifulSoup(res.text, 'lxml')

    raceDetails = {}
    standingsSoup = soup.find('div', class_='standing-table standing-table--full f1-races__table')
    raceSoup = standingsSoup.parent.parent
    raceDetails['location'] = raceSoup.find('h2', class_='f1-races__race-name').text.strip()   
    raceDetails['grandDate'] = fetchRaceDatetime(raceSoup, 'Grand Prix')
    raceDetails['qualDate'] = fetchRaceDatetime(raceSoup, 'Qualifying')

    
    return raceDetails


def setUpEmail(FROM, TO, location, date, raceType):
    SUBJECT = f"Reminder: {raceType} Tomorrow  Don't Miss It!"
    TXT = f"""
    the {raceType} is happening tomorrow! 🏁

    Here are the event details:

    Location: {location}
    Date: {date.date()}
    Time: {date.time()}
    """
    msg = EmailMessage()
    msg['Subject'] = SUBJECT
    msg['From'] = FROM
    msg['TO'] = TO
    msg.set_content(TXT)

    return msg


def sendEmail(location, date, raceType):
    host = 'smtp.gmail.com'
    port = 587
    FROM = os.getenv('EMAIL')
    TO = os.getenv('EMAIL')

    msg = setUpEmail(FROM, TO, location, date, raceType)
    try:
        server = smtplib.SMTP(host, port)
        server.connect(host, port)
        server.starttls()
        server.login(FROM, os.getenv('APP_PASSWORD'))
        server.send_message(msg)
        server.quit()
    except:
        print('Something went wrong in the email sender')



prixDetails = fetchData()
localizedCurrentDate = datetime.now().astimezone(timezone('Etc/GMT-4')).date()
if(prixDetails['qualDate'] != None):
    qualDaysDif = prixDetails['qualDate'].date() - localizedCurrentDate
    if(qualDaysDif.days == 1):
        sendEmail(prixDetails['location'], prixDetails['qualDate'], 'Qaulifying')

if(prixDetails['grandDate'] != None):
    qualDaysDif = prixDetails['grandDate'].date() - localizedCurrentDate
    if(qualDaysDif.days == 1):
        sendEmail(prixDetails['location'], prixDetails['grandDate'], 'Grand Prix')





        