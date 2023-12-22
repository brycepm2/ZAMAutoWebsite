
# A very simple Flask Hello World app for you to get started with...

from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import datetime
import rfpReaderBackend
import sys
import os

app = Flask(__name__)
# app.config.from_object('config')
# db = SQLAlchemy(app)

@app.route('/')
def home():
    # ip = request.headers.get("X-Real-Ip", "")
    # now = datetime.datetime.now(datetime.timezone.utc)
    # jobID = f"{ip}{now}"
    # data = Job(slug=jobID)
    # db.session.add(data)
    # db.session.commit()
    try :
        os.remove("./ZAMAutoWebsite/assets/pdfOut/RFPSummary.pdf")
    except OSError as e:
        print("PDF already gone!!!")
    return render_template('index.html') #, job_id = jobID)

@app.route('/callPython', methods=["GET","POST"])
def callPython():
    # print to log file instead of stdout
    old_stdout = sys.stdout
    logFile = open("./ZAMAutoWebsite/RFPRun.log", 'w')
    sys.stdout = logFile
    maxNumRFPs = 30
    try:
        email = request.args.get('email', 'empty', type=str)
        prompt = request.args.get('prompt', 'empty', type=str)
        reportNum= request.args.get('reportNum', 1, type=int)
        rfpStart = request.args.get('rfpStart', 1, type=int)
        rfpEnd = request.args.get('rfpEnd', 40, type=int)
        if rfpStart > rfpEnd and rfpEnd - rfpStart > maxNumRFPs:
            print("rfpRange is off, will correct in backend!!!")
        useGPT4 = True if request.args.get('useGPT4', type=str) == 'true' else False
        rfpText = rfpReaderBackend.getRFPReport(reportNum, rfpStart, rfpEnd)
        if rfpText != False:
            if (useGPT4 == True):
                model = 'gpt-4-1106-preview'
            else:
                model = 'gpt-3.5-turbo-1106'
            print("Probing RFPs")
            print("using: ", model)
            rfpReaderBackend.probeRFPs(rfpText, prompt, model)
            sys.stdout = old_stdout
            logFile.close()
            print("Done")
            return jsonify(emailOut=email, promptOut=prompt)
        else:
            return jsonify(emailOut=email, promptOut="No opportunities in this report!!!")
    except Exception as e:
        sys.stdout = old_stdout
        logFile.close()
        return jsonify(result=str(e))

# @app.route("/query", methods=["POST"])
# def query():
#     job_id = request.form["id"]
#     data = Job.query.filter_by(slug=job_id).first()
#     return jsonify(
#         {
#             "state": data.state,
#             "result": data.result,
#         }
#     )


# class Job(db.Model):
#     __tablename__ = "jobs"
#     id = db.Column(db.Integer, primary_key=True)
#     slug = db.Column(db.String(64), nullable=False)
#     state = db.Column(db.String(10), nullable=False, default="queued")
#     result = db.Column(db.Integer, default=0)

