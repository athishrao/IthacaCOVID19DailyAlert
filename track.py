import os
import urllib3
import hashlib
import requests
import smtplib, ssl
from bs4 import BeautifulSoup
from urllib.request import urlopen
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

URL = "https://tompkinscountyny.gov/health"
USER = ""
PWD = ""
RECV = []
when, totalTest, posCases, negCases, deaths = "", "", "", "", ""
CWD = os.getcwd()

#####################################################################################################################
# Method : Get a list of users to whom the mail is to be sent to
# Enter email ID's seperated by newline character
def retreiveUsers():
    global RECV
    with open(CWD+"/recv.txt", "r") as f:
        for line in f.readlines():
            RECV.append(line.strip())

#####################################################################################################################
# Method : Create Body of the mail
# Parameters - 
# when          date of the announcement
# totalTest     total test cases
# posCases      positive cases
# negCases      negative cases
# deaths        deaths caused
def getBody(when, totalTest, posCases, negCases, deaths):
    return str("In Ithaca, as of " + when + ", Total Tested for COVID-19 is " + totalTest + " Positive Test Results are " + posCases + ". Negative cases is " + negCases + ". Death toll is " + deaths + ".\nTake care.\n\n-Athish Rahul Rao\n+1 7189160665")
    
#####################################################################################################################
# Method : Retrieve gmail credentials from a file called creds.txt to be places in the same directory as this file
# Username of line 1 and Pwd on line 2
# Parameters - None
def getCreds():
    global USER
    global PWD
    creds = []
    with open(CWD+"/creds.txt", "r") as f:
        for line in f.readlines():
            creds.append(line.strip())
    USER = creds[0]
    PWD = creds[1]

#####################################################################################################################
# Method : Get a unique hash for the numbs at hand
# Parameters -
# text          text to be hashed
# Return - hash value of the text
def getHash(text):
    return str(hashlib.sha224(text.encode('utf-8')).hexdigest())

#####################################################################################################################
# Method : Go through the contents of the page and identify the table
# Parameters -
# url       URL to the page
def parseURL(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    temp = []
    table = soup.find_all('table')[0]
    parseTable(table)

#####################################################################################################################
# Method : Given a table, retrieve the numbers
# Parameters -
# table     HTML Table from parseURL method
def parseTable(table):
    global totalTest
    global posCases
    global negCases
    global deaths
    global when
    cols = 0
    rows = 0
    column_names = []
    data = table.find_all('tr')
    when = str(table.find_all("em")).split(".")[0][11:]
    data = str(data).split("<td class=\"ctr\">")
    data = data[4].split()
    totalTest = data[3].split("</td>")[0]
    posCases = data[6].split("</td>")[0]
    negCases = data[9].split("</td>")[0]
    deaths = data[12].split("</td>")[0]

#####################################################################################################################
# Method : Send an email from the sender to recievers
# Parameters -
# Username      gmail username of sender
# password      gmail password of sender
# receivers     list of receivers
# body          body of the mail being sent
def sendMail(Username, password, receivers, body):
    
    receivers = ",".join(receivers)
    message = MIMEMultipart()
    message['From'] = Username
    message['To'] = receivers
    message['Subject'] = 'Ithaca Corona Update '+ when
    message.attach(MIMEText(body, 'plain'))
    session = smtplib.SMTP('smtp.gmail.com', 587) 
    session.starttls() 
    session.login(Username, password) 
    text = message.as_string()
    session.sendmail(Username, receivers, text)
    session.quit()

#####################################################################################################################
# Method : Called on initialisation of the script
if __name__ == "__main__":
    oldHash = ""
    message = ""
    with open(CWD + "/hash.txt", "r") as f:
        for line in f.readlines():
            oldHash = line.strip()
    
    retreiveUsers()
    
    parseURL(URL)

    getCreds()

    hash = getHash(when + totalTest + posCases + negCases + deaths)
    
    body = getBody(when, totalTest, posCases, negCases, deaths)

    if (hash == oldHash):
        message = 'No Updates!'
    else:
        sendMail(USER, PWD, RECV, body)
        message = 'Mail Sent!'
        with open(CWD + "/hash.txt", "w") as f:
            f.write(hash)
    
    with open(CWD + "/file.txt", "a") as f:
            f.write(message)