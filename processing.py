import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_ENGINE_OPTIONS
from flask_app import rfpJob

import rfpReaderBackend


engine = create_engine(
    SQLALCHEMY_DATABASE_URI, **SQLALCHEMY_ENGINE_OPTIONS
)
Session = sessionmaker(engine)


def find_pending_job():
    with Session.begin() as session:
        queue = session.query(rfpJob).filter_by(state="Queued")
        if job := queue.first():
            print("Found Job!!!")
            job.state = "Running!!!"
            return job.slug


def getJobData(slug):
    print(f"Processing job: {slug}...", end=" ", flush=True)
    with Session.begin() as session:
        data = session.query(rfpJob).filter_by(slug=slug).all()
        # only work on most recent job
        job = data[-1]
        if job != None:
            prompt = job.prompt
            reportNum = job.reportNum
            rfpStart = job.rfpStart
            rfpEnd = job.rfpEnd
            useGPT4 = job.useGPT4
            return prompt, reportNum, rfpStart, \
                rfpEnd, useGPT4

def runJob(slug, prompt, reportNum, rfpStart, rfpEnd, useGPT4):
    # start clock
    sTime = time.time()
    # scrape desired rfp text
    rfpText = rfpReaderBackend.getRFPReport(reportNum, rfpStart, rfpEnd)
    if rfpText != False:
        if (useGPT4 == True):
            model = 'gpt-4-1106-preview'
        else:
            model = 'gpt-3.5-turbo-1106'
        print("Probing RFPs", flush=True)
        print("using: ", model)
        totalCost = rfpReaderBackend.probeRFPs(rfpText, prompt, model)
        eTime = time.time()
        result = eTime - sTime
        state = "Done!!!"
        print(f"done after {result} seconds!", flush=True)
        print(f"totalCost =  {totalCost}", flush=True)
    else:
        # there are no RFPs in this report
        print("There are no RFPs in this report!!!")
        result = -1
        state = "No RFPs in Report!!!"
    updateJob(slug, state, totalCost, result)
    return 0

def updateJob(slug, state, totalCost, result):
    with Session.begin() as session:
        data = session.query(rfpJob).filter_by(slug=slug).all()
        # only work on most recent job
        job = data[-1]
        job.state = "Done!!!"
        job.totalCost = totalCost
        job.result = result

if __name__ == "__main__":
    while True:
        if slug := find_pending_job():
            prompt, reportNum, rfpStart, \
                rfpEnd, useGPT4 = getJobData(slug)
            iErr = runJob(slug, prompt, reportNum, rfpStart,
                          rfpEnd, useGPT4)
        else:
            time.sleep(1)
