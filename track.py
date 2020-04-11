import os
import urllib3
import hashlib
import requests
import smtplib, ssl
from constants import *
from datetime import date
from bs4 import BeautifulSoup
from urllib.request import urlopen
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ----- GENERAL UTILS
def retreive_subscribers():
    """
    Get a list of subscribers to whom the mail is to be sent to

    :return:    Emails of current subscribers
    """
    subscribers = []
    SUBSCRIBER_FILE = "recv.txt"
    with open(CWD + SUBSCRIBER_FILE, "r") as f:
        for line in f.readlines():
            subscribers.append(line.strip())
    return subscribers


def get_body(when, totalTest, posCases, negCases, pending, recovered, currentlyHospitalized, dischargedToday, TCResidentDeaths, nonResidentDeaths):
    """
    Create Body of the mail

    :param when:        date of the announcement
    :param totalTest:   total test cases
    :param posCases:    positive cases
    :param negCases:    negative cases
    :param deaths:      deaths caused

    :return:            Formatted message string
    """
    return f"In Ithaca, as of {when},\n\nTotal Tested for COVID-19: {totalTest} \nPending Tests: {pending} \nPositive Test Results count: {posCases} \nRecovered Cases: {recovered} \nNegative results count: {negCases}\nCurrently Hospitalized: {currentlyHospitalized}\nDischarged Today: {dischargedToday}\nTC Resident Deaths: {TCResidentDeaths}\nNon-Resident Deaths: {nonResidentDeaths}\n\nTake care.\n\n{MSG_FOOTER}"


def get_creds():
    """
    Load my email credentials from environment variables

    :return:    tuple -> email, passWord
    """
    return os.environ.get("EMAIL_ID"), os.environ.get("EMAIL_PASS")


def generate_hash(text):
    """
    Get a unique hash for the numbs at hand

    :param text:    text to be hashed
    :return:        SHA224 value of the text
    """
    return str(hashlib.sha224(text.encode("utf-8")).hexdigest())

# ----- HTML PARSING UTILS
def parse_url(url):
    """
    Go through the contents of the page and identify the table

    :param url:     URL to the page
    :return:        parse_table return
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "lxml")
    temp = []
    table = soup.find_all("table")
    return parse_table(table)


def parse_table(table):
    """
    Given a table, retrieve the numbers

    :param table:       HTML Table from parse_url method
    :return:            A hashmap (detail_type -> detail_value)
    """
    details = {}
    cols = 0
    rows = 0
    column_names = []
    data = []
    data1 = (table[0].find_all("tr"))
    data2 = (table[1].find_all("tr"))
    # details["when"] = str(table.find_all('em style="font-size:90%;"')).split(".")[0][11:]
    today = date.today()
    d1 = today.strftime("%d/%m/%Y")
    details["when"] = d1
    data1 = str(data1).split('<td class="ctr">')
    data1 = data1[5].split("</td>")
    data2 = str(data2).split('</td>')
    details["totalTest"] = data1[1].split("\t")[-1]
    details["pending"] = data1[2].split("\t")[-1]
    details["posCases"] = data1[3].split("\t")[-1]
    details["negCases"] = data1[4].split("\t")[-1]
    details["recovered"] = data1[5].split("\t")[-1]
    details["Currently Hospitalized"] = data2[4].split("\t")[-1]
    details["Discharged Today"] =  data2[5].split("\t")[-1]
    details["TC Resident Deaths"] = data2[6].split("\t")[-1]
    details["Non-Resident Deaths"] = data2[7].split("\t")[-1]
    return details


# ----- MAILER
def dispatch_mails(username, password, receivers, body):
    """
    Send an email from the sender to recievers

    :param username:      gmail username of sender
    :param password:      gmail password of sender
    :param receivers:     list of receivers
    :param body:          body of the mail being sent
    """
    receivers = ",".join(receivers)
    message = MIMEMultipart()
    message["From"] = username
    message["To"] = receivers
    # message["Bcc"] = receivers
    message["Subject"] = "Ithaca Corona Update "
    message.attach(MIMEText(body, "plain"))
    session = smtplib.SMTP("smtp.gmail.com", 587)
    session.starttls()
    # TODO: NEED ERROR CHECKING HERE (LOGIN FAILED)
    session.login(username, password)
    text = message.as_string()
    # TODO: NEED ERROR CHECKING HERE (EMAIL SEND FAILED)
    print(receivers)
    session.sendmail(username, receivers.split(","), text)
    session.quit()


# ----- MAIN EXECUTION
if __name__ == "__main__":
    oldHash = ""
    message = ""
    with open(CWD + "hash.txt", "r") as f:
        for line in f.readlines():
            oldHash = line.strip()

    subscribers = retreive_subscribers()
    parsed_data = parse_url(URL)
    username, password = get_creds()
    hash = generate_hash(
        parsed_data["when"]
        + parsed_data["totalTest"]
        + parsed_data["posCases"]
        + parsed_data["negCases"]
        + parsed_data["pending"]
        + parsed_data["recovered"]
        + parsed_data["Currently Hospitalized"]
        + parsed_data["Discharged Today"]
        + parsed_data["TC Resident Deaths"]
        + parsed_data["Non-Resident Deaths"]
    )
    if hash == oldHash:
        message = "No Updates!"
    else:
        body = get_body(
            parsed_data["when"],
            parsed_data["totalTest"],
            parsed_data["posCases"],
            parsed_data["negCases"],
            parsed_data["pending"],
            parsed_data["recovered"],
            parsed_data["Currently Hospitalized"],
            parsed_data["Discharged Today"],
            parsed_data["TC Resident Deaths"],
            parsed_data["Non-Resident Deaths"]
        )
        dispatch_mails(username, password, subscribers, body)
        message = "Mail Sent!"
        with open(CWD + "hash.txt", "w") as f:
            f.write(hash)

    with open(CWD + "file.txt", "a") as f:
        f.write(message)
