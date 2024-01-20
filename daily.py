import time
import datetime
import sys
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS
from flask_app import rfpJob

import rfpReaderBackend

import smtplib
from os.path import basename
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate



engine = create_engine(
    SQLALCHEMY_DATABASE_URI, **SQLALCHEMY_ENGINE_OPTIONS
)
Session = sessionmaker(engine)

def getDailyJobData():
    print("Fetching job data")
    with Session.begin() as session:
        job = session.query(rfpJob).filter_by(slug="DAILY_CONFIG").first()
        # only work on most recent job
        if job != None:
            prompt = job.prompt
            reportNum = job.reportNum
            rfpStart = job.rfpStart
            rfpEnd = job.rfpEnd
            useGPT4 = job.useGPT4
            return prompt, reportNum, rfpStart, \
                rfpEnd, useGPT4

def createDailyJob(promptIn, reportNum, rfpStart, rfpEnd, useGPT4):
    print("Creating daily job")
    # create jobDatabase
    # get data from form
    now = datetime.datetime.now(datetime.timezone.utc)
    rfpJobID = f"DAILY_RUN_{now}"
    state = "Running!!!"
    prompt = promptIn
    # create jobDatabase
    data = rfpJob(slug=rfpJobID, state=state, prompt=prompt,
                  reportNum=reportNum, rfpStart=rfpStart,
                  rfpEnd=rfpEnd, useGPT4=useGPT4)
    with Session.begin() as session:
        session.add(data)
        session.commit()
    return rfpJobID

def sendMail(send_from, send_to, subject, text, files=None,
              server="smtp.gmail.com"):
    assert isinstance(send_to, list)
    print("Sending email!!!")
    msg = MIMEMultipart()
    msg['From'] = send_from
    msg['To'] = COMMASPACE.join(send_to)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject

    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=basename(f)
            )
        # After the file is closed
        part['Content-Disposition'] = 'attachment; filename="%s"' % basename(f)
        msg.attach(part)


    smtp = smtplib.SMTP(host=server, port=587)
    smtp.starttls()
    smtp.login(user, pwd)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()

fromEmail = "brycepm2@gmail.com"
toEmail = ["brycepm2@illinois.edu"]
today = datetime.date.today()
d1 = today.strftime("%m/%d/%Y")
emailSubject = f"RFP Daily Report - {d1}"
user = "brycepm2@gmail.com"
pwd = os.getenv("EMAIL_APP_PWD")

def runDailyJob(slug, prompt, reportNum, rfpStart, rfpEnd, useGPT4):
    # start clock
    sTime = time.time()
    # scrape desired rfp text
    rfpText, rfpStart, rfpEnd = rfpReaderBackend.getRFPReport(reportNum, rfpStart, rfpEnd)
    emailText = ""
    outPdfFullPath = '/home/brycepm2/ZAMAutoWebsite/DailyReports/RFPReport_'+slug[0:20]
    if rfpText != False:
        if (useGPT4 == True):
            model = 'gpt-4-1106-preview'
        else:
            model = 'gpt-3.5-turbo-1106'
        print("Probing RFPs", flush=True)
        print("using: ", model)
        totalCost = rfpReaderBackend.probeRFPs(rfpText, prompt, model, outPdfFullPath)
        eTime = time.time()
        result = eTime - sTime
        state = "Done!!!"
        print(f"done after {result} seconds!", flush=True)
        print(f"totalCost =  {totalCost}", flush=True)
        emailText = "Daily rfp report for TGRWA"
        files = [outPdfFullPath + ".pdf"]
    else:
        # there are no RFPs in this report
        print("There are no RFPs in this report!!!")
        result = -1
        state = "No RFPs in Report!!!"
        emailText = "There are no RFPs in today report."
        files = None
    sendMail(fromEmail, toEmail, emailSubject, emailText, files)
    updateJob(slug, rfpStart, rfpEnd, state, totalCost, result)
    return 0

def updateJob(slug, rfpStart, rfpEnd, state, totalCost, result):
    with Session.begin() as session:
        data = session.query(rfpJob).filter_by(slug=slug).all()
        # only work on most recent job
        job = data[-1]
        job.rfpStart = rfpStart
        job.rfpEnd = rfpEnd
        job.state = "Done!!!"
        job.totalCost = totalCost
        job.result = result

if __name__ == "__main__":
    prompt, reportNum, rfpStart, rfpEnd, useGPT4 = getDailyJobData()
    print(reportNum)
    slug = createDailyJob(prompt, reportNum, rfpStart, rfpEnd, useGPT4)
    print(slug)
    iErr = runDailyJob(slug, prompt, reportNum, rfpStart, rfpEnd, useGPT4)
    # TODO: add email
