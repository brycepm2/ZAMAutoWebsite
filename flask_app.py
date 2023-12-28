
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import datetime
import rfpReaderBackend
import sys
import os
from time import sleep

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

@app.route('/')
def home():
    ip = request.headers.get("X-Real-Ip", "")
    now = datetime.datetime.now(datetime.timezone.utc)
    jobID = f"{ip}{now}"
    data = Job(slug=jobID)
    db.session.add(data)
    db.session.commit()
    try :
        os.remove("./ZAMAutoWebsite/assets/pdfOut/RFPSummary.pdf")
    except OSError as e:
        print("PDF already gone!!!")
    return render_template('index.html', job_id = jobID)

@app.route("/stashRFPData", methods=["GET", "POST"])
def stashRFPData():
    # make jobID
    try:
        # get data from form
        rfpJobID = request.form["id"]
        prompt = request.form["promptIn"]
        reportNum = request.form["reportNumIn"]
        rfpStart = request.form["rfpStartIn"]
        rfpEnd = request.form["rfpEndIn"]
        useGPT4 = True if request.form["useGPT4"] == 'true' else False
        if rfpStart > rfpEnd and rfpEnd - rfpStart > maxNumRFPs:
            print("rfpRange is off, will correct in backend!!!")
        # create jobDatabase
        data = rfpJob(slug=rfpJobID, prompt=prompt,
                      reportNum=reportNum, rfpStart=rfpStart,
                      rfpEnd=rfpEnd, useGPT4=useGPT4)
        db.session.add(data)
        db.session.commit()
    except Exception as e:
        return jsonify(result=str(e))
    try :
        os.remove("./ZAMAutoWebsite/assets/pdfOut/RFPSummary.pdf")
    except OSError as e:
        print("PDF already gone!!!")
    return jsonify(
        {
        'status': "Saved"
        }
    )



@app.route("/query", methods=["POST"])
def query():
    job_id = request.form["id"]
    rfpStatus = request.form["rfpStatus"]
    if rfpStatus == "Saved":
        jobs = rfpJob.query.filter_by(slug=job_id).all()
        # if there are no running jobs, use last 
        data = jobs[-1]
        for iJob in jobs:
            if iJob.state != 'Done!!!':
                # if this job is not done, use that
                data = iJob
                break
            else:
                # if this job is done go to the next one
                continue
        out = jsonify(
            {
                "state": data.state,
                "result": data.result,
            }
        )
    else:
        out = jsonify(
            {
                "state": "",
                "result": 0,
            }
        )
    return out
        
 
class rfpJob(db.Model):
    __tablename__ = "rfpRun"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), nullable=False)
    state = db.Column(db.String(64), nullable=False, default="Queued")
    prompt = db.Column(db.Text, nullable=False)
    reportNum = db.Column(db.Integer, default=1)
    rfpStart = db.Column(db.Integer, default=1)
    rfpEnd = db.Column(db.Integer, default=1)
    useGPT4 = db.Column(db.Boolean, default=False)
    totalCost = db.Column(db.Float, default=0.0)
    result = db.Column(db.Integer, default=0)

class Job(db.Model):
    __tablename__ = "jobs"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(64), nullable=False)
    state = db.Column(db.String(64), nullable=False, default="queued")
    result = db.Column(db.Integer, default=0)
