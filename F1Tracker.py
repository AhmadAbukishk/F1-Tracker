from bs4 import BeautifulSoup
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage
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
    return datetime.strptime(mergedDate, '%d-%b-%Y %H:%M')


def fetchRaceDatetime(race, raceType):
    qualRow = race.findChild('td', string=re.compile(f'{raceType}')).parent
    qualDT = qualRow.findChild('td', string=re.compile(r'\w{3}')).text.strip()
    qualTM = qualRow.findChild('td', string=re.compile(':')).text.strip()

    return formatDate(qualDT, qualTM)


def fetchData():
    res = requests.get(f"https://www.skysports.com/f1/schedule-results")
    soup = BeautifulSoup(res.text, 'lxml')

    raceDetails = {}
    standingsSoup = soup.find('div', class_='standing-table standing-table--full f1-races__table')
    raceSoup = standingsSoup.parent.parent
    raceDetails['location'] = raceSoup.findChild('h2', class_='f1-races__race-name').text.strip()   
    raceDetails['raceDate'] = fetchRaceDatetime(raceSoup, 'Grand Prix')
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




tz = pytz.timezone('Etc/GMT+4')

prixDetails = fetchData()
qualDaysDif = prixDetails['qualDate'].date() - tz.localize(datetime.now()).date()
raceDaysDif = prixDetails['raceDate'].date() - tz.localize(datetime.now()).date()

if(qualDaysDif.days == 1):
    sendEmail(prixDetails['location'], prixDetails['qualDate'], 'Qaulifying')
    print("Email sent")
elif(raceDaysDif == 1):
    sendEmail(prixDetails['location'], prixDetails['raceDate'], 'Grand Prix')
    print("Email sent")

        