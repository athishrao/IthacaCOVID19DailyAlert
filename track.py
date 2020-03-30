import os
import urllib3
import hashlib
import requests
import smtplib, ssl
from constants import *
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
    return subscribers[:1]


def get_body(when, totalTest, posCases, negCases, deaths):
    """
    Create Body of the mail

    :param when:        date of the announcement
    :param totalTest:   total test cases
    :param posCases:    positive cases
    :param negCases:    negative cases
    :param deaths:      deaths caused

    :return:            Formatted message string
    """
    return f"In Ithaca, as of {when} \nTotal Tested for COVID-19: {totalTest} \nPositive Test Results count: {posCases}\nNegative results count: {negCases}\nDeath toll: {deaths}\n\nTake care.\n\n{MSG_FOOTER}"


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
    table = soup.find_all("table")[0]
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
    data = table.find_all("tr")
    details["when"] = str(table.find_all("em")).split(".")[0][11:]
    data = str(data).split('<td class="ctr">')
    data = data[4].split()
    details["totalTest"] = data[3].split("</td>")[0]
    details["posCases"] = data[6].split("</td>")[0]
    details["negCases"] = data[9].split("</td>")[0]
    details["deaths"] = data[12].split("</td>")[0]
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
    message["Subject"] = "Ithaca Corona Update "
    message.attach(MIMEText(body, "plain"))
    session = smtplib.SMTP("smtp.gmail.com", 587)
    session.starttls()
    # TODO: NEED ERROR CHECKING HERE (LOGIN FAILED)
    session.login(username, password)
    text = message.as_string()
    # TODO: NEED ERROR CHECKING HERE (EMAIL SEND FAILED)
    session.sendmail(username, receivers, text)
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
        + parsed_data["deaths"]
    )
    if hash == oldHash:
        message = "No Updates!"
    else:
        body = get_body(
            parsed_data["when"],
            parsed_data["totalTest"],
            parsed_data["posCases"],
            parsed_data["negCases"],
            parsed_data["deaths"],
        )
        dispatch_mails(username, password, subscribers, body)
        message = "Mail Sent!"
        with open(CWD + "hash.txt", "w") as f:
            f.write(hash)

    with open(CWD + "file.txt", "a") as f:
        f.write(message)
